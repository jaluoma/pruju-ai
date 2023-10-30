from loguru import logger
from datetime import datetime

import os
from langchain.schema import AIMessage, SystemMessage, HumanMessage
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain.chat_models import ChatOllama
from langchain.callbacks import get_openai_callback

from dotenv import load_dotenv 
load_dotenv()

from chat_utils import purge_memory

# Control parameters
max_default_calls_per_day = int(os.getenv("DEFAULT_MODEL_QUOTA"))
max_total_calls_per_day = int(os.getenv("TOTAL_MODEL_QUOTA"))

# Log-file definition
isDocker = os.path.exists("/.dockerenv")
log_path = "/logs" if isDocker else "logs"
log_file = f"{log_path}/call_log_{{time:YYYY-MM-DD}}.log"
logger.remove()
logger.add(log_file, rotation="1 day", format="{time} {message}", level="INFO")

# Initialize chat model

llm_provider = os.getenv("LLM_PROVIDER")
print("Using LLM-provider: " + llm_provider)

# Define chat engines

def initialize_chat(llm_provider):
    # define chat engines 
    default_model = "gpt-4"
    fallback_model = "gpt-35-turbo"

    if llm_provider=="azure":
        chat = AzureChatOpenAI(
            openai_api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
            openai_api_version="2023-05-15",
            deployment_name=default_model,
            openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
            openai_api_type="azure",
            temperature=0,
        )
    elif llm_provider=="openai":
        chat = ChatOpenAI(temperature=0,
                        model_name=default_model, 
                        openai_api_key=os.getenv("OPENAI_API_KEY"))
        fallback_model = "gpt-3.5-turbo"
    elif llm_provider=="ollama":
        chat = ChatOllama(model=os.getenv("OLLAMA_MODEL_NAME"),temperature=0)
    elif llm_provider=="null":
        chat = None
    else:
        raise ValueError("LLM-provider not recognized. Check LLM_PROVIDER environment variable.")
    return chat, default_model, fallback_model

try:
    chat, default_model, fallback_model = initialize_chat(llm_provider)
except ValueError as e:
    print(e)
    exit(1)

def change_chat_engine(chat_model,desired_engine):
    if isinstance(chat_model,AzureChatOpenAI):
        chat.deployment_name = desired_engine
    elif isinstance(chat_model,ChatOpenAI):
        chat.model_name = desired_engine
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
        daily_calls_sum = get_daily_calls(f"{log_path}/call_log_{datetime.now().strftime('%Y-%m-%d')}.log")
    except FileNotFoundError:
        daily_calls_sum = 0
        logger.remove()
        logger.add(log_file, rotation="1 day", format="{time} {message}", level="INFO")
    return daily_calls_sum

def choose_model(daily_calls_sum):
    if daily_calls_sum > max_total_calls_per_day:
        return "END"
    elif daily_calls_sum > max_default_calls_per_day:
        current_model=fallback_model
        change_chat_engine(chat,current_model)
        return current_model
    else:
        current_model=default_model
        change_chat_engine(chat,current_model)
        return current_model
    
# Read knowledge base
os.environ['TOKENIZERS_PARALLELISM'] = 'false' # Avoid warning: https://github.com/huggingface/transformers/issues/5486
vector_store = FAISS.load_local(os.getenv("CHAT_DATA_FOLDER")+"/faiss_index", HuggingFaceInstructEmbeddings(cache_folder=os.getenv("MODEL_CACHE"), model_name="sentence-transformers/all-MiniLM-L6-v2"))
instruction_file = open(str(os.getenv("CHAT_DATA_FOLDER"))+"/prompt_template.txt",'r')
system_instruction_template = instruction_file.read()
print("System instruction template:\n" + system_instruction_template)

# Main chat caller function

def query_gpt_chat(query: str, history, max_tokens: int):
    max_tokens=int(os.getenv("MAX_PROMPT_TOKENS"))
    # Check quota status and update model accordingly
    daily_calls_sum = check_quota_status()
    current_model = choose_model(daily_calls_sum)
    if current_model == "END":
        change_chat_engine(chat,default_model)
        return None, "I've been dealing with so many requests today that I need to rest a bit. Please come back tomorrow!"

    # Search vector store for relevant documents
    docs = vector_store.similarity_search(query)
    context = "NEW DOCUMENT:\n"+"\nNEW DOCUMENT:\n".join(doc.page_content for doc in docs)

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
    purge_memory(messages,current_model, max_tokens)
    # print("First message: \n" + str(messages[1].type))

    #print(str(messages))

    if llm_provider != 'null':
        # Query chat model
        with get_openai_callback() as cb:
            results = chat(messages)
        print(cb)

        # Log statistics
        query_statistics = [cb.prompt_tokens, cb.completion_tokens, cb.total_cost, cb.successful_requests]
        query_statistics = ",".join(str(i) for i in query_statistics)+ " " + str(daily_calls_sum+cb.successful_requests) 
        logger.info(query_statistics)
        
        results_content = results.content
    else:
        # debug mode:
        results_content = context

    return current_model, results_content
