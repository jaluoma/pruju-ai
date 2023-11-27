# Script for trying out streaming with langchain

import os

from langchain.schema import AIMessage, SystemMessage, HumanMessage
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import get_openai_callback

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


from dotenv import load_dotenv
load_dotenv()

print("API KEY: "+os.getenv("OPENAI_API_KEY"))

chat = ChatOpenAI(temperature=0,streaming=True, callbacks=[StreamingStdOutCallbackHandler()])
system = SystemMessage(content="You are a helpful assistant that translates sentences from English to verbose giberrish.")
human = HumanMessage(content="I love Git.")
messages = [system, human]

print("Trying with GPT-3.5: ")
chat.model_name = "gpt-3.5-turbo"
print("Model name: " + chat.model_name)
with get_openai_callback() as cb:
    ai = chat(messages)
print(cb)

print(ai.content)

print("Trying with GPT-4: ")
chat.model_name = "gpt-4"
print("Model name: " + chat.model_name)
with get_openai_callback() as cb:
    ai = chat(messages)
print(cb)

print(ai.content)