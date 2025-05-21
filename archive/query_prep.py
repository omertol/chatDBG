import os
import torch
from transformers import AutoTokenizer, AutoModel
import spacy
import fasttext
from DictaBERTEmbeddings import DictaBERTEmbeddings

# Constants
DATA_PATH = './data/'
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Global variables
tokenizer_hebrew = None
model_hebrew = None
nlp_english = None
lang_detector = None
hebrew_stopwords = []

def initialize_preprocessing():
    global tokenizer_hebrew, model_hebrew, nlp_english, lang_detector, hebrew_stopwords
    
    print(f'Initializing preprocessing models on device: {DEVICE}')
    
    # Load DictaBERT-lex model for Hebrew
    tokenizer_hebrew = AutoTokenizer.from_pretrained('dicta-il/dictabert-lex')
    model_hebrew = AutoModel.from_pretrained('dicta-il/dictabert-lex', trust_remote_code=True)
    model_hebrew = model_hebrew.to(DEVICE)
    model_hebrew.eval()
    print("done")
    # Load spaCy model for English
    nlp_english = spacy.load('en_core_web_sm')
    
    # Load the pretrained language detection model
    model_path = os.path.join(DATA_PATH, 'lid.176.bin')
    lang_detector = fasttext.load_model(model_path)
    
    # Load Hebrew stopwords from file
    stopwords_file = os.path.join(DATA_PATH, 'stopwords.txt')
    with open(stopwords_file, 'r', encoding='utf-8') as file:
        hebrew_stopwords = file.read().splitlines()

# Stopwords removal for Hebrew
def remove_hebrew_stopwords(text):
    words = text.split()
    filtered_words = [word for word in words if word not in hebrew_stopwords]
    return ' '.join(filtered_words)

# Language detection
def detect_lang(text):
    if not isinstance(text, str) or text.strip() == "":
        return "unknown"  
   
    label = lang_detector.predict(text)[0][0]  
    return label.replace("__label__", "")

def preprocess_query(query):
    lang = detect_lang(query)

    if lang == 'he':
        query = remove_hebrew_stopwords(query)
        lemmatized = model_hebrew.predict([query], tokenizer_hebrew)
        query_processed = " ".join([lemma[1] if lemma[1] != "[BLANK]" else lemma[0] for lemma in lemmatized[0]])

    elif lang == 'en':
        query = query.lower()
        doc = nlp_english(query)
        query_processed = " ".join([token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct])

    else:
        query_processed = query


    return query_processed

if __name__ == "__main__":
    initialize_preprocessing()
