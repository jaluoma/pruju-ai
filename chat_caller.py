from loguru import logger
from datetime import datetime

import os
from langchain.schema import AIMessage, SystemMessage, HumanMessage
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chat_models import ChatOllama
from langchain.callbacks import get_openai_callback

import httpx

from dotenv import load_dotenv 
load_dotenv()
isDocker = os.path.exists("/.dockerenv")
if isDocker:
    os.environ["CHAT_DATA_FOLDER"] = "/"+os.getenv("CHAT_DATA_FOLDER")

from chat_utils import purge_memory, token_counter

# Control parameters
max_total_calls_per_day = int(os.getenv("TOTAL_MODEL_QUOTA"))

# Log-file definition
root_path = os.getenv("ROOT_PATH")
log_path = "/logs" if isDocker else "logs"
log_file = f"{log_path}/{root_path}_call_log_{{time:YYYY-MM-DD}}.log"
logger.remove()
logger.add(log_file, rotation="1 day", format="{time} {message}", level="INFO")

# Initialize chat model
llm_provider = os.getenv("LLM_PROVIDER")
print("Using LLM-provider: " + llm_provider)

# Modify this to identify languages
if os.getenv("DOC_LANGUAGE") == "fi":
    doc_language="Finnish"
else:
    doc_language="English"

# Define chat engines

def initialize_chat(llm_provider):
    default_model = os.getenv("MODEL_NAME")
    if llm_provider=="azure":
        # URL backend and authentication customization
        # https://github.com/openai/openai-python/issues/547#issuecomment-1795526894
        def update_base_url(request: httpx.Request) -> None:
            if os.getenv("AZURE_OPENAI_CUSTOM_BACKEND") is not None:
                if request.url.path == "/chat/completions":
                    request.url = request.url.copy_with(path=os.getenv("AZURE_OPENAI_CUSTOM_BACKEND"))
        chat = ChatOpenAI(
            openai_api_base=os.getenv("MODEL_ENDPOINT"),
            model_name=default_model,
            temperature=0,
            default_headers=(
                        {os.getenv("AZURE_OPENAI_CUSTOM_HEADER"): os.environ.get("OPENAI_API_KEY")} 
                        if os.getenv("AZURE_OPENAI_CUSTOM_HEADER") is not None
                        else {"Authorization": "Bearer "+os.environ.get("OPENAI_API_KEY")}
            ),

            http_client=httpx.Client(
                event_hooks={
                    "request": [update_base_url],
                }
                ),
            )

    elif llm_provider=="openai":
        chat = ChatOpenAI(temperature=0,
                        model_name=default_model)
    elif llm_provider=="ollama":
        chat = ChatOllama(model=default_model,temperature=0)
    elif llm_provider=="null":
        chat = None
    else:
        raise ValueError("LLM-provider not recognized. Check LLM_PROVIDER environment variable.")
    return chat, default_model

try:
    chat, default_model = initialize_chat(llm_provider)
except ValueError as e:
    print(e)
    exit(1)

# Function to change model, deprecated
def change_chat_engine(chat_model,desired_engine):
    if isinstance(chat_model,ChatOpenAI):
        chat.model_name = desired_engine
    elif isinstance(chat_model,ChatOllama):
        chat.model = desired_engine
    else:
        print("Unsupported model detected")
        return 0

# Book-keeping for quota monitoring 

def get_daily_calls(log_file):
    # Loop through lines in file and return the number after ' ' on the last line
    # This is the cumulative number of calls so far
    with open(log_file, 'r') as file:
        last_line = None
        for line in file:
            last_line = line
        if last_line:
            return int(last_line.split(' ')[-1])
        else:
            return 0
        
def check_quota_status():
    try:
        daily_calls_sum = get_daily_calls(f"{log_path}/{root_path}_call_log_{datetime.now().strftime('%Y-%m-%d')}.log")
    except FileNotFoundError:
        daily_calls_sum = 0
        logger.remove()
        logger.add(log_file, rotation="1 day", format="{time} {message}", level="INFO")
    return daily_calls_sum

def choose_model(daily_calls_sum):
    if daily_calls_sum > max_total_calls_per_day:
        return "END"
    else:
        current_model=default_model
        return current_model
    
def provide_context_for_question(query, smart_search=False):
    if smart_search==True:
        system="""
        You are an AI that provides assistance in database search. 
        Please translate the user's query to a list of search keywords
        that will be helpful in retrieving documents from a database
        based on similarity.
        The language of the keywords should match the language of the documents: 
        """+doc_language+"""\n
        Answer with a list of keywords.
        """
        query=chat(
            [SystemMessage(content=system),
             HumanMessage(content=query)]
        ).content
    if os.getenv("DOCS_N") is not None:
        docs = vector_store.similarity_search(query, k = int(os.getenv("DOCS_N")))
    else:
        docs = vector_store.similarity_search(query)
    context = "\n---\n".join(doc.page_content for doc in docs)
    return context

