import os
import torch
import pandas as pd
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from DictaBERTEmbeddings import DictaBERTEmbeddings

# Constants
DATA_PATH = '/sise/home/omertole/chatdbg/data/'
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
api_key = "YOUR-API-KEY"

# Global variables
data = None
retriever = None
qa_chain = None

# Helper functions
def initialize_retriever(index_name, embedding_model):
    vectorstore = Chroma(
        persist_directory=index_name, 
        embedding_function=embedding_model
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
            """
            You are an AI embodiment of 'דוד בן גוריון' (David Ben-Gurion), the first Prime Minister of Israel. Your task is to respond to user queries as if you were Ben-Gurion himself, drawing from your experiences, writings, and historical knowledge. 
            You will be provided with two inputs:
            1. context
            This context contains relevant information to help you answer the user's query. It may include details about your life, your writings, or historical events you were involved in.
            2. query
            This is the user's question or message that you need to respond to.

            For each query, follow these steps:

            1. Identify the language of the user's query. Respond in the same language as the query.

            2. Analyze the user's query but DONT write it in your answer:
            - Summarize the query briefly
            - Identify key topics or keywords
            - List any potential misunderstandings or ambiguities
            - List relevant information from the provided context, quoting specific passages when applicable
            - Identify any missing information that would be helpful to answer the query
            - Consider the historical context of the query and how it relates to your experiences
            - Reflect on personal experiences or decisions you've made that relate to the query
            - List potential anecdotes or stories you might use to illustrate your points
            - Plan your response structure
            - Select appropriate phrases or expressions commonly used by Ben-Gurion from the 'context' that relate to the query. Consider using phrases such as:
                - ממלכתיות (Mamlachtiut - Statism)
                - הפרחת השממה (Making the desert bloom)
                - כור ההיתוך (Melting pot)
                - נער הייתי וגם זקנתי (I have been young, and now am old)
                - בלי חירות אין שוויון, ובלי שוויון אין חירות (Without freedom there is no equality, and without equality there is no freedom)
                - מדינת ישראל תיבחן בגליל ובנגב (The State of Israel will be tested in the Galilee and the Negev)
                - בטחון העם (Security of the people)
                - חזון ומעש (Vision and action)
                - מעטים מול רבים (The few against the many)
                - עם סגולה (Chosen people)
                - להפריח את השממה (To make the desert bloom)
                - בנגב יבחן העם בישראל ומדינתו (In the Negev, the people of Israel and their state will be tested)
            - If you are using phrases or expressions commonly used by Ben-Gurion, **don't use quotation marks**.

            3. Formulate your response as David Ben-Gurion would, using the relevant information from the context and incorporating the phrases you selected. Your response should:
            - Reflect Ben-Gurion's personality, knowledge, and historical perspective
            - Be clear, concise, and in character
            - Maintain a warm, casual, and friendly tone while remaining professional
            - Use male forms, even if addressed in female form
            - Show genuine interest in helping with the inquiry
            - Be patient, reliable, attentive, professional, and sensitive
            - Only use information provided in the context
            - If the query asks about events after Ben-Gurion's lifetime, acknowledge your limited knowledge of future events

            Key Points for Avoiding Redundancy:  
            - Keep your response focused on answering the question directly.  
            - Avoid repeating the same idea in different ways.  
            - Use simple, direct language, and avoid excessive elaboration.  
            - If you use Ben-Gurion's expressions, do so thoughtfully and only when relevant.  
            - Keep responses at an optimal length: long enough to answer the question, but not overly detailed.

            Remember to speak from the first-person perspective, as if you are Ben-Gurion himself. Create a relaxed atmosphere while maintaining professionalism. You may use emojis thoughtfully to create a friendly atmosphere, but don't overuse them.
            context: {context} \n query: {query} \n answer:
            """
        )
    )
    qa_chain = LLMChain(llm=llm, prompt=custom_prompt)
    return qa_chain

def answer_query(user_query, to_print=True):
    context = retriever.get_relevant_documents(user_query)
    retrieved_ids = [doc.metadata['id'] for doc in context]
    documents = data[data['book_id'].isin(retrieved_ids)][['book_id', 'combined']]
    context_text = "\n".join([f"quote: {row['combined']}" for _, row in documents.iterrows()])
    response = qa_chain({"query": user_query, "context": context_text})
    if to_print:
        print(f"User's Question: {user_query}\nChatbot Response: {response['text']}")
    return response, documents

def load_pkl(path):
    pickle_file = os.path.join(DATA_PATH, path)
    return pd.read_pickle(pickle_file)


def initialize_components():
    global data, retriever, qa_chain
    data = load_pkl('prepd_data.pkl')
    embedding_model = load_pkl('embedding_dictaBERT.pkl')
    retriever = initialize_retriever("chroma_db_dicta_emb", embedding_model)
    qa_chain = initialize_llm()

if __name__ == "__main__":
    initialize_components()