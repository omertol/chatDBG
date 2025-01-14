import pickle
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import get_peft_model, LoraConfig, TaskType
from transformers import Trainer, TrainingArguments

os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

class arcDataset(torch.utils.data.Dataset):
    def __init__(self, encodings):
        self.encodings = encodings

    def __len__(self):
        return len(self.encodings)

    def __getitem__(self, idx):
        return {key: torch.tensor(val[idx]).to(device) for key, val in self.encodings.items()}  # Move data to GPU


def config_lora(model, r, alpha, dropout, task_type):
    # Apply LoRA (optional) if you want to use it for fine-tuning
    lora_config = LoraConfig(
        r=r,
        lora_alpha=alpha,
        lora_dropout=dropout,
        task_type=task_type
    )
    lora_model = get_peft_model(model, lora_config)

    return lora_model


def tokenize_function(examples, tokenizer):
    return tokenizer(examples, padding="max_length", truncation=True, max_length=256)


def trainer(output_dir, train_epochs, batch_size, log_dir, eval, steps):
    # Define training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=train_epochs,
        per_device_train_batch_size=batch_size,
        logging_dir=log_dir,
        evaluation_strategy=eval,
        save_steps=steps,
    )

    # Create the Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset
    )

    return trainer

if __name__ == '__main__':
    # # Check if GPU is available
    # device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    # print(f"Using device: {device}")
    #
    # torch.cuda.empty_cache()
    #
    # # Path to the directory where your .pkl files are stored in Kaggle
    # dataset_path = './pickles/'
    #
    # # Load the pickle files into separate variables
    # with open(os.path.join(dataset_path, 'train_encodings.pkl'), 'rb') as f:
    #     train_encodings = pickle.load(f)
    #
    # with open(os.path.join(dataset_path, 'val_encodings.pkl'), 'rb') as f:
    #     val_encodings = pickle.load(f)
    #
    # with open(os.path.join(dataset_path, 'test_encodings.pkl'), 'rb') as f:
    #     test_encodings = pickle.load(f)
    #
    # train_dataset = arcDataset(train_encodings)
    # val_dataset = arcDataset(val_encodings)
    #
    # # Load DictaLM model and tokenizer
    # model_name = "dicta-il/dictalm2.0"
    # model = AutoModelForCausalLM.from_pretrained(model_name).to(device)  # Move model to GPU
    #
    # lora_model = config_lora(model, 8, 16, 0.1, TaskType.CAUSAL_LM)
    #
    # trainer_instance = trainer("./results", 3, 1, "./logs", "steps", 500)
    #
    # # Start fine-tuning
    # trainer_instance.train()
    # torch.save(lora_model.state_dict(), os.path.join(dataset_path, "lora_model.pth"))

    tokenizer = AutoTokenizer.from_pretrained("dicta-il/dictabert")
    model = AutoModelForCausalLM.from_pretrained("dicta-il/dictalm2.0")

    assert tokenizer.vocab_size == model.config.vocab_size, "Tokenizer and model vocab sizes are incompatible!"


