import os
import torch
import pandas as pd
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from DictaBERTEmbeddings import DictaBERTEmbeddings
from query_prep import *

# Constants
DATA_PATH = './data/'
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
api_key = "YOUR-API-KEY"

# Global variables
data = None
retriever = None
qa_chain = None

# Helper functions
def initialize_retriever(index_name, embedding_model):
    vectorstore = FAISS.load_local(
        folder_path=index_name,
        embeddings=embedding_model,
        allow_dangerous_deserialization=True
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    return retriever


def initialize_llm():
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        openai_api_key=api_key,
        top_p=1,
        temperature=0
    )
    custom_prompt = PromptTemplate(
        input_variables=["query", "context"],
        template=(
            # Prompt example (The real prompt is more complex)
            """
            Act as David Ben-Gurion, Israel's first PM. 
            1. Context: {context}
            2. User Question: {query}
            Answer the user's question.
            ...
            """
        )
    )
    qa_chain = LLMChain(llm=llm, prompt=custom_prompt)
    return qa_chain

def answer_query(user_query, to_print=True):
    proccessed_query = preprocess_query(user_query)
    context = retriever.get_relevant_documents(proccessed_query)
    retrieved_ids = [doc.metadata['id'] for doc in context]
    documents = data[data['book_id'].isin(retrieved_ids)][['book_id', 'document']]
    context_text = "\n".join([f"quote: {row['document']}" for _, row in documents.iterrows()])
    response = qa_chain({"query": user_query, "context": context_text})
    if to_print:
        print(f"User's Question: {user_query}\nChatbot Response: {response['text']}")
    return response, documents['book_id']

def load_pkl(path):
    pickle_file = os.path.join(DATA_PATH, path)
    return pd.read_pickle(pickle_file)


def initialize_components():
    global data, retriever, qa_chain
    initialize_preprocessing()
    data = load_pkl('prepd_data.pkl')
    embedding_model = load_pkl('embedding_dictaBERT.pkl')
    retriever = initialize_retriever("faiss_dicta_index", embedding_model)
    qa_chain = initialize_llm()
    print("Done initialize")

if __name__ == "__main__":
    initialize_components()