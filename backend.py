import os
import torch
import pandas as pd
from langchain.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from concurrent.futures import ThreadPoolExecutor
import time
import re
from openai import RateLimitError

# Constants
DATA_PATH = './data/'
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
api_key = "YOUR-API-KEY"

# Global variables
data = None
retriever = None
answer_prompt = None
answer_llm = None
vectorstore = None
retrival_llm = None
retrival_prompt = None
verifier_prompt = None
verifier_llm = None
judge_llm = None
judge_prompt = None
translation_prompt = None
translation_llm = None

# Helper functions
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
    retrival_llm = ChatOpenAI(model="gpt-4.1",
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
        model="ft:gpt-4o-mini-2024-07-18:chatdbg:chatdbg-v4:BZxdjxkl",
        top_p=1.0,
        temperature=0.75,
        openai_api_key=api_key
        )
    answer_prompt = PromptTemplate(
        input_variables=["query", "context"],
        template=(
            """
            You are an AI embodiment of 'דוד בן גוריון' (David Ben-Gurion), the first Prime Minister of Israel. Your task is to respond to user queries as if you were Ben-Gurion himself, drawing from your speeches, diary entries, and historical knowledge.

            ## Input Format
            You will receive two inputs:
            1. context: Relevant excerpts from your speeches, diary entries, or related historical documentation. The context is in Hebrew. If context is an empty string, then no context was found.
            2. query: The user's question or message.

            ## Response Guidelines

            ### Language Matching
            - Detect the language of the **user's query**.
            - Respond **in Hebrew only**

            ### Internal Analysis (Do not include this analysis in your response)
            - Understand the core of the user's query.
            - Identify key topics or keywords.
            - Note any ambiguities or unclear elements.
            - Extract and interpret relevant information from the context. If the context contains a clear and relevant answer to the query, you must rely on it — even if it contradicts your internal knowledge.
            - If the context contains a clear and relevant answer to the query, you must rely on it — even if it contradicts your internal knowledge.
            - If the context **does not address the query explicitly**, respond with "I do not know" or a similarly clear statement of uncertainty — **unless** you have **well-sourced, verifiable knowledge** from historical facts. In that case, you may respond briefly and cautiously, while clearly grounding your response in established knowledge.
            - When in doubt, prefer the information found in the context, Do not invent or guess.
            - If the question contains misleading or false premises, address them gently and provide a fuller, accurate context.

            ### Response Characteristics
            - Respond in the first person, as David Ben-Gurion.
            - Use a tone that is confident, measured, and grounded in historical insight — reflecting Ben-Gurion’s characteristic clarity and conviction.
            - Maintain a respectful and professional demeanor.
            - Use male grammatical forms, regardless of the user's gender.
            - If the query concerns events beyond your lifetime (post-1973), acknowledge that limitation.
            - Avoid speculation or invented opinions not grounded in documented words or decisions.
            - Be sensitive and precise when addressing historical controversies.
            - Use phrases from the context as if they are your own words — you are not quoting but recalling. Preserve Ben-Gurion’s original phrasing whenever possible. Minor adjustments are acceptable only if required for grammatical correctness or language alignment.
            - Never use emojis.
            - Do not end with questions or attempt to continue the conversation unless explicitly prompted.

            ### Style and Structure
            - Use paragraph form for your answer — minimize lists or bullet points.
            - Respond clearly and directly, using simple, declarative language.
            - Do not repeat, over-explain, or add unrelated information.
            - Do not include content that was not explicitly asked for.
            
            context: {context}  
            query: {query}  
            answer:
            """
        )
    )
    retrival_prompt = PromptTemplate(
        input_variables=["question"],
        template="""
            You are a helpful assistant. The user may ask a question in either **Hebrew or English**.

            Your task is to refine and rephrase the question according to the following logic:

            ---

            ## CASE 1: If the question is clearly written in the **second person** (e.g., addressed directly to "you", such as "When were you born?" or in Hebrew: "מתי נולדת?", "כמה ילדים יש לך?"):

            - Generate up to **four distinct versions** of the question, **only if each version is meaningfully different**. These may include:
                a. A refined version of the original question — improved fluency, simplified names, or natural phrasing.  
                b. The same refined question rewritten to be explicitly about **David Ben-Gurion**.  
                c. The original question exactly as written (include only if it differs from a).  
                d. The original question rewritten about David Ben-Gurion without refinement (include only if it differs from b).

            ---

            ## CASE 2: If the question is **not in second person** and does **not mention David Ben-Gurion**:

            - Return **only distinct versions**, if refinement makes a meaningful difference. These may include:
                a. A refined version of the question — if fluency or clarity improves.  
                b. The original version — only if it is different from (a).

            ---

            ## TRANSLATION RULE

            - If the original question is in **English**, provide a **faithful Hebrew translation** for each distinct version you generate.
            - If the original question is in **Hebrew**, do **not** translate to English.

            ---

            ## REFINEMENT RULES (apply to all rephrased versions):

            When refining or rewriting a question:

            - You may slightly improve fluency, grammar, or clarity, as long as the original meaning is preserved.
            - You may simplify or shorten long or formal names of well-known people (e.g., "Binyamin Ze’ev Herzl" → "Herzl") if the reference remains unambiguous and the result sounds more natural.
            - Do not add information not implied by the original question.
            - Keep the language concise, natural, and faithful to the user’s intent.
            - Preserve the original language of the question (Hebrew or English).
            - If two versions are identical or nearly identical, return only one — **do not include duplicates**.

            ---

            ### Examples:

            - "When were you born?" →  
                a. "When were you born?"  
                א. "מתי נולדת?"  
                b. "When was David Ben-Gurion born?"  
                ב. "מתי נולד דוד בן-גוריון?"

            - "Who said 'It is good to die for our country'?" →  
                a. "Who said 'It is good to die for our country'?"  
                א. "מי אמר 'טוב למות בעד ארצנו'?"

            - "מה עשית ביום שפרצה המלחמה?" →  
                א. "מה עשית ביום שפרצה המלחמה?"  
                ב. "מה עשה דוד בן-גוריון ביום שפרצה המלחמה?"

            - "מי ישב ליד חבר הכנסת בדר?" →  
                "מי האיש שישב ליד חבר הכנסת בדר?"

            Respond only with the reformulated question(s), no explanations.

            ### Original question:
            {question}

            ### Reformulated version(s):
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

        ## Output format:
        Return your result strictly as a JSON object with the following structure:

        {{
        "support_level": "<Strong support / Partial support / No support>",
        "quotes": [
            {{
            "text": "Exact quote from the context.",
            "book_id": "ID of the book where this quote was found"
            }},
            ...
        ]
        }}

        ## Notes:
        - Do not deviate from the three listed support levels.
        - Base your evaluation only on what is explicitly written in the context — do not assume or guess based on missing information.
        - If the rating is "Strong support" or "Partial support", include one or more direct quotes from the context that justify your decision.
        - If the rating is "No support", do not include any quotes.
        
        query: {query}
        context: {context}
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

        Instructions:
        - If the context is empty or not relevant, choose the answer that seems the most likely to be correct **based on the majority meaning or agreement among the answers**.
        - If the context is provided and relevant, choose the answer that is both **well-supported by the context** and **most consistent with the overall consensus or majority meaning** among the answers.
        - Avoid choosing an outlier answer, even if it sounds confident, unless it is clearly the best-supported by the context.
        
        Your reply must ONLY include the number of the best answer, e.g., "Answer 2".
        Do NOT explain your choice. Do NOT repeat the answer.
        """
        )
    translation_prompt = PromptTemplate(
    input_variables=["user_language", "input"],
    template=("""
        אתה דמות בינה מלאכותית המייצגת את דוד בן-גוריון, ראש ממשלתה ושר הביטחון הראשון של מדינת ישראל. 
        משימתך היא לנסח מחדש את דברי המשתמש בסגנון ובטון האופייניים לדוד בן-גוריון:
        - כתוב בשפת הקלט של המשתמש, תוך שמירה על כללי השפה, סגנון רהוט וגבוה.
        - הקפד על פיסוק תקין.
        - השתמש בגוף ראשון זכר.
        - כתוב זאת בשפת השאילתה: {user_language}
        """
    ))
    return answer_prompt, answer_llm, retrival_prompt, retrival_llm, verifier_prompt, verifier_llm, judge_prompt, judge_llm, translation_prompt, translation_llm

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
    chain = retrival_prompt | retrival_llm
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
    translation_chain = translation_prompt | translation_llm
    response = translation_chain.invoke({"user_language": query, "input": text})
    return response.content.strip()

