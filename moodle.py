import os
import requests
import pandas as pd
from urllib.request import urlretrieve
from dotenv import load_dotenv
load_dotenv(".moodle")

def ws_fn_call(endpoint=os.getenv("WS_ENDPOINT"), courseid=os.getenv("COURSE_ID"), token=os.getenv("WS_TOKEN"), fn="core_course_get_contents"):
    """Run a Moodle Webservice API call.
    
    This function allows simple API calls via the Webservice API.

    Args:
        endpoint (str): The Moodle instance endpoint. Defaults to WS_ENDPOINT environment variable.
        courseid (str): The courseID. Defaults to COURSE_ID environment variable.
        token (str): The wstoken. Defaults to WS_TOKEN environment variable.
        fn (str): Name of Webservice API function. Defaults to core_course_get_contents.

    Returns:
        requests.Response object

    Raises:
        Exception with status code and response text.
    """
    data = {
        "courseid": courseid,
        "wstoken": token,
        "wsfunction": fn,
        "moodlewsrestformat": "json",
    }

    # HTTP request
    response = requests.post(endpoint,data)
    if response.status_code==200:
        return response
    else:
        raise Exception(f"Request failed with status code: {response.status_code}: {response.text}")

def ws_create_file_list(response: requests.Response, token=os.getenv("WS_TOKEN")):
    """Create file list from Moodle Webservice core_course_get_contents response.
    
    This function create a file list from Moodle Webservice API response object.

    Args:
        response (requests.Response): requests.Response object based on ws_fn_call(..., fn="core_course_get_contents")

    Returns:
        pandas DataFrame
    """
    # Initialize dataframe for metadata
    file_data = pd.DataFrame(columns=['Filename','User URL','Download URL'])

    response=response.json()
    for section in response:
        for module in section.get('modules', []):
            if module.get('modplural','')=='Files' or module.get('modplural','')=='Folders':
                module_name = module.get('name','')
                module_url = module.get('url','')          
                for content in module.get('contents', []):
                    item_name = module_name+"->"+content.get('filename','')
                    file_data.loc[len(file_data)] = [item_name,module_url,content.get('fileurl', '')+"&token="+token]

    return file_data


def ws_files_todisk(df: pd.DataFrame, save_location=os.getenv("WS_STORAGE")):
    """Save Moodle files to disk.
    
    This function downloads files based on a file list and saves them to disk.

    Args:
        df (pandas.DataFrame): pandas.DataFrame object that contains a list of files to be saved
        save_location (str): The directory to save the files. Defaults to WS_STORAGE environment variable.

    Returns:
        boolean: Whether the save was successful or not.
    """
    save_dir = save_location
    if save_dir is None:
        print("No save folder determined. Exiting.")
        return False
    if os.path.isdir(save_dir)==False:
        os.mkdir(save_dir)

    for index, row in df.iterrows():
        urlretrieve(row['Download URL'],save_location+"/"+row['Filename'])

    return True

if __name__=="__main__":
    resp=ws_fn_call()
    df=ws_create_file_list(resp)
    ws_files_todisk(df)

    filenames = []
    for file in df['Filename']:
        file = os.getenv("WS_STORAGE")+"/"+file
        filenames.append(file)
    
    from read_to_vectorstore import convert_files_totext, create_chunck_dataframe, create_vector_store
    texts = convert_files_totext(filenames)

    material_headings = df['Filename'] + ", " + df['User URL']
    material_headings = material_headings.tolist()

    chunk_df = create_chunck_dataframe(material_headings, texts)
    vector_store = create_vector_store(chunk_df,store_type="faiss")

    vector_store_dir = os.getenv("WS_STORAGE")+"_vdb"
    if os.path.isdir(vector_store_dir)==False:
        os.mkdir(vector_store_dir)    

    vector_store.save_local(vector_store_dir)

    print("Test querying the vector store.")
    try:
        query = input("Search the database: ")
        docs = vector_store.similarity_search(query)
        print("Results of test query: ")
        print(docs)
    except Exception as e:
        print(f"An error occurred when performing a query: {e}")
        exit(1)