# Read knowledge base
os.environ['TOKENIZERS_PARALLELISM'] = 'false' # Avoid warning: https://github.com/huggingface/transformers/issues/5486
print("Vector store: " + str(os.getenv("VECTOR_STORE")))
if os.getenv("VECTOR_STORE") is None or os.getenv("VECTOR_STORE")=="faiss":
    print("Using local FAISS.")
    from langchain.vectorstores import FAISS
    vector_store = FAISS.load_local(os.getenv("CHAT_DATA_FOLDER")+"/faiss_index", HuggingFaceInstructEmbeddings(cache_folder=os.getenv("MODEL_CACHE"), model_name="sentence-transformers/all-MiniLM-L6-v2"))
elif os.getenv("VECTOR_STORE")=="qdrant":
    from langchain.vectorstores import Qdrant
    from qdrant_client import QdrantClient
    client = QdrantClient(url=os.getenv("VECTOR_STORE_ENDPOINT"),api_key=os.getenv("VECTOR_STORE_API_KEY"))
    collection_name = os.getenv("VECTOR_STORE_COLLECTION")
    vector_store = Qdrant(client, collection_name, HuggingFaceInstructEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"))
else:
    print("Vector store not identified. Exiting.")
    exit(1)

# Admin token check
def check_admin_token(admin_token):    
    if admin_token is not None and os.getenv("ADMIN_TOKEN") is not None and admin_token == os.getenv("ADMIN_TOKEN"):
        model_string = default_model + "-" + admin_token
    else:
        model_string = default_model
    return model_string

instruction_file = open(str(os.getenv("CHAT_DATA_FOLDER"))+"/prompt_template.txt",'r')
system_instruction_template = instruction_file.read()
print("System instruction template:\n" + system_instruction_template)

# Main chat caller function

def query_gpt_chat(query: str, history, prompt_logging_enabled: bool, conversation_id: str, admin_token: str = None):
    max_tokens=int(os.getenv("MAX_PROMPT_TOKENS"))
    # Check quota status and update model accordingly
    daily_calls_sum = check_quota_status()
    current_model = choose_model(daily_calls_sum)
    if current_model == "END":
        return None, "I've been dealing with so many requests today that I need to rest a bit. Please come back tomorrow!"

    # Search vector store for relevant documents
    context = provide_context_for_question(query)

    # Combine instructions + context to create system instruction for the chat model
    system_instruction = system_instruction_template + context

    # Convert message history to list of message objects
    messages_history = []
    i = 0
    for message in history:
        if i % 2 == 0: 
            messages_history.append(HumanMessage(content=message))
        else:
            messages_history.append(AIMessage(content=message))
        i += 1
    
    # Initialize message list
    messages = [SystemMessage(content=system_instruction)]
    for message in messages_history:
        messages.append(message)
    messages.append(HumanMessage(content=query))

    # Purge memory to save tokens
    # Current implementation is not ideal.
    # Gradio keeps the entire history in memory 
    # Therefore, the messages memory is re-purged on every call once token count max_tokens 
    # print("Message purge")
    token_count = purge_memory(messages,current_model, max_tokens)
    # print("First message: \n" + str(messages[1].type))
    # print(str(messages))
    # print(token_count)
    if llm_provider != 'null':
        results = chat(messages)
        result_tokens = token_counter([results],default_model)
        print(f"Prompt tokens: {token_count}")
        print(f"Completion tokens: {result_tokens}")
        total_tokens = token_count+result_tokens
        print(f"Total tokens: {total_tokens}")

        # Log statistics
        results_content = results.content
        query_statistics = [token_count, result_tokens, total_tokens, 1]
        if prompt_logging_enabled == True:
            text1 = query.replace("\n", "\\n")
            text2 = results_content.replace("\n", "\\n")
            logged_prompt = f"<{conversation_id}>".join([text1,text2])
        else:
            logged_prompt = "DISABLED"
        model_string=check_admin_token(admin_token)
        #print(model_string)
        query_statistics = model_string+","+conversation_id+","+logged_prompt+","+",".join(str(i) for i in query_statistics)+ " " + str(daily_calls_sum+1) 
        logger.info(query_statistics)
        
        
    else:
        # debug mode:
        results_content = context

    return current_model, results_content

def write_log_removal_request(conversation_id, admin_token):
    daily_calls_sum = check_quota_status()
    model_string=check_admin_token(admin_token)
    logger.info(model_string+
                ","+conversation_id+
                ","+"PROMPT REMOVAL REQUEST"+f"<{conversation_id}>"+
                ","+
                ",".join(str(i) for i in [0, 0, 0, 0])+ " " + str(daily_calls_sum))
    return True

def log_vote(liked, value,conversation_id, prompt_logging_enabled, admin_token):
    daily_calls_sum = check_quota_status()
    vote_type = "UPVOTE" if liked else "DOWNVOTE"
    output=str(value) if prompt_logging_enabled else "DISABLED"
    output = output.replace("\n", "\\n")
    model_string=check_admin_token(admin_token)
    logger.info(model_string +
                ","+ conversation_id +
                ","+ vote_type +
                f"<{conversation_id}>" + output + "," +
                ",".join(str(i) for i in [0, 0, 0, 0])+ " " + str(daily_calls_sum))
    return True
