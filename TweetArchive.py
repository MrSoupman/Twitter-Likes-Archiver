from genericpath import exists
import time
from typing import List
from urllib import response
import tweepy
import sys
from bs4 import BeautifulSoup
import os
import requests
import youtube_dl
import shutil
import traceback
# global vars
cwd = os.getcwd()
templateDir = os.path.join(cwd, "template")
archiveDir = os.path.join(cwd, "archive")
tweetsDir = os.path.join(archiveDir, "tweets")
resDir = os.path.join(cwd, archiveDir, "res")
profileDir = os.path.join(resDir, "profile")
mediaDir = os.path.join(resDir, "media")
req = requests.Session()

class TweetAuthor:
    def __init__(self, AuthorID, AuthorName, AuthorUsername, AuthorPicture):
        self.AuthorID = AuthorID
        self.AuthorName = AuthorName
        self.AuthorUsername = AuthorUsername
        self.AuthorPicture = AuthorPicture

class Tweet:
    def __init__(self, TweetID, TweetText, TweetDate):
        self.TweetID = TweetID
        self.TweetText = TweetText
        self.TweetDate = TweetDate

def CreateAuth():
    key = ""
    try:
        with open("key.txt","r") as f:
            key = f.readline()
    except:
        print("Error occurred attempting to read key file.")
        exit()
    # probably should create an error if something goes wrong here
    return tweepy.Client(key, wait_on_rate_limit=True)

def CreateArchive(tweet: Tweet, tweetAuthor: TweetAuthor, media: List):
    template = ""
    attachmentBody = ""

    # Download all media inc pfp    
    if len(media) > 0:
        mediaIDDir = os.path.join(mediaDir,tweet.TweetID)
        if not os.path.exists(mediaIDDir):
            os.mkdir(mediaIDDir)
        count = 1
        for attachment in media:
            attachmentName = attachment[attachment.rfind('/')+1:]
            attachmentName = str(count).rjust(4,'0') + '-' + attachmentName
            if attachment != 'video':
                pic = req.get(attachment)
                try:
                    with open(os.path.join(mediaIDDir,attachmentName), 'wb') as f:
                        f.write(pic.content)
                    attachmentBody += "<img src=../../res/media/" + tweet.TweetID + "/" + attachmentName + "/>"
                except:
                    print("Error downloading/saving " + attachment)
                    traceback.print_exc()
            else:
                with youtube_dl.YoutubeDL({'outtmpl': os.path.join(mediaIDDir,attachmentName + ".webm")}) as ydl:
                    ydl.download(["https://twitter.com/twitter/status/" + tweet.TweetID]) # we dont have the direct video link, use tweet link instead
                    attachmentBody += "<video controls=\"controls\"" + " src="
                    attachmentBody += "../../res/media/" + tweet.TweetID + "/" + attachmentName + ".webm" 
                    attachmentBody += "></video><br>"
            count += 1
    

    #DL profile picture if it doesn't already exist
    pfpName = tweetAuthor.AuthorPicture
    pfpName = pfpName[pfpName.rfind('/')+1:]
    pfpPath = os.path.join(profileDir,tweetAuthor.AuthorID,pfpName)
    if not os.path.exists(pfpPath):
        pfp = req.get(tweetAuthor.AuthorPicture)
        if not os.path.exists(os.path.join(profileDir,tweetAuthor.AuthorID)):
            os.mkdir(os.path.join(profileDir,tweetAuthor.AuthorID))
        try:
            open(pfpPath, 'wb').write(pfp.content)
        except:
            print("Error saving profile picture")
    #DL media

    # read the template file
    with open(os.path.join(templateDir,"template.html")) as fp:
        template = BeautifulSoup(fp, 'html.parser')
        
    # replace all placeholders
    # replace pfp
    template.find(id="pfp")['src'] = "file://" + pfpPath
    
    # replace display and username
    template.find(id="DisplayName").string = tweetAuthor.AuthorName
    template.find(id="Username").string = "@" + tweetAuthor.AuthorUsername

    # replace body
    body = BeautifulSoup("<p>" + tweet.TweetText + "</p>" + attachmentBody + "<br>" + tweet.TweetDate, 'html.parser')

    content = template.find('div', attrs={"class":"content"})
    content.clear()
    content.append(body)
    
    # write completed template
    if not os.path.exists(os.path.join(tweetsDir, tweetAuthor.AuthorID)):
        os.mkdir(os.path.join(tweetsDir, tweetAuthor.AuthorID))
    finalTweetDir = os.path.join(tweetsDir, tweetAuthor.AuthorID, tweet.TweetID + ".html")
    with open(finalTweetDir,'x',encoding="utf-8") as f:
        f.write(str(template))

    # insert into metadata
    if not os.path.exists("archive/index.html"):
        shutil.copy("template/index.html", "archive/index.html")
    with open("archive/index.html","r+",encoding="utf-8") as f:
        homePg = BeautifulSoup(f, 'html.parser')
        li_new_tag = homePg.new_tag('li')
        li_new_tag.string = "<a href=" + "\"" + "tweets/" + tweetAuthor.AuthorID + "/" + tweet.TweetID + ".html" + "\"" + ">" + tweetAuthor.AuthorUsername + " - " + tweet.TweetText[:15] + "</a>"
        tags = homePg.ul
        tags.append(li_new_tag)
        #tags.insert(1, li_new_tag)
        f.seek(0)
        f.write(homePg.prettify(formatter=None))
        f.truncate()


