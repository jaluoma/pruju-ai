from loguru import logger
from datetime import datetime

import os
from langchain.schema import AIMessage, SystemMessage, HumanMessage
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import AzureChatOpenAI
import tiktoken
from langchain.callbacks import get_openai_callback

# Define chat engine
default_model = "gpt-4"
fallback_model = "gpt-35-turbo"

# Control parameters:
max_default_calls_per_day = 3
max_total_calls_per_day = 5

# Log-file definition
logger.remove()
logger.add("logs/call_log_{time:YYYY-MM-DD}.log", rotation="1 day", format="{time} {message}", level="INFO")

# Initialize chat model
chat = AzureChatOpenAI(
    openai_api_base="http://127.0.0.1:7080",
    openai_api_version="2023-05-15",
    deployment_name=default_model,
    openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
    openai_api_type="azure",
)

# Define functions for memory management

def purge_memory(messages, max_tokens: int):

    token_count = token_counter(messages)
    if (len(messages)>1):
        while (token_count>max_tokens):
            # Print purged message for testing purposes
            # print("Purged the following message:\n" + messages[1].content)
            messages.pop(1)
            token_count = token_counter(messages)
    return

def token_counter(messages):
    current_model = chat.deployment_name
    print("Counting tokens based on: " + current_model)
    if current_model == default_model:
        encoding = tiktoken.encoding_for_model("gpt-4")
    else:
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    concatenated_content = ''.join([message.content for message in messages])
    token_count = len(encoding.encode(concatenated_content))
    return token_count

# Book-keeping for quota monitoring 

def get_daily_calls(log_file):
    # Loop through lines in file and return the number after ;
    # This is the cumulative number of calls so far
    with open(log_file, 'r') as file:
        last_line = None
        for line in file:
            last_line = line
        if last_line:
            return int(last_line.strip().split(';')[-1])
        else:
            return 0
        
def check_quota_status():
    try:
        daily_calls_sum = get_daily_calls(f"logs/call_log_{datetime.now().strftime('%Y-%m-%d')}.log")
    except FileNotFoundError:
        daily_calls_sum = 0
        logger.remove()
        logger.add("logs/call_log_{time:YYYY-MM-DD}.log", rotation="1 day", format="{time} {message}", level="INFO")
    return daily_calls_sum

def choose_model(daily_calls_sum):
    if daily_calls_sum > max_total_calls_per_day:
        return "END"
    elif daily_calls_sum > max_default_calls_per_day:
        current_model=fallback_model
        chat.deployment_name=current_model
        return current_model
    else:
        current_model=default_model
        chat.deployment_name = current_model
        return current_model

# Read knowledge base

knowledge_base = FAISS.load_local(os.getenv("CHAT_DATA_FOLDER")+"/faiss_index", HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl"))
instruction_file = open(str(os.getenv("CHAT_DATA_FOLDER"))+"/prompt_template.txt",'r')
system_instruction_template = instruction_file.read()
print("System instruction template:\n" + system_instruction_template)

# Main chat caller function

def query_gpt_chat(query: str, history, max_tokens: int):

    # Check quota status and update model accordingly
    daily_calls_sum = check_quota_status()
    current_model = choose_model(daily_calls_sum)
    if current_model == "END":
        current_model=default_model
        return("I've been dealing with so many requests today that I need to rest a bit. Please come back tomorrow!")

    # Search knowledge base for relevant documents
    docs = knowledge_base.similarity_search(query)
    context = str(docs)

    # Combine instructions + context to create system instruction for the chat model
    system_instruction = system_instruction_template + context

    # Read messages from history
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
    #print("Message purge")
    #print("tokens: " + str(token_counter(messages)))
    purge_memory(messages,max_tokens)
    #print("tokens: " + str(token_counter(messages)))

    #print(str(messages))

    # Query chat model
    with get_openai_callback() as cb:
        results = chat(messages)
    print(cb)

    query_statistics = [cb.prompt_tokens, cb.completion_tokens, cb.total_cost, cb.successful_requests]
    query_statistics = ",".join(str(i) for i in query_statistics)+";" + str(daily_calls_sum+cb.successful_requests) 
    logger.info(query_statistics)
    
    results_content = results.content

    return results_content