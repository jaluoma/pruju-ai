import os
#from customllm_langchain.custom_azure import MyChat # Import custom wrapper
from langchain.schema import AIMessage, SystemMessage, HumanMessage
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import AzureChatOpenAI
import tiktoken

#chat = MyChat() # Initialize chat model

# openai.api_base = "http://127.0.0.1:7080"
# openai.api_key = os.getenv("AZURE_OPENAI_KEY")
# openai.api_type = "azure"
# openai.api_version = "2023-05-15"
# BASE_URL = openai.api_base
# API_KEY = openai.api_key
# DEPLOYMENT_NAME = "chat"
chat = AzureChatOpenAI(
    openai_api_base="http://127.0.0.1:7080",
    openai_api_version="2023-05-15",
    deployment_name='gpt-4', #"gpt-35-turbo",
    openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
    openai_api_type="azure",
)

# Define functions for memory management

def purge_memory(messages, max_tokens: int):

    token_count = token_counter(messages)
    if (len(messages)>1):
        while (token_count>max_tokens):
            print("Purged the following message:\n" + messages[1].content)
            messages.pop(1)
            token_count = token_counter(messages)
    return

def token_counter(messages):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    concatenated_content = ''.join([message.content for message in messages])
    token_count = len(encoding.encode(concatenated_content))
    return token_count

# Read knowledge base

knowledge_base = FAISS.load_local(os.getenv("CHAT_DATA_FOLDER")+"/faiss_index", HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl"))

instruction_file = open(str(os.getenv("CHAT_DATA_FOLDER"))+"/prompt_template.txt",'r')
system_instruction_template = instruction_file.read()
print("System instruction template:\n" + system_instruction_template)

def query_gpt_chat(query: str, history, max_tokens: int):
    
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
    print("Message purge")
    print("tokens: " + str(token_counter(messages)))
    purge_memory(messages,max_tokens)
    print("tokens: " + str(token_counter(messages)))

    #print(str(messages))

    # Query chat model
    results = chat(messages)
    results_content = results.content

    return results_content


