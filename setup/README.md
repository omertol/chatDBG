# 📚 chatDBG – Setup Guide

This repository contains setup instructions for building the **chatDBG** pipeline, based on David Ben-Gurion's writings. The system enables interaction with an AI embodiment of Israel's first prime minister.

---

## ⚠️ Prerequisites

* An **OpenAI API key** is required for embeddings, fine-tuning, and generation.

---

## 📁 Data Structure

| Column Name        | Description                            | Type  |
| ------------------ | -------------------------------------- | ----- |
| `book_id`          | Unique identifier                      | `int` |
| `type`             | Type of document (e.g., speech, diary) | `str` |
| `unit`             | Source collection                      | `str` |
| `headline`         | Title or description                   | `str` |
| `additional_info1` | First content chunk                    | `str` |
| `additional_info2` | Second content chunk                   | `str` |

---

## 🧑‍💻 Environment Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate     # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

Includes: `transformers`, `faiss-gpu`, `langchain`, `streamlit`, and more.

---

## 🔧 Pipeline Steps

1. **Preprocess data**: `data_prep.ipynb`
2. **Generate embeddings**: `embeddings.ipynb`
3. **Create FAISS index**: `RAG_setup.ipynb`

To enrich the database, run JSON_wiki_extraction.ipynb to extract relevant Wikipedia content. 

You can create a list of page names within the notebook, then loop over the list using the function save_wikipedia_page_data('page_name').


---

## 🧪 Style Transfer (Optional)

1. Generate parallel text: `text_generation.ipynb`
2. Fine-tune model: `fine_tune.ipynb`

The `fine_tune.ipynb` notebook includes an input validation step based on [OpenAI's Fine-Tuning Guide](https://platform.openai.com/docs/guides/fine-tuning).

---

## 📝 Notes

* Ensure all required libraries are installed before running notebooks.
