from dotenv import load_dotenv
load_dotenv()

import gradio as gr
from chat_caller import query_gpt_chat
import os

from aaltotheming import aaltobluetheme

def courseGPT(query, chat_history):
    max_tokens = 2000
    # unpack history
    chat_history_unpacked = []
    for x in chat_history:
        for y in x:
            chat_history_unpacked.append(y)
    return(query_gpt_chat(query,chat_history_unpacked,max_tokens))

with open(os.getenv("CHAT_DATA_FOLDER")+'/examples_ui.txt', 'r') as file: 
    examples = file.readlines()
examples = [example.strip() for example in examples]

with open(os.getenv("CHAT_DATA_FOLDER")+'/chat_description.txt', 'r') as file: 
    chat_description = file.read().strip()

chat_description=chat_description.strip()

with open(os.getenv("CHAT_DATA_FOLDER")+'/chat_name.txt', 'r') as file: 
    chat_name = file.read().strip()

demo = gr.ChatInterface(fn=courseGPT, 
                        analytics_enabled=False, 
                        examples = examples,
                        theme=aaltobluetheme,
                        title=chat_name,
                        description=chat_description,
                        undo_btn="Undo",
                        retry_btn="Retry",
                        clear_btn="Clear")

if __name__ == "__main__":
    print("Launching Demo\n")
    server_name = "127.0.0.1"
    isDocker = os.path.exists("/.dockerenv")
    print(f"Docker: {isDocker}\n")
    demo.launch(server_name="0.0.0.0" if isDocker else "127.0.0.1", root_path="/coursegpt")