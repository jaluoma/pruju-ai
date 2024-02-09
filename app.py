from dotenv import load_dotenv
load_dotenv()

import gradio as gr
from chat_caller import query_gpt_chat, check_quota_status, choose_model, write_log_removal_request, log_vote
from chat_utils import read_course_assets
import os

from brand_theming import customtheme

import uuid

def try_admin_token(request):
    try:
        admin_token = request.query_params['admin_token']
    except:
        admin_token = None
    return admin_token

def call_chat(query, chat_history, prompt_logging_enabled, conversation_id, request: gr.Request):
    if len(chat_history) == 0:
        conversation_id = str(uuid.uuid4()) if os.getenv("ENABLE_CONVERSATION_ID") is not None else "N/A"
    
    # Try to read admin token
    admin_token=try_admin_token(request)
    # unpack history
    # print(admin_token)
    chat_history_unpacked = []
    for x in chat_history:
        for y in x:
            chat_history_unpacked.append(y)
    chat_engine, answer = query_gpt_chat(query,chat_history_unpacked, prompt_logging_enabled, conversation_id, admin_token)
    chat_history.append((query, answer))
    return "", chat_history, conversation_id

def log_removal_request(conversation_id, request: gr.Request):
    # Try to read admin token
    admin_token=try_admin_token(request)
    write_log_removal_request(conversation_id, admin_token)
    return "", [], str(uuid.uuid4())

def log_removal_success():
    return [("Please remove any stored prompts from this conversation.",
             "Your request has been logged. You can safely close this window or continue chatting. Please remember to untick the prompt logging checkbox if you do not want us to save your prompts.")]

def vote(data: gr.LikeData, conversation_id, prompt_logging_enabled, request: gr.Request) -> None:
    admin_token=try_admin_token(request)
    log_vote(data.liked, data.value, conversation_id, prompt_logging_enabled, admin_token)
    #print(data)
    #print(prompt_logging_enabled)
    #print(conversation_id)

# with gr.Blocks() as demo:
with gr.Blocks(theme=customtheme, 
               analytics_enabled=False, 
               title = "Pruju AI") as demo:
    conversation_id = gr.State()
    
    examples, chat_header, chat_footer = read_course_assets()
    
    gr.Markdown(value=chat_header)
    chatbot = gr.Chatbot(label="Model: " + choose_model(check_quota_status()),
                         scale=10,show_label=True,
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
    # Prompt logging
    enable_logging_prompts = os.getenv("ENABLE_LOGGING_PROMPTS")
    if enable_logging_prompts is not None:
        enable_logging_prompts = True if int(os.getenv("ENABLE_LOGGING_PROMPTS"))==1 else False
    prompt_logging_enabled=gr.Checkbox(value=False,
                                        label="Allow prompt logging",
                                        visible=enable_logging_prompts,
                                        container=False,
                                        scale=40)
    enable_liking = os.getenv("ENABLE_LIKING")
    if enable_liking is not None:
        enable_liking = True if int(os.getenv("ENABLE_LIKING"))==1 else False
    if enable_liking:
        chatbot.like(vote, inputs=[conversation_id,prompt_logging_enabled], outputs=None)  
    gr.Markdown(value=chat_footer)  
    if len(examples)>0:
        gr.Examples(examples=examples,inputs=query)
    if enable_logging_prompts:
        regret=gr.Button(value="Click here to request a removal of any stored prompts from this conversation.",
                         variant="secondary",size="sm")
    query.submit(fn=call_chat, inputs=[query, chatbot, prompt_logging_enabled, conversation_id], outputs=[query, chatbot, conversation_id],
                 concurrency_limit=int(os.getenv("MAX_CONCURRENCY")))
    submit_button.click(fn=call_chat, inputs=[query, chatbot, prompt_logging_enabled, conversation_id], outputs=[query, chatbot, conversation_id],
                        concurrency_limit=int(os.getenv("MAX_CONCURRENCY")))
    if enable_logging_prompts:
        regret.click(fn=log_removal_request, inputs=[conversation_id], outputs=[query, chatbot, conversation_id]).success(log_removal_success,inputs=None,outputs=[chatbot])

if __name__ == "__main__":
    print("Launching Demo\n")
    server_name = "127.0.0.1"
    isDocker = os.path.exists("/.dockerenv")
    print(f"Docker: {isDocker}\n")
    
    demo.queue(#concurrency_count=int(os.getenv("MAX_CONCURRENCY")),
               max_size=int(os.getenv("MAX_QUEUE")))
    demo.launch(server_name="0.0.0.0" if isDocker else "127.0.0.1", 
                root_path=os.getenv("ROOT_PATH"),show_api=False,
                favicon_path=os.getenv("CHAT_DATA_FOLDER")+"/favicon.ico")