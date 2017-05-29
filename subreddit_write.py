import praw
import feedparser
import config
import bs4
import requests
import pathlib
import logging
logging.basicConfig(filename='',  format='%(asctime)s %(message)s',  datefmt='%m/%d/%Y %I:%M:%S %p',  level=logging.INFO)
lastModifiedFile = ''
##reddit##
reddit = praw.Reddit(client_id= config.CLIENT_ID, 
                     client_secret=config.CLIENT_SECRET,
                     user_agent=config.USER_AGENT,
                     username=config.USERNAME,
                     password=config.PASSWORD)
subs = reddit.subreddit(config.SUBREDDITS[0])

##check if entry was ever posted in the subredd##
def housekeep(entry_title):
    colon_index = entry_title.find(':')
    entry_id = entry_title[:colon_index]
    print('checking ' + entry_title + 'in the subreddit')
    for submission in subs.hot():
        thread_title = submission.title
        colon_index = thread_title.find(':')
        thread_id = thread_title[:colon_index]
        if(entry_id == thread_id):
            logging.info('found entry already in subreddit')
            print('found the entry already in the subreddit')
            return 1
    print("didn't find the entry, returning 0.")
    logging.info('found the entry, returning 0')
    return 0

##take a dict{title, url} and subreddit submit it as link##
def postToSub(entry):
    try:
        subs.submit(entry['title'],  url=entry['url'],  send_replies=False)
        return 1
    except:
        print('Error in posting ' + entry['title'])
        return None

##grab the last modified date from last check##
def readLastModified():
    path ='/home/hai/PythonWorkspace/openargs/lastModified.txt'
    pl = pathlib.Path(path)
    if not pl.is_file():
        open(path,  'a').close()
        print('created lastModified.txt because doesnt exist')
    else:
        with open(path,  'rb') as f:
            if f.read(1) == b'\n':
                return None
            f.seek(-2, 2)             # Jump to the second last byte.
            while f.read(1) != b"\n": # Until EOL is found...
                try:
                    f.seek(-2, 1)     # ...jump back the read byte plus one more.
                except IOError:
                    f.seek(-1, 1)
                    if f.tell() == 0:
                        break
            last = f.readline()       # Read last line.
            return last

##save the rss last modified date##
def saveLastModified(lastModifiedFile,  rss):
    with open( lastModifiedFile,  'r+') as f:
        f.write(rss.modified)
        logging.info('saving new lastModified: %s',  rss.modified)

def cdata_parse(html):
    soup = bs4.BeautifulSoup(html,  'html.parser')
    for tag in soup.find_all(True):
        tag.unwrap()
    return soup

def getSiteLink():
    dict = {}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36'}
    r = requests.get(config.SITE, headers=headers)
    rtext = (r.text)
    soup = bs4.BeautifulSoup(rtext,  'html.parser')
    articles = soup.find_all('article')
    dict['title'] = articles[0].h1.get_text()
    dict['url'] = articles[0].a.get('href')
    return dict


##main##
logging.info('starting openargs')
old_rss = readLastModified()
if not(old_rss):
    rss = feedparser.parse(config.RSS_SITE)
else:
    mod_decoded = old_rss.decode()
    rss = feedparser.parse(config.RSS_SITE,  modified=mod_decoded)

if not rss.status == '304':
    logging.info('not 304, housekeeping')
    entries = rss.entries
    if (len(entries)):
        if not (housekeep(entries[0].title)):
            postToSub(getSiteLink())
        saveLastModified(lastModifiedFile,  rss)
else:
    logging.info('304: No Updates')
    print('304 and no updates')
##end##
