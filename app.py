from dotenv import load_dotenv
load_dotenv()

import gradio as gr
from chat_caller import query_gpt_chat, check_quota_status, choose_model
from chat_utils import read_course_assets
import os

from brand_theming import customtheme

def courseGPT(query, chat_history):
    max_tokens = 0 # deprecated
    # unpack history - consider moving to chat_caller.py
    chat_history_unpacked = []
    for x in chat_history:
        for y in x:
            chat_history_unpacked.append(y)
    chat_engine, answer = query_gpt_chat(query,chat_history_unpacked,max_tokens)
    chat_history.append((query, answer))
    return "", chat_history

def update_model_status():
    model = choose_model(check_quota_status())
    # print(model)
    return "Model: " + model

# with gr.Blocks() as demo:
with gr.Blocks(theme=customtheme, 
               analytics_enabled=False, 
               title = "Pruju AI") as demo:
    
    examples, chat_header, chat_footer = read_course_assets()
    
    gr.Markdown(value=chat_header)
    model_md = gr.Markdown("Model: " + choose_model(check_quota_status()))
    chatbot = gr.Chatbot(label="pruju_ai",scale=10,show_label=True,
                         bubble_full_width=False,
                         show_copy_button=True)
    with gr.Group():
        with gr.Row():
            query = gr.Textbox(show_label=False,
                                placeholder="Your question.",
                                scale=40,
                                container=False,autofocus=True)
            clear = gr.ClearButton([query, chatbot],value="🗑️",scale=1,min_width=10,variant='secondary')
            submit_button = gr.Button(value="Go!",scale=6,variant="primary",min_width=10)

    gr.Markdown(value=chat_footer)  
    gr.Examples(examples=examples,inputs=query)
    query.submit(fn=courseGPT, inputs=[query, chatbot], outputs=[query, chatbot]).success(update_model_status, None, model_md, queue=False)
    submit_button.click(fn=courseGPT, inputs=[query, chatbot], outputs=[query, chatbot]).success(update_model_status, None, model_md, queue=False)

if __name__ == "__main__":
    print("Launching Demo\n")
    server_name = "127.0.0.1"
    isDocker = os.path.exists("/.dockerenv")
    print(f"Docker: {isDocker}\n")
    demo.queue(max_size=1)
    demo.launch(server_name="0.0.0.0" if isDocker else "127.0.0.1", 
                root_path="/pruju_ai",show_api=False,
                favicon_path=os.getenv("CHAT_DATA_FOLDER")+"/favicon.ico")