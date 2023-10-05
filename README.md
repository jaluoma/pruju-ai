# Introduction

Course-gpt is a course assistant app based on retrieval-augmented generation and large language models. It uses `gradio` to render the front end `langchain` to retrieve documents and communicate with the large language model. By default it uses Azure/OpenAI, but you should be able to change this to any chat model supported by langchain.

With the current setup it is available locally.

# Getting started

Clone the repo, create a virtual environment, and install required dependencies.

```bash
(.venv) foo@bar ~$: pip install -r requirements
```

You should create a .env file with contents something like this:

```
AZURE_OPENAI_KEY = "your-secret-key-goes-here"
AZURE_OPENAI_TEMPERATURE = "0"
CHAT_DATA_FOLDER ="syllabusgpt"
```

# Launch the app

Run:

```bash
(.venv) foo@bar ~$: gradio app.py
```

Once the app is running, it will tell you the address where you can find the chatbot interface.

# Course materials

The variable `CHAT_DATA_FOLDER` in the .env file tells the app where to look for the course materials. Please see `langchain` [FAISS](https://python.langchain.com/docs/integrations/vectorstores/faiss) documentation to see how to use your own course materials. In practice, the course materials are read into small text chunks that look something like this:

```
'Source: Week: 5 slides\n\nTechniques in Text Analytics\n\n- Text Preprocessing: Tokenization, stemming, etc.\x0b- Text Vectorization: Count vectorization, TF-IDF.\x0b- Sentiment Analysis: Determining the sentiment expressed in text.\n\n\nApplications in Business\n\n- Customer Feedback Analysis: Understanding customer sentiments.\x0b- Keyword Extraction: Identifying important topics in customer reviews.\x0b- Chatbot Training: Training intelligent chatbots to handle customer queries.\n\n\nSummary\n\n- We covered basic techniques in text analytics'
```

These are then processed using a text embeddings models and stored in a FAISS vector store. Something along the lines of:

```python
embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
knowledge_base = FAISS.from_texts(master_chunk, embeddings) # master_chunk is a list of strings

# Test performing a search:
query = input("Search the database: ")
docs = knowledge_base.similarity_search(query)
print(docs)

knowledge_base.save_local("faiss_local")
```