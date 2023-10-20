from dotenv import load_dotenv
load_dotenv()

import gradio as gr
from chat_caller import query_gpt_chat
import os

from aaltotheming import aaltobluetheme

def courseGPT(query, chat_history):
    print("Chat history :" + str(chat_history))
    max_tokens = 2000 # not used?
    # unpack history - consider moving to chat_caller.py
    chat_history_unpacked = []
    for x in chat_history:
        for y in x:
            chat_history_unpacked.append(y)
    #answer = query_gpt_chat(query,chat_history_unpacked,max_tokens)
    answer = "You said: "+query
    chat_history.append((query, answer))
    return "", chat_history
    #return(query_gpt_chat(query,chat_history_unpacked,max_tokens))

# layout, examples, chat_header, theme = unpack_resources(os.getenv("CHAT_DATA_FOLDER"))
# initialize_layout(layout) 

with open(os.getenv("CHAT_DATA_FOLDER")+'/examples_ui.txt', 'r') as file: 
    examples = file.readlines()
examples = [example.strip() for example in examples]

with open(os.getenv("CHAT_DATA_FOLDER")+'/chat_description.txt', 'r') as file: 
    chat_description = file.read().strip()

chat_description=chat_description.strip()

with open(os.getenv("CHAT_DATA_FOLDER")+'/chat_header.md', 'r') as file: 
    chat_header = file.read().strip()

with open(os.getenv("CHAT_DATA_FOLDER")+'/chat_name.txt', 'r') as file: 
    chat_name = file.read().strip()

footer="![Aalto University Logo]("+os.getenv("CHAT_DATA_FOLDER")+'/aalto_logo.png)'
print(footer)

footer="![Aalto University Logo](aalto_logo.png)"

with gr.Blocks(theme=aaltobluetheme,
               analytics_enabled=False,
               title = "CourseGPT",
               ) as demo:
    gr.Markdown(value=chat_header)
    chatbot = gr.Chatbot(label="CourseGPT",scale=10,show_label=False,
                         bubble_full_width=False,
                         show_copy_button=True)
    with gr.Group():
        with gr.Row():
            query = gr.Textbox(show_label=False,
                                placeholder="Your question.",
                                scale=10,
                                container=False,autofocus=True)
            submit_button = gr.Button(value="Go!",scale=1,variant="primary",min_width=10)
    with gr.Row():
        model_choice = gr.Dropdown(choices = [("gpt-3.5-turbo",0), ("gpt-4",1)], 
            label = "Model choice: ",
            show_label=False, scale=10,
            value=0,
            interactive=True,
            container=True)
        clear = gr.ClearButton([query, chatbot],value="🗑️ Clear history",scale=1)
    #gr.Markdown(footer) # does not work
    gr.Examples(examples=examples,inputs=query)  



    # def respond(message, chat_history):
    #     bot_message = random.choice(["How are you?", "I love you", "I'm very hungry"])
    #     chat_history.append((message, bot_message))
    #     time.sleep(2)
    #     print("Message: " + message)
    #     print("History: " + str(chat_history))
    #     return "", chat_history

    query.submit(fn=courseGPT, inputs=[query, chatbot], outputs=[query, chatbot])
    submit_button.click(fn=courseGPT, inputs=[query, chatbot], outputs=[query, chatbot])

# demo = gr.ChatInterface(fn=courseGPT, 
#                         analytics_enabled=False, 
#                         examples = examples,
#                         theme=aaltobluetheme,
#                         title=chat_name,
#                         description=chat_description,
#                         undo_btn="Undo",
#                         retry_btn="Retry",
#                         clear_btn="Clear")

if __name__ == "__main__":
    print("Launching Demo\n")
    server_name = "127.0.0.1"
    isDocker = os.path.exists("/.dockerenv")
    print(f"Docker: {isDocker}\n")
    demo.launch(server_name="0.0.0.0" if isDocker else "127.0.0.1", 
                root_path="/coursegpt",show_api=False,
                favicon_path=os.getenv("CHAT_DATA_FOLDER")+"/favicon.ico")