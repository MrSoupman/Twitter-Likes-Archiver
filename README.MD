# Twitter Likes Archiver
This script pulls all liked tweets of a user and builds them in an html format. It saves the tweet body including all images and videos. It is also able to save individual tweets. An index page is made to allow users to more easily browse through all their twitter likes.

# Downloading
Download the github repo either by cloning the repo or downloading it as a zip by clicking on Code -> Download Zip. it is important to at the very least, download TweetArchive.py and the template folder.


# Usage
First save your bearer token to a file 'key.txt'.
Next, run the script by inputting either the username or the link to the tweet you'd like to save.
Example: "python3 TweetArchive.py twitter" would begin to look at all tweets liked by the user "twitter" and begin archiving them from most recent to oldest.
Using "python3 TweetArchive.py https://twitter.com/Twitter/status/1476946953518948358" would save just that one tweet.
After running the script, tweets will be saved in the newly created archive folder. index.html will hold a list of all saved tweets with a link to them.

# Requirements
The following are required for TweetArchive to function properly:

 - Your own bearer token
 - beautifulsoup4==4.11.1
 - requests==2.27.1
 - tweepy==4.10.0
 - youtube_dl==2021.12.17

Alternatively, use the included requirements.txt file to install: ``python pip install -r requirements.txt``

