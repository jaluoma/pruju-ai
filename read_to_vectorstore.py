import os 
import textract
import pandas as pd
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS

# Scan files from the course_material directory (or alternative)

material_directory = "course_material/"
dir_input = input(f"Default materials directory: {material_directory}\nPress enter to keep the same, or write the desired name to change: ")
if dir_input != '':
    material_directory = dir_input
filenames = []
for root, dirs, files in os.walk(material_directory):
    for name in files:
        # Exclude dot-files
        if name[0] != '.':
            filenames.append(os.path.join(root, name))

print("The following files will be processed:\n")
print(filenames)

# Make headings pretty based on file names
# '_' to ' ', remove file suffixes, title case, "/" to ": " 
 
material_headings = [filename[len(material_directory):] for filename in filenames]
def pretty_headings(heading):
    heading = heading.replace('_', ' ')
    heading = heading.split('.')[0]
    heading = heading.title()
    heading = heading.replace('/', ': ') 
    return heading
material_headings = [pretty_headings(heading) for heading in material_headings]

# Loop through suggested material headings and ask the user if they want to change it

for i, heading in enumerate(material_headings):
    # print(heading)
    user_input = input(f"Suggested heading: {heading}\nPress enter to keep the same, or write the desired name to change:")
    if user_input != '':
        material_headings[i] = user_input

print(material_headings)

# Extract text from the files
# Supported file formats: https://textract.readthedocs.io/en/stable/ + MarkDown
texts = []
for filename in filenames:
    # Exctract file type
    filetype = filename.split('.')[-1]
    print(filename)
    if filetype != "md":
        text = textract.process(filename)
        text = text.decode("utf-8")
    else:
        with open(filename) as f:
            text=f.read()
            f.close()

    texts.append(text)

# Create data frame

df = pd.DataFrame({'Heading': material_headings, 'Text': texts})

# Create chunks

from langchain.text_splitter import CharacterTextSplitter
text_splitter = CharacterTextSplitter(        
    separator = "\n\n",
    chunk_size = 500,
    chunk_overlap  = 100,
    length_function = len,
    is_separator_regex = False,
)

df['Text_Splitted'] = df['Text'].apply(text_splitter.split_text)


# Append Heading to the top of chunk

df['Text_Splitted_w_Headings'] = df.apply(lambda row: [row['Heading'] + '\n' + chunk for chunk in row['Text_Splitted']], axis=1)

# Create master chunk

master_chunk = []
for i, row in df.iterrows():
    master_chunk += row['Text_Splitted_w_Headings']

# Create vector store

embeddings = HuggingFaceInstructEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = FAISS.from_texts(master_chunk, embeddings)

# Try querying the vector store

query = input("Search the database: ")
docs = vector_store.similarity_search(query)
print(docs)

# Ask for the folder to save the database in

folder_figured_out = False
while folder_figured_out == False:
    folder = input("What folder would you like to save the database in? Default: course_material_vdb \n")
    if folder == "":
        folder = "course_material_vdb"
        folder_figured_out = True
    if not os.path.exists(folder):
        print(f"Folder {folder} does not exist. Do you want to create it?")
        create_folder = input("Y/n: ")
        if create_folder.lower() == "y":
            os.mkdir(folder)
            folder_figured_out = True
        elif create_folder.lower() == "":
            os.mkdir(folder)
            folder_figured_out = True

print(f"Saving database in {folder}")

# Save the vector store

vector_store.save_local(folder)
print("Save succcess!")

# Load the vector store for testing

loaded_vector_store = FAISS.load_local(folder, HuggingFaceInstructEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"))

# Try querying the vector store

query = input("Search the database: ")
docs = loaded_vector_store.similarity_search(query)
print(docs)


