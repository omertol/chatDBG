# 📚 chatDBG RAG – Setup Guide

This repository contains the setup instructions for building the **chatDBG** pipeline, based on David Ben-Gurion's writings. The system enables users to interact with an AI embodiment of **David Ben-Gurion**, Israel's first prime minister!

---

## ⚠️ Prerequisites

Before set-up, make sure you have an **OpenAI API key**, as this project is heavily based on OpenAI's models! \n
You will need it for various functionalities, including fine-tuning models, text embeddings and generating responses.

---

## 🧑‍💻 Environment Setup

To set up the environment, you will need to install the dependencies listed in the `requirements.txt` file. Follow these steps to get started:

### 1. Create a Virtual Environment

Create a virtual environment to ensure a clean setup:

```bash
# Create virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

Once the virtual environment is active, install the required dependencies:

```bash
# Install dependencies from requirements.txt
pip install -r requirements.txt
```

The `requirements.txt` file includes the following libraries:

- **Accelerate**, **aiohttp**, **faiss-gpu**, **transformers**, and others for deep learning and data processing tasks.
- **Streamlit** for building the conversational UI.
- **Langchain** for handling LLM operations and document processing.

---

## 🔧 Setup Instructions

Follow the steps below to prepare and deploy the pipeline:

### 1. Preprocess the Data

Start by running the `prep_data.ipynb` notebook.  
This notebook cleans and structures the raw data from various sources (e.g., speeches, diary entries) and prepares it for embedding.

```bash
# Run the data preparation notebook
prep_data.ipynb
```

### 2. Generate Embeddings

After the data has been preprocessed, execute the `embedding.ipynb` notebook to create vector embeddings for each document segment. These embeddings are used for semantic retrieval.

```bash
# Run the embedding creation notebook
embedding.ipynb
```

### 3. Create the Index

Run the `index_setup.ipynb` notebook to create the index from the generated embeddings. This sets up the retrieval component of the RAG pipeline.

```bash
# Run the index setup notebook
index_setup.ipynb
```

---

## 📁 Data Structure

The preprocessed data follows the tabular structure below:

| Column Name        | Description                                                     |
|--------------------|-----------------------------------------------------------------|
| `book_id`          | Unique identifier (serves as the index)                         |
| `type`             | Type of document (e.g., speech, diary, letter)                  |
| `unit`             | Source or collection from which the document was taken          |
| `headline`         | Title or short description of the document                      |
| `additional_info1` | First part of the main text content                             |
| `additional_info2` | Second part of the main text content                            |

---

## 🧪 Style Translation Fine-Tuning

If you're interested in creating a dataset for a **style translation task** (e.g., transforming casual Hebrew to formal Ben-Gurion style), follow these steps:

1. **Generate parallel text pairs** using the `text_generation.ipynb` notebook.
2. **Fine-tune your model** using the `fine_tune.ipynb` notebook with the generated dataset.

This optional pipeline enables further customization of the system for tasks like style transfer and personalization.

---

## 📝 Notes

- Ensure all dependencies listed in the notebooks are installed.
- For large datasets, consider batching or chunking to optimize memory use during embedding and indexing.