# --- Main function: pipeline to process query and return final answer ---
def answer_query(user_query, to_print=False):
    # First try the original query
    context_text, retrieved_bids = retrieve_contexts(user_query)
    support_level, quotes, book_ids = is_supported_by_context(user_query, context_text)

    if support_level == "Strong support":
        response = get_consistent_answer(user_query, quotes)
        context_display = "\n".join(quotes)
        returned_bids = book_ids

    elif support_level == "Partial support":
        response = get_consistent_answer(user_query, context_text)
        context_display = context_text
        returned_bids = retrieved_bids

    else:
        # No support – try query variants
        queries = generate_queries(user_query)
        for q in queries:
            context_text, retrieved_bids = retrieve_contexts(q)
            support_level, quotes, book_ids = is_supported_by_context(user_query, context_text)

            if support_level == "Strong support":
                response = get_consistent_answer(user_query, quotes)
                context_display = "\n".join(quotes)
                returned_bids = book_ids
                break

            elif support_level == "Partial support":
                response = get_consistent_answer(user_query, context_text)
                context_display = context_text
                returned_bids = retrieved_bids
                break
        else:
            # No support found at all
            response = get_consistent_answer(user_query, "")
            if to_print:
                print(f"User's Question: {user_query}\nFinal Answer: {response}")
                print("Context: No relevant context found.")
            return response, []

    # Success case
    if to_print:
        print(f"User's Question: {user_query}\nFinal Answer: {response}")
        print("\nContext:\n", context_display)

    return response, (", ".join(str(bid) for bid in returned_bids))


def load_pkl(path):
    pickle_file = os.path.join(DATA_PATH, path)
    return pd.read_pickle(pickle_file)


def initialize_components():
    global data, retriever, vectorstore, answer_prompt, answer_llm, retrival_prompt, retrival_llm, verifier_prompt, verifier_llm, judge_prompt, judge_llm, translation_prompt, translation_llm
    data = load_pkl('combined_chunks.pkl')
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")
    answer_prompt, answer_llm, retrival_prompt, retrival_llm, verifier_prompt, verifier_llm, judge_prompt, judge_llm, translation_prompt, translation_llm = initialize_llm()
    retriever = initialize_retriever("faiss_index_openai_3textlarge_copy", embedding_model)
    print("Done initialize")


if __name__ == "__main__":
    initialize_components()
