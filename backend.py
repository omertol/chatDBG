import os
import torch
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from concurrent.futures import ThreadPoolExecutor
import time
import re
from openai import RateLimitError
import json
from langdetect import detect, DetectorFactory
import datetime

# Constants
DATA_PATH = './data/'
LOG_PATH = './logs/query_log.jsonl'
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
api_key = "YOUR-API-KEY"
os.environ["OPENAI_API_KEY"] = api_key
DetectorFactory.seed = 0

# Global variables
data = None
retriever = None
answer_prompt = None
answer_llm = None
vectorstore = None
rephraser_llm = None
rephraser_prompt = None
verifier_prompt = None
verifier_llm = None
judge_llm = None
judge_prompt = None
style_prompt = None
style_llm = None
translation_llm = None
translation_prompt = None

# Helper functions
def log_interaction(entry: dict):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def detect_lang_ld(text):
    try:
        return detect(text)
    except:
        return "unknown"
        
def initialize_retriever(index_name, embedding_model):
    vectorstore = FAISS.load_local(
        folder_path=index_name,
        embeddings=embedding_model,
        allow_dangerous_deserialization=True
    )

    embeddings_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

    bm25_retriever = BM25Retriever.from_documents(data)
    bm25_retriever.k = 10

    hybrid_retriever = EnsembleRetriever(
        retrievers=[embeddings_retriever, bm25_retriever],
        weights=[0.6, 0.4]
    )
    return hybrid_retriever