def PrepTweet(tweetID, api):
    tweet = api.get_tweet(id=tweetID,
        tweet_fields=["id","text","attachments","author_id","created_at"],
        media_fields=["media_key","type","url","alt_text"],
        user_fields=["id","name","username", "profile_image_url"],
        expansions=["attachments.media_keys","author_id"]
        )
    ArchiveTweet(tweet)

def ArchiveTweet(tweet, media=None, author=None):
    # Core stuff
    if media == None:
        media = {m["media_key"]: m for m in tweet.includes['media']}
    if author == None:
        author = tweet.includes['users'][0].data # for now, only saving singular user
    
    data = tweet.data
    attachments = None
    media_keys = None

    if 'attachments' in data:
        attachments = data['attachments']  
        media_keys = attachments['media_keys']
    # info about the tweet
    twtTweet = Tweet(str(data['id']), data['text'], str(data['created_at']))
    # info about the author
    twtAuthor = TweetAuthor(str(data['author_id']),author['name'], author['username'], author['profile_image_url'])

    #info about any media
    lstMedia = []
    if media_keys != None:
        for key in media_keys:
            if media[key].url:
                lstMedia.append(media[key].url)
            elif media[key].type == 'video': # twitterv2 api does not support direct video links yet
                lstMedia.append("video")

    CreateArchive(twtTweet, twtAuthor, lstMedia)

def ArchiveLiked(user_name, api: tweepy.Client):
    pagination = None
    user = api.get_user(username=user_name).data
    while True:
        try:
            tweets = api.get_liked_tweets(id=user.id, max_results=5,
                tweet_fields=["id","text","attachments","author_id","created_at"],  
                media_fields=["media_key","type","url","alt_text"],
                user_fields=["id","name","username", "profile_image_url"],
                expansions=["attachments.media_keys","author_id"],
                pagination_token=pagination)
            media = {m["media_key"]: m for m in tweets.includes['media']}
            users = {u['id']: u for u in tweets.includes['users']}
            for i in range(0, len(tweets.data)):
                if not os.path.exists("archive/tweets/" + str(tweets.data[i]['id'])):
                    ArchiveTweet(tweets.data[i], media, users[tweets.data[i].author_id])
                else:
                    print("Tweet already exists: " + tweets.data[i]['id'])
            if 'next_token' in tweets.meta:
                pagination = tweets.meta['next_token']
            else:
                break
        except tweepy.errors.TooManyRequests:
            print("Call limit reached, waiting 15 min...")
            time.sleep(60 * 15)
    

if __name__ == '__main__':
    # initial sanity check
    if not os.path.exists(templateDir):
        print("Error, please extract the template folder as well.")
        input()
        exit()
    if(len(sys.argv) == 1):
        print("Error, please include either a username or a link to a tweet.")
        input()
        exit()

    # checking if all folders are here
    if not os.path.exists(archiveDir):
        os.mkdir(archiveDir)
    if not os.path.exists(tweetsDir):
        os.mkdir(tweetsDir)
    if not os.path.exists(resDir):
        os.mkdir(resDir)
    if not os.path.exists(profileDir):
        os.mkdir(profileDir)
    if not os.path.exists(mediaDir):
        os.mkdir(mediaDir)

    api = CreateAuth()
    username = ""
    link = ""
    # status meaning it is a singular tweet
    if "status" in sys.argv[1]:
            link = link[link.rfind('/')+1:]
    else:
        username = sys.argv[1]

    
    if username != "":
        ArchiveLiked(username, api)
    else:
        PrepTweet(link, api)
