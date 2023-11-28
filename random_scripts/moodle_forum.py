import os
import requests

from dotenv import load_dotenv
load_dotenv("../.moodle")

endpoint=os.getenv("WS_ENDPOINT")
courseid=os.getenv("COURSE_ID")
token=os.getenv("WS_TOKEN")

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
    print("Unable to figure out the forumid. Exiting")
    exit(1)

fn = "mod_forum_get_forum_discussions"

data = {
    "forumid": forumid, 
    "wstoken": token,
    "wsfunction": fn,
    "moodlewsrestformat": "json",
}

posts = []

response = requests.post(endpoint,data).json()
discussions = response.get('discussions',[])
for discussion in discussions:
    #print("Subject: "+discussion.get('subject',''))
    #print("Message: "+discussion.get('message',''))
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
        posts.append([subject,message,url, modified])

print(posts)

fn = "mod_forum_get_discussion_posts"

data = {
    "discussionid": discussion.get('discussion'), 
    "wstoken": token,
    "wsfunction": fn,
    "moodlewsrestformat": "json",
}

discussion_posts = requests.post(endpoint,data).json()
discussion_posts.get('posts')[0]['subject']
discussion_posts.get('posts')[0]['message']


fn="core_course_get_contents"

data = {
    "courseid": courseid, 
    "wstoken": token,
    "wsfunction": fn,
    "moodlewsrestformat": "json",
}

contents = requests.post(endpoint,data).json()
for content in contents:
    modules = content.get('modules',[])
    for module in modules:
        if module.get('name')=="Announcements" and module.get('modname')=="forum":
            announcements_url = module.get('url','')

print(announcements_url)        

#
#for module in modules:
#    if module.get('name')=="Announcements" and module.get('modname')=="forum":
#        

#print(announcements_url)
