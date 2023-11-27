# Script for initializing openai and azure chat models with langchain 

import os
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain.schema import AIMessage, SystemMessage, HumanMessage
from langchain.callbacks import get_openai_callback

from dotenv import load_dotenv 
load_dotenv("../.env")

messages = []
messages.append(SystemMessage(content="You are a helpful assistant that translates sentences from English to French."))
messages.append(HumanMessage(content="I love Git."))

if os.getenv("LLM_PROVIDER") == "openai":

    chat = ChatOpenAI(temperature=0,
                    model_name="gpt-4",)

    chat.default_headers= {"Authorization": "Bearer "+os.environ.get("OPENAI_API_KEY")}

    with get_openai_callback() as cb:
        results = chat(messages)
    print(cb)
    print(results)

else:
    import httpx

    # URL backend and authentication customization
    # https://github.com/openai/openai-python/issues/547#issuecomment-1795526894
    def update_base_url(request: httpx.Request) -> None:
        if os.getenv("AZURE_OPENAI_CUSTOM_BACKEND") is not None:
            if request.url.path == "/chat/completions":
                request.url = request.url.copy_with(path=os.getenv("AZURE_OPENAI_CUSTOM_BACKEND"))


    chat = ChatOpenAI(
                openai_api_base=os.getenv("MODEL_ENDPOINT"),
                model_name="gpt-4",
                temperature=0,
                default_headers = {
                    os.getenv("AZURE_OPENAI_CUSTOM_HEADER"): os.environ.get("OPENAI_API_KEY"),
                },
                http_client=httpx.Client(
                    event_hooks={
                        "request": [update_base_url],
                    }
                    ),
                )


    with get_openai_callback() as cb:
        results = chat(messages)
    print(cb)
    print(results)
