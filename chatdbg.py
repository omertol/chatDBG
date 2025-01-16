import os
import pickle
import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM, BertConfig, BertLMHeadModel, Trainer, TrainingArguments, \
    EarlyStoppingCallback
from peft import get_peft_model, LoraConfig, TaskType
from sklearn.model_selection import train_test_split
import optuna

# Constants
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
DATA_PATH = './data'
ENCODINGS_PATH = './pickles/'

# Logger setup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Dataset Class
class ArcDataset(torch.utils.data.Dataset):
    def __init__(self, encodings):
        self.encodings = encodings

    def __len__(self):
        return len(self.encodings)

    def __getitem__(self, idx):
        return {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}


# Function to load data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path)
        new_column_names = ['book_id', 'type', 'unit', 'headline', 'from_date', 'to_date', 'additional_info',
                            'additional_info_2']
        if len(new_column_names) == len(df.columns):
            df.columns = new_column_names
        else:
            logger.error("Error: The number of new column names does not match the number of columns in the DataFrame.")
        return df
    except FileNotFoundError:
        logger.error("Error: File not found. Please check the file path.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


# Function to preprocess data
def preprocess_data(original_df):
    df = original_df.copy(deep=True)
    df.fillna('', inplace=True)  # Replace None values with empty strings
    df['combined_info'] = df['additional_info'] + df['additional_info_2']
    df['combined'] = df.apply(lambda row: f"Headline: {row['headline']}. Text: {row['combined_info']}" if row[
        'combined_info'] else f"Headline: {row['headline']}", axis=1)
    df.to_pickle(os.path.join(ENCODINGS_PATH, 'first_data_batch.pkl'))
    return df


# Function to configure LoRA
def config_lora(model, r, alpha, dropout, task_type):
    lora_config = LoraConfig(r=r, lora_alpha=alpha, lora_dropout=dropout, task_type=task_type)
    return get_peft_model(model, lora_config)


# Function to tokenize data
def tokenize_data(examples, tokenizer):
    encodings = tokenizer(examples, padding="max_length", truncation=True, max_length=256)
    labels = encodings['input_ids'].copy()
    for i in range(len(labels)):
        labels[i] = labels[i][1:] + [tokenizer.pad_token_id]  # Shift and pad
    encodings['labels'] = labels
    return encodings


# Define the objective function for Optuna
def objective(trial, train_dataset, val_dataset, tokenizer):
    # Suggest values for hyperparameters using Optuna
    learning_rate = trial.suggest_loguniform('learning_rate', 1e-6, 1e-4)
    batch_size = trial.suggest_categorical('batch_size', [2048])
    num_train_epochs = trial.suggest_categorical('num_train_epochs', [5000])
    r = trial.suggest_categorical('lora_r', [4])
    alpha = trial.suggest_categorical('lora_alpha', [128])
    dropout = trial.suggest_categorical('lora_dropout', [0.1, 0.2, 0.3, 0.5])
    gradient_clipping = trial.suggest_categorical('gradient_clipping', [1.0])
    warmup_steps = trial.suggest_categorical('warmup_steps', [0, 500, 1000, 5000])
    weight_decay = trial.suggest_categorical('weight_decay', [0, 0.01, 0.1, 0.2])

    # Configure LoRA
    model_name = "dicta-il/dictabert"
    config = BertConfig.from_pretrained(model_name)
    config.is_decoder = True
    model = BertLMHeadModel.from_pretrained(model_name, config=config).to(DEVICE)
    lora_model = config_lora(model, r=r, alpha=alpha, dropout=dropout, task_type=TaskType.CAUSAL_LM)

    # Set up the training arguments with early stopping
    training_args = TrainingArguments(
        output_dir=f"./results_{r}_{alpha}_{dropout}_{batch_size}_{learning_rate}",
        num_train_epochs=int(num_train_epochs),
        per_device_train_batch_size=int(batch_size),
        logging_dir="./logs",
        eval_strategy="steps",
        save_steps=500,
        save_total_limit=1,  # Save only the last checkpoint
        remove_unused_columns=False,
        load_best_model_at_end=True,  # Enable saving the best model
        metric_for_best_model="eval_loss",  # Track validation loss to find the best model
        greater_is_better=False,  # Lower validation loss is better
        learning_rate=learning_rate,
        gradient_accumulation_steps=1,
        max_grad_norm=float(gradient_clipping),
        weight_decay=float(weight_decay),
        warmup_steps=int(warmup_steps),
    )

    # Early stopping callback
    early_stopping_callback = EarlyStoppingCallback(
        early_stopping_patience=2)  # Stop if no improvement after 2 eval steps

    # Initialize the Trainer
    trainer = Trainer(
        model=lora_model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        callbacks=[early_stopping_callback],
    )

    # Start fine-tuning
    trainer.train()

    # Get validation loss from the best model
    eval_results = trainer.evaluate()
    val_loss = eval_results["eval_loss"]

    # Return the validation loss for optimization
    return val_loss


# Function to optimize hyperparameters using Optuna
def optimize_hyperparameters(train_dataset, val_dataset, tokenizer, n_trials=100):
    # Create an Optuna study to optimize the objective
    study = optuna.create_study(direction='minimize')  # Minimize validation loss
    study.optimize(lambda trial: objective(trial, train_dataset, val_dataset, tokenizer), n_trials=n_trials)

    # Get the best hyperparameters
    best_params = study.best_params
    logger.info(f"Best hyperparameters: {best_params}")
    logger.info(f"Best validation loss: {study.best_value}")

    # Load the best model from the saved checkpoint
    best_model_path = f"./results_{best_params['lora_r']}_{best_params['lora_alpha']}_{best_params['lora_dropout']}_{best_params['batch_size']}_{best_params['learning_rate']}/"
    best_model = BertLMHeadModel.from_pretrained(best_model_path).to(DEVICE)

    return best_model, best_params

# def grid_search(train_dataset, val_dataset, tokenizer):
#     # Define hyperparameter grid
#     param_grid = {
#         'learning_rate': [1e-6, 1e-5, 3e-5, 5e-5, 1e-4, 3e-4],
#         'batch_size': [4, 8, 16, 32, 64, 128],
#         'num_train_epochs': [2, 5, 10, 20, 50],
#         'lora_r': [4, 8, 16, 32, 64],
#         'lora_alpha': [8, 16, 32, 64, 128],
#         'lora_dropout': [0.1, 0.2, 0.3, 0.5],
#         'gradient_clipping': [1.0, 5.0, 10.0],
#         'warmup_steps': [0, 500, 1000, 5000],
#         'weight_decay': [0, 0.01, 0.1, 0.2],
#     }
#
#     best_model = None
#     best_val_loss = float('inf')
#     best_params = {}
#
#     # Generate all combinations of hyperparameters
#     for learning_rate, batch_size, num_train_epochs, r, alpha, dropout, gradient_clipping, warmup_steps, weight_decay in product(*param_grid.values()):
#         logger.info(f"Starting training with r={r}, alpha={alpha}, dropout={dropout}, batch_size={batch_size}, learning_rate={learning_rate}, num_train_epochs={num_train_epochs}, gradient_clipping={gradient_clipping}, warmup_steps={warmup_steps}, weight_decay={weight_decay}")
#
#         # Configure LoRA
#         model_name = "dicta-il/dictabert"
#         config = BertConfig.from_pretrained(model_name)
#         config.is_decoder = True
#         model = BertLMHeadModel.from_pretrained(model_name, config=config).to(DEVICE)
#         lora_model = config_lora(model, r=r, alpha=alpha, dropout=dropout, task_type=TaskType.CAUSAL_LM)
#
#         # Set up the training arguments with early stopping
#         training_args = TrainingArguments(
#             output_dir=f"./results_{r}_{alpha}_{dropout}_{batch_size}_{learning_rate}",
#             num_train_epochs=int(num_train_epochs),  # Ensure it's an integer
#             per_device_train_batch_size=int(batch_size),  # Ensure it's an integer
#             logging_dir="./logs",
#             evaluation_strategy="steps",
#             save_steps=500,
#             save_total_limit=1,  # Save only the last checkpoint
#             remove_unused_columns=False,
#             load_best_model_at_end=True,  # Enable saving the best model
#             metric_for_best_model="eval_loss",  # Track validation loss to find the best model
#             greater_is_better=False,  # Lower validation loss is better
#             learning_rate=learning_rate,
#             gradient_accumulation_steps=1,  # Adjust if necessary
#             max_grad_norm=float(gradient_clipping),  # Ensure it's a float
#             weight_decay=float(weight_decay),  # Ensure it's a float
#             warmup_steps=int(warmup_steps),  # Ensure it's an integer
#         )
#
#         # Early stopping callback
#         early_stopping_callback = EarlyStoppingCallback(early_stopping_patience=2)  # Stop if no improvement after 2 eval steps
#
#         # Initialize the Trainer with early stopping
#         trainer = Trainer(
#             model=lora_model,
#             args=training_args,
#             train_dataset=train_dataset,
#             eval_dataset=val_dataset,
#             callbacks=[early_stopping_callback],
#         )
#
#         # Start fine-tuning
#         trainer.train()
#
#         # Get validation loss from the best model
#         eval_results = trainer.evaluate()
#         val_loss = eval_results["eval_loss"]
#
#         # Save the model if it's the best one based on validation loss
#         if val_loss < best_val_loss:
#             best_val_loss = val_loss
#             best_model = lora_model
#             best_params = {
#                 "r": r,
#                 "alpha": alpha,
#                 "dropout": dropout,
#                 "batch_size": batch_size,
#                 "learning_rate": learning_rate,
#                 "num_train_epochs": num_train_epochs,
#                 "gradient_clipping": gradient_clipping,
#                 "warmup_steps": warmup_steps,
#                 "weight_decay": weight_decay,
#             }
#             # Save the best model
#             best_model.save_pretrained(f"./best_model_{r}_{alpha}_{dropout}_{batch_size}_{learning_rate}")
#             logger.info(f"Best model updated with val_loss={val_loss}")
#
#     return best_model, best_params

# Main script logic
def main():
    logger.info(f"Using device: {DEVICE}")
    tokenizer = AutoTokenizer.from_pretrained('dicta-il/dictabert')

    # Load or generate encodings
    try:
        with open(os.path.join(ENCODINGS_PATH, 'train_encodings.pkl'), 'rb') as f:
            train_encodings = pickle.load(f)
        with open(os.path.join(ENCODINGS_PATH, 'val_encodings.pkl'), 'rb') as f:
            val_encodings = pickle.load(f)
    except FileNotFoundError:
        # Load and process data
        try:
            with open(os.path.join(ENCODINGS_PATH, 'first_data_batch.pkl'), 'rb') as f:
                processed_df = pickle.load(f)
        except FileNotFoundError:
            df = load_data(os.path.join(DATA_PATH, 'bg_arc_output.xlsx'))
            processed_df = preprocess_data(df)

        # Split the dataset
        train_data, temp_data = train_test_split(processed_df, test_size=0.3, random_state=42)
        val_data, test_data = train_test_split(temp_data, test_size=0.66, random_state=42)

        # Tokenize and save the encodings
        train_encodings = tokenize_data(train_data["combined"].to_list(), tokenizer)
        val_encodings = tokenize_data(val_data["combined"].to_list(), tokenizer)

        with open(os.path.join(ENCODINGS_PATH, 'train_encodings.pkl'), 'wb') as f:
            pickle.dump(train_encodings, f)
        with open(os.path.join(ENCODINGS_PATH, 'val_encodings.pkl'), 'wb') as f:
            pickle.dump(val_encodings, f)

    # Prepare datasets
    train_dataset = ArcDataset(train_encodings)
    val_dataset = ArcDataset(val_encodings)

    # Perform optimization to find the best model and hyperparameters
    best_model, best_params = optimize_hyperparameters(train_dataset, val_dataset, tokenizer)

    # After optimization, save the best model's weights
    torch.save(best_model.state_dict(), os.path.join(DATA_PATH, "best_model_final.pth"))
    logger.info(f"Best model parameters: {best_params}")


if __name__ == '__main__':
    main()
