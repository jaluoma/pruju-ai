# Introduction

Pruju AI is a teaching assistant that allows students to interact with the teacher's course materials. The assistant is designed to answer any student question, but _only if_ the answer can be found in the course materials provided by the teacher (e.g., syllabus, slides, lecture transcripts). The assistant can also be guided to answer in ways that align with the course’s pedagogical objectives. For example, the assistant can be told to _not_ answer certain questions or to answer in a particular way.

The project exists to make creating virtual teaching assistants as easy as possible. From a pedagogical point of view, it is essential to be able to control the knowledge base of the assistant as well as the types of answers that the assistant provides to the student's questions.

The app can be configured to work with the teacher's own materials without any coding. You do need to modify some text files and run one Python script to make it your own. You can also use the code as a starting point for more sophisticated and customized setups. If your course uses Moodle, you can now import data from your own course!

The app works with OpenAI's API, Microsoft's Azure OpenAI Service and Ollama. Ollama supports a wider range of open-source models (e.g., Mistral 7B, Llama 2). Only Mistral 7B has been tested.

_Pruju is Finnish university slang for a study handout. According to the (Finnish) [Urban Dictionary](https://urbaanisanakirja.com/word/pruju/), prujus "can range in quality from a good book [...] to a pile of cryptic lecture slides that make no sense whatsoever."_

# Getting started

The instructions are for macOS but should work with Linux and (with small modifications) Windows, too.

Clone the repo and create a virtual environment for the project. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Create and edit .env

You should create a .env file that contains at least the following:

```
# Specify LLM provider and model
LLM_PROVIDER="openai"
MODEL_NAME="gpt-4"
# Directory for your course data:
CHAT_DATA_FOLDER ="prujuai_resources" 
# Total model call quota:
TOTAL_MODEL_QUOTA=5
# Max number of tokens per call
MAX_PROMPT_TOKENS=2000
# Capacity management:
MAX_CONCURRENCY=2
MAX_QUEUE=10
```

## LLM-provider specific environment variables

You can currently choose between "openai" (OpenAI's own API), "azure" (Microsoft's Azure OpenAI Service), or "ollama" (Ollama).

If you choose openai, you must define the API key:

```
LLM_PROVIDER="openai"
MODEL_NAME="gpt-4"
OPENAI_API_KEY="your-secret-key-goes-here"
```

If you choose azure, you must define the API endpoint and API key:

```
LLM_PROVIDER="azure"
MODEL_NAME="gpt-4"
OPENAI_API_KEY = "your-secret-key-goes-here" 
MODEL_ENDPOINT="https://your-azure-endpoint"
# Optionally, you can define:
AZURE_OPENAI_CUSTOM_BACKEND = "/custom/url/back/end/other/than/chat/completions"
AZURE_OPENAI_CUSTOM_HEADER="Some-Custom-Authentication-Header"
```

If you choose ollama, you need to define the model to be used.

```
LLM_PROVIDER="ollama"
MODEL_NAME="mistral"
```

In the case of Ollama, you need to  install Ollama and run `ollama serve <modelname>` to serve the model to `127.0.0.1:11434`. Only Mistral 7B has been tested so far. The basic functionality works, but is not extensively tested.

# Launch the app

Run:

```bash
gradio app.py
```

Once the app is running, it will tell you the address where you can find the chatbot interface.

# Bring your own course materials

## The basics

To get started, create a copy of the `prujuai_resources` directory and give it a name that you like (e.g., `mycourse_resources`) Then modify the .env file so that the app knows where to look for the files (e.g. `CHAT_DATA_FOLDER="mycourse_resources"`). In this new directory, modify the following files to your liking:

- `prompt_template.txt` provides the general system instructions for the chatbot
- `examples_ui.txt` defines the examples that help the user start asking useful questions
- `favicon.ico` is the icon of the app
- `chat_header.md` provides a modifiable description of your app that is displayed above the chat interface
- `chat_footer.md` as above, but below the chat interface

To read your own materials to a vector store, you should run:

```bash
python3 read_to_vectorstore.py
```

The script will read your course materials from a given location (`./course_material` by default) and store them to a [FAISS](https://python.langchain.com/docs/integrations/vectorstores/faiss) vector store (by default `./course_material_vdb`). Once you are done, move the `index.faiss` and `index.pkl` files to `CHAT_DATA_FOLDER/faiss_index`. If you want more options, such as running the script in non-interactive mode with sensible defaults, run the script with -h:

```bash
python3 read_to_vectorstore.py -h
```

The default course materials are from an imaginary course called _Primer on Business Analytics with Python_, produced with the help of ChatGPT (GPT-4) for demonstration purposes. The example materials (`course_materials`) include lecture slides, lecture transcripts and Python scripting tutorials.

## Moodle integration

_Please think carefully what data you (don't) want your app to have access to!_ 

You can import the materials from a Moodle instance. Create a file called `.moodle` and modify it to contain the following things:

```
COURSE_ID="12345"
WS_TOKEN="your-token"
WS_ENDPOINT="https://your-moodle-instance.edu/webservice/rest/server.php"
WS_STORAGE="moodle_data"
```
Running the `moodle.py` script will download files (from _File_ and _Folder_ resources) from your course, as well as posts from the _Announcements_ forum. The script will by default embed the contents in a FAISS vector store in a directory specified in the `WS_STORAGE` environment variable, followed by "`_vdb`" (e.g., `moode_data_vdb`).

```bash
python3 moodle.py
```

You can then copy the `index.faiss` and `index.pkl` files to your course material folder (`CHAT_DATA_FOLDER/faiss_index`). The script also includes Moodle links to the text chucks consumed by the vector store, so it's advisable to add something like this to the system prompt: `Make sure to include hyperlinks to allow easy access to the materials.` This allows the user to click on the links and see the contents of the original concent on Moodle. Make sure that the access token is associated with the appropriate permissions on the Moodle end.

## Qdrant vector database

You can also use a [qdrant](https://qdrant.tech/) vector database, run locally in a container or using the hosted service. You can specify the app to use your qdrant collection by modifying .env as follows:

```
VECTOR_STORE="qdrant" # If you use qdrant
VECTOR_STORE_COLLECTION="my_collection" # qdrant collection name
VECTOR_STORE_ENDPOINT="localhost" #"localhost" or hosted service endpoint
VECTOR_STORE_API_KEY="your-secret" # If you use qdrant's hosted service
```

If you're importing your course materials from Moodle using `moodle.py`, add the above lines to your `.moodle` too. You can consider running the Moodle import script periodically to keep the chatbot's knowledge base up-to-date. Again, be mindful of premissions on the Moodle end.

# Project status

The project is currently in a working demo state, with loads of room for improvement. Some possible directions for further development: 

- _New features_: Alternative assistance modes (e.g., simple Q&A, prepping for exam, reflective discussions), a user interface for no-code chatbot customization à la OpenAI's GPT Builder.
- _Technical improvements_: The app has not been tested or optimized for large use volumes.
- _Support for alternative LLMs_: The app was originally designed to run with OpenAI's ChatGPT, but because the app uses lanchain to make the API calls, it can be integrated with many other LLMs with relative ease.
- _(Better) integration with Moodle and other platforms_: For example, using Google Drive, OneDrive, Dropbox for files would be convenient.

# Acknowledgements

[Enrico Glerean](https://github.com/eglerean) provided invaluable advice on many aspects of the project. [Thomas Pfau](https://github.com/tpfau) contributed code and provided many crucial technical insights along the way.