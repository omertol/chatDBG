import torch
from transformers import AutoTokenizer, AutoModel
from langchain.embeddings.base import Embeddings

class DictaBERTEmbeddings(Embeddings):
    def __init__(self, model_name="dicta-il/dictabert", device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)

    def embed_documents(self, texts):
        """Embed a list of documents."""
        return [self._embed_text(text) for text in texts]

    def embed_query(self, text):
        """Embed a single query."""
        return self._embed_text(text)

    def _embed_text(self, text):
        """Tokenize and compute the embeddings for a single text."""
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512, padding="max_length"
        ).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
        # Take the mean of the hidden states as the sentence embedding
        embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
        return embeddings