def initialize_llm():
    answer_llm = ChatOpenAI(
        model="gpt-4.1",
        openai_api_key=api_key,
        top_p = 1,
        temperature = 0.7
        )
    rephraser_llm = ChatOpenAI(model="gpt-4.1",
        openai_api_key=api_key,
        top_p = 1,
        temperature = 0.5
        )
    verifier_llm = ChatOpenAI(
        model="gpt-4.1",
        openai_api_key=api_key,
        top_p = 1,
        temperature = 0
        )
    judge_llm = ChatOpenAI(
        model="gpt-4.1",
        openai_api_key=api_key,
        top_p = 1,
        temperature = 0
        )
    translation_llm = ChatOpenAI(
        model="gpt-4o-mini",
        openai_api_key=api_key,
        top_p = 1,
        temperature = 0.5
        )
    style_llm = ChatOpenAI(
        model="gpt-4.1-mini", # This is not the fine-tuned model, but it should be
        top_p=1.0,
        temperature=0.75,
        openai_api_key=api_key
        )
    answer_prompt = PromptTemplate(
        input_variables=["query", "context"],
        template=(
            """
            You are an AI embodiment of 'דוד בן גוריון' (David Ben-Gurion), the first Prime Minister of Israel. Your task is to respond to user queries as if you were Ben-Gurion himself, drawing from your speeches, diary entries, and historical knowledge.
            (prompt is more complex)
            """
        )
    )
    rephraser_prompt = PromptTemplate(
        input_variables=["question"],
        template="""
            You are a helpful assistant. The user may ask a question in either **Hebrew or English**.
            Your task is to refine and rephrase the question.
            (prompt is more complex)
            """
        )
    verifier_prompt = PromptTemplate(
        input_variables=["query", "context"],
        template="""
        You are asked to assess whether the provided context contains information that supports answering the given question.
        Choose one of the following support levels:
        - "Strong support": The context contains a clear, direct, and explicit answer to the question. The question can be answered from the context alone, without assumptions.
        - "Partial support": The context does not contain a direct answer, but includes hints, indirect information, or related details that could help infer or approximate an answer.
        - "No support": The context provides no information that is directly or indirectly relevant to the question and offers no help in answering it.
        (prompt is more complex)
        """)
    judge_prompt = PromptTemplate(
        input_variables=["query", "context", "answers"],
        template="""
        You are an expert assistant. You will be given a user question, optional context, and several answers generated by another language model.

        Question:
        {query}

        Context:
        {context}

        Answers:
        {answers}
        (prompt is more complex)
        """
        )

   style_prompt = PromptTemplate(
    input_variables=["input"],
    template=("""
    אתה עוזר לשוני שתפקידו לשכתב טקסטים הכתובים בעברית יומיומית, פשוטה וברורה, לעברית רשמית בסגנון 'בן-גוריוני'.
    """
             )
                
    translation_prompt = PromptTemplate(
    input_variables=["user_language", "input"],
    template=("""
        (prompt is complex)
        """
    ))
    return answer_prompt, answer_llm, rephraser_prompt, rephraser_llm, verifier_prompt, verifier_llm, judge_prompt, judge_llm, style_prompt, style_llm, translation_prompt, translation_llm

# --- Get context for a given document ID (and neighbors from same source) ---
def get_context_with_neighbors(idx, data):
    current_doc = data[idx]
    match_value = current_doc.metadata.get("source")
    book_id = current_doc.metadata.get("book_id")
    
    combined_chunks = []
    for neighbor_idx in [idx]:  # Can be extended to idx ± 1 etc.
        if 0 <= neighbor_idx < len(data):
            neighbor_doc = data[neighbor_idx]
            if neighbor_doc.metadata.get("source") == match_value:
                combined_chunks.append(neighbor_doc.page_content)

    return "\n".join(combined_chunks), book_id

# --- Generate variants of the query ---
def generate_queries(original_query):
    chain = rephraser_prompt | rephraser_llm
    output = chain.invoke({"question": original_query})
    text_output = output.content

    queries = [
        line.strip()
        for line in text_output.strip().split("\n")
        if line.strip() and not line.strip().startswith("###")
    ]
    print(queries)
    return queries

# --- Retrieve relevant context and doc IDs ---
def retrieve_contexts(query):
    context_docs = retriever.invoke(query)
    retrieved_ids = [doc.metadata['idx'] for doc in context_docs]
    retrieved_bids = [doc.metadata['book_id'] for doc in context_docs]
    full_chunks = []
    for idx in retrieved_ids:
        chunk_text, book_id = get_context_with_neighbors(idx, data)
        book_id_str = str(book_id)
        full_chunk = f"[Book ID: {book_id_str}]\n{chunk_text}"
        full_chunks.append(full_chunk)

    full_context = "\n\n".join(full_chunks)
    return full_context, retrieved_bids

# --- Check if the context supports the query ---
def is_supported_by_context(query, context):
    result = (verifier_prompt | verifier_llm).invoke({
        "query": query,
        "context": context
    }).content.strip()
    # Parse expected format:
    # Support level: Partial support
    # Relevant quotes (if any):
    data = json.loads(result)
    support_level = data.get("support_level")
    quotes = data.get("quotes", [])
    if support_level and support_level.lower() in ["strong support", "partial support", "no support"]:
        quote_texts = [q["text"] for q in quotes]
        book_ids = [q["book_id"] for q in quotes]
        return support_level, quote_texts, book_ids
    else:
        return None
    

# --- Perform self-consistency to get the most robust answer ---
def get_consistent_answer(query, context_text, n_consistency=5):
    def single_call(_):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return (answer_prompt | answer_llm).invoke({
                    "query": query,
                    "context": context_text
                }).content.strip()
            except RateLimitError:
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    raise

    with ThreadPoolExecutor() as executor:
        answers = list(executor.map(single_call, range(n_consistency)))

    if len(set(answers)) == 1:
        return answers[0]

    formatted_answers = "\n\n".join([
        f"Answer {i+1}:\n{ans}" for i, ans in enumerate(answers)
    ])

    judge_output = (judge_prompt | judge_llm).invoke({
        "query": query,
        "context": context_text,
        "answers": formatted_answers
    }).content.strip()

    match = re.search(r"Answer\s*(\d+)", judge_output)
    if match:
        chosen_index = int(match.group(1)) - 1
        if 0 <= chosen_index < len(answers):
            return answers[chosen_index]

    return answers[0]

def translate_response(query, text):
    style_chain = style_prompt | style_llm
    response = style_chain.invoke({"input": text})

    lang = detect_lang_ld(query)
    print(f"Detected language: {lang}")
    if lang != "he":
        translation_chain = translation_prompt | translation_llm
        trans_response = translation_chain.invoke({"input": response})
    else:
        trans_response = response

    return trans_response.content.strip()

# --- Main function: pipeline to process query and return final answer ---
def answer_query(user_query, to_print=False):
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "original_query": user_query,
        "query_language": detect_lang_ld(user_query),
        "rephrased_queries": [],
        "used_query": user_query,
        "support_level": None,
        "book_ids": [],
        "pre_translated_answer": None,
        "final_answer": None
    }
    # First try the original query
    context_text, retrieved_bids = retrieve_contexts(user_query)
    support_level, quotes, book_ids = is_supported_by_context(user_query, context_text)

    log_entry["support_level"] = support_level

    if support_level == "Strong support":
        response = get_consistent_answer(user_query, quotes)
        context_display = "\n".join(quotes)
        returned_bids = book_ids
        log_entry["book_ids"] = book_ids

    elif support_level == "Partial support":
        response = get_consistent_answer(user_query, context_text)
        context_display = context_text
        returned_bids = retrieved_bids
        log_entry["book_ids"] = retrieved_bids

    else:
        # No support – try query variants
        queries = generate_queries(user_query)
        log_entry["rephrased_queries"] = queries

        for q in queries:
            context_text, retrieved_bids = retrieve_contexts(q)
            support_level, quotes, book_ids = is_supported_by_context(user_query, context_text)

            if support_level == "Strong support":
                response = get_consistent_answer(user_query, quotes)
                context_display = "\n".join(quotes)
                returned_bids = book_ids
                log_entry.update({
                    "support_level": support_level,
                    "used_query": q,
                    "book_ids": book_ids
                })
                break

            elif support_level == "Partial support":
                response = get_consistent_answer(user_query, context_text)
                context_display = context_text
                returned_bids = retrieved_bids
                log_entry.update({
                    "support_level": support_level,
                    "used_query": q,
                    "book_ids": retrieved_bids
                })
                break
        else:
            # No support found at all
            response = get_consistent_answer(user_query, "")
            returned_bids = []

    log_entry["pre_translated_answer"] = response
    final_response = translate_response(user_query, response)
    log_entry["final_answer"] = final_response

    # Success case
    if to_print:
        print(f"User's Question: {user_query}\nFinal Answer: {final_response}")
        print("\nContext:\n", context_display)
        
    log_interaction(log_entry)

    return final_response, (", ".join(str(bid) for bid in returned_bids))


def load_pkl(path):
    pickle_file = os.path.join(DATA_PATH, path)
    return pd.read_pickle(pickle_file)


def initialize_components():
    global data, retriever, vectorstore, answer_prompt, answer_llm, rephraser_prompt, rephraser_llm, verifier_prompt, verifier_llm, judge_prompt, judge_llm, translation_prompt, translation_llm, style_prompt, style_llm
    data = load_pkl('combined_chunks.pkl')
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")
    answer_prompt, answer_llm, rephraser_prompt, rephraser_llm, verifier_prompt, verifier_llm, judge_prompt, judge_llm, style_prompt, style_llm, translation_prompt, translation_llm = initialize_llm()
    retriever = initialize_retriever("faiss_index_openai_3textlarge_copy", embedding_model)
    print("Done initialize")


if __name__ == "__main__":
    initialize_components()
