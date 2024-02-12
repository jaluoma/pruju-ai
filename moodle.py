import os
import requests
import pandas as pd
from urllib.request import urlretrieve
from dotenv import load_dotenv
import argparse

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
    
def ws_return_announcements(endpoint=os.getenv("WS_ENDPOINT"), courseid=os.getenv("COURSE_ID"), token=os.getenv("WS_TOKEN")):
    
    posts = pd.DataFrame(columns=['Subject', 'URL', 'Message', 'Modified'])
    
    fn = "mod_forum_get_forums_by_courses"

    data = {
        "courseids[0]": courseid, 
        "wstoken": token,
        "wsfunction": fn,
        "moodlewsrestformat": "json",
    }

    forumid = 0
    forums = requests.post(endpoint,data).json()
    for forum in forums:
        if (forum.get('type')=="news"):
            forumid=forum.get('id')

    if forumid==0:
        print("Unable to find forums. Returning None.")
        return None

    fn = "mod_forum_get_forum_discussions"

    data = {
        "forumid": forumid, 
        "wstoken": token,
        "wsfunction": fn,
        "moodlewsrestformat": "json",
    }

    response = requests.post(endpoint,data).json()
    discussions = response.get('discussions',[])
    for discussion in discussions:
        fn = "mod_forum_get_discussion_posts"
        data = {
            "discussionid": discussion.get('discussion'), 
            "wstoken": token,
            "wsfunction": fn,
            "moodlewsrestformat": "json",
        }
        discussion_posts = requests.post(endpoint,data).json().get('posts',[])
        for post in discussion_posts:
            subject=post['subject']
            message=post['message']
            url=post['urls']['view']
            modified=post['timemodified']
            posts.loc[len(posts)]=[subject,url,message, modified]

    return(posts)

def ws_create_file_list(response: requests.Response, token=os.getenv("WS_TOKEN")):
    """Create file list from Moodle Webservice core_course_get_contents response.
    
    This function create a file list from Moodle Webservice API response object.

    Args:
        response (requests.Response): requests.Response object based on ws_fn_call(..., fn="core_course_get_contents")

    Returns:
        pandas DataFrame
    """
    # Initialize dataframe for metadata
    file_data = pd.DataFrame(columns=['Filename','User URL','Download URL', 'Modified'])

    response=response.json()
    for section in response:
        for module in section.get('modules', []):
            if module.get('modplural','')=='Files' or module.get('modplural','')=='Folders':
                module_name = module.get('name','')
                module_url = module.get('url','')          
                for content in module.get('contents', []):
                    item_name = module_name+"->"+content.get('filename','')
                    file_data.loc[len(file_data)] = [item_name,module_url,content.get('fileurl', '')+"&token="+token, content.get('timemodified', '')]
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
    parser=argparse.ArgumentParser(description="Ingest a Moodle course into a vector store.")
    parser.add_argument('-p','--posts',action='store_true',help="Process forum posts",required=False, default=False)
    parser.add_argument('-f','--file',help="Dot file that contains the configuration",required=False, default=".moodle")
    dotfile = parser.parse_args().file
    print("Dot file: " + dotfile)
    load_dotenv(dotfile)
    resp=ws_fn_call(endpoint=os.getenv("WS_ENDPOINT"), courseid=os.getenv("COURSE_ID"), token=os.getenv("WS_TOKEN"), fn="core_course_get_contents")
    df=ws_create_file_list(resp, token=os.getenv("WS_TOKEN"))
    ws_files_todisk(df, save_location=os.getenv("WS_STORAGE"))
    if parser.parse_args().posts:
        posts=ws_return_announcements(endpoint=os.getenv("WS_ENDPOINT"), courseid=os.getenv("COURSE_ID"), token=os.getenv("WS_TOKEN"))
        if len(posts)==0:
            posts=None
    else:
        posts=None

    # Remove unsupported file types
    from textract.parsers import _get_available_extensions as get_available_extensions
    supported_types = get_available_extensions()
    df = df[df['Filename'].str.split('.').str[-1].isin(supported_types)]
    # Ignore files that are listed in IGNORE_SUFFIXES environment variable
    if os.getenv("IGNORE_SUFFIXES") is not None:
        ignore_suffixes = os.getenv("IGNORE_SUFFIXES").split(',')
        df = df[~df['Filename'].str.split('.').str[-1].isin(ignore_suffixes)]
    df = df.reset_index(drop=True)    

    filenames = []
    for file in df['Filename']:
        file = os.getenv("WS_STORAGE")+"/"+file
        filenames.append(file)
    
    from read_to_vectorstore import convert_files_totext, create_chunck_dataframe, create_vector_store
    texts = convert_files_totext(filenames)

    material_headings = df['Filename'] + ", " + df['User URL']
    material_headings = material_headings.tolist()

    chunk_df = create_chunck_dataframe(material_headings, texts)
    chunk_df['Modified'] = df['Modified']
    
    if posts is not None:
        post_headings = "Announcements->" + posts['Subject'] + ", " + posts['URL']
        post_chunk_df = create_chunck_dataframe(post_headings,posts['Message'])
        post_chunk_df['Modified'] = posts['Modified']
        chunk_df = pd.concat([chunk_df,post_chunk_df],ignore_index=True)

    vector_store_type=os.getenv("VECTOR_STORE")
    if vector_store_type=="qdrant":
        vector_store=create_vector_store(chunk_df,
                                store_type="qdrant",
                                metadatas=True,
                                vector_store_endpoint=os.getenv("VECTOR_STORE_ENDPOINT"),
                                vector_store_api_key=os.getenv("VECTOR_STORE_API_KEY"), 
                                vector_store_collection_name=os.getenv("VECTOR_STORE_COLLECTION"))
    else:
        vector_store = create_vector_store(chunk_df,store_type="faiss", metadatas=True)
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

