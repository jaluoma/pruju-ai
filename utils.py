import tiktoken

# Define functions for memory management

def purge_memory(messages, model_name, max_tokens: int):

    token_count = token_counter(messages, model_name)
    if (len(messages)>1):
        while (token_count>max_tokens):
            # Print purged message for testing purposes
            # print("Purged the following message:\n" + messages[1].content)
            messages.pop(1)
            token_count = token_counter(messages)
    return

def token_counter(messages, model_name):
    # print("Counting tokens based on: " + current_model)
    if model_name == "gpt-4":
        encoding = tiktoken.encoding_for_model("gpt-4")
    else:
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    concatenated_content = ''.join([message.content for message in messages])
    token_count = len(encoding.encode(concatenated_content))
    return token_count