import praw 	# Python Reddit API Wrapper
import re  		# Regex
import json 	# Read.json files
import datetime # Date, time
import sys 		# Command line arguments
from credentials import USERNAME, PASSWORD, \
		USER_AGENT, CLIENT_ID, CLIENT_SECRET, \
		USER_AGENT2, CLIENT_ID2, CLIENT_SECRET2, \
		USER_AGENT_DEBUG, CLIENT_ID_DEBUG, CLIENT_SECRET_DEBUG, \
		USER_AGENT2_DEBUG, CLIENT_ID2_DEBUG, CLIENT_SECRET2_DEBUG 	
		# Auth data for Reddit API

starttime = datetime.datetime.now().timestamp()

# This python script is a reddit bot which responds to submissions 
# with text formatted like '[[CARD NAME]]' with information about 
# the card, from www.shardveil.com/cards/. 

# Get the data from the .json file
with open("../ShardBound_cards.json") as data_file:
	data = json.load(data_file)

# Dictionary for display purposes
colors = {"Neutral": "", "Steelsinger": "(Red)", "Fatekeeper": "(Blue)", "Landshaper": "(Green)", "Packrunner": "(Yellow)", "Wayfinder": "(Orange)", "Bloodbinder": "(Purple)"}


# {0} Card Name
# {1} Image Link
# {2} Faction
# {3} Type (Range/Melee)
# {4} Mana Cost
# {5} Attack Value
# {6} Health Value
# {7} Tribe
# {8} Rarity
# {9} Card Text
# {10} Color

# [Novice Knight](link.jpg) Neutral color common melee minion
# 1 mana 2/2 tribe - text here

MINION_REPLY_TEMPLATE = '* [{0}]({1}) {2} {10} {8} {3}\n\n       {4} Mana {5}/{6} {7} - {9}\n\n'
ARTIFACT_REPLY_TEMPLATE = '* [{0}]({1}) {2} {10} {8} {3}\n\n       {4} Mana 0/{6} {7} - {9}\n\n'
SPELL_REPLY_TEMPLATE = '* [{0}]({1}) {2} {7} {5} {3}\n\n       {4} Mana - {6}\n\n'
HERO_REPLY_TEMPLATE = '* [{0}]({1}) {2} {7} {3}\n\n       {4}/{5} - {6}\n\n'
SIMPLE_TEMPLATE = "* Card: {0}\n\n"

REPLY_FOOTER = '\n\n^(This comment was generated by an automated bot. Please direct any questions or feedback to) ^/u\/Seura.)\n\n'

LOG_TEMPLATE = "\n{0} Detected: {1} in {2}'s {3} ({4}).\n"

def main():
	# Pick which mode we operate in
	if len(sys.argv) == 2 and sys.argv[1] == 'submissions':
		print("Submission Mode")
		debug = False
		subMode = True
		MY_USER_AGENT = USER_AGENT
		MY_CLIENT_ID = CLIENT_ID
		MY_CLIENT_SECRET = CLIENT_SECRET
		filename = "logfile_s.txt"

	elif len(sys.argv) == 2 and sys.argv[1] == 'comments':
		print("Comment Mode")
		debug = False
		subMode = False
		MY_USER_AGENT = USER_AGENT2
		MY_CLIENT_ID = CLIENT_ID2
		MY_CLIENT_SECRET = CLIENT_SECRET2
		filename = "logfile_c.txt"

	elif len(sys.argv) == 3 and sys.argv[1] == 'submissions' and sys.argv[2] == 'debug':
		print("Submissions Debug Mode")
		debug = True
		subMode = True
		MY_USER_AGENT = USER_AGENT_DEBUG
		MY_CLIENT_ID = CLIENT_ID_DEBUG 
		MY_CLIENT_SECRET = CLIENT_SECRET_DEBUG
		filename = "logfile_sd.txt"

	elif len(sys.argv) == 3 and sys.argv[1] == 'comments' and sys.argv[2] == 'debug':
		print("Comments Debug Mode")
		debug = True
		subMode = False
		MY_USER_AGENT = USER_AGENT2_DEBUG
		MY_CLIENT_ID = CLIENT_ID2_DEBUG
		MY_CLIENT_SECRET = CLIENT_SECRET2_DEBUG
		filename = "logfile_cd.txt"

	else:
		print("Incorrect arguments. try 'python redditBot.py (submissions/comments) (debug/'')'")
		return

	# Initialize the Reddit Client
	print("initializing reddit client")
	reddit = praw.Reddit(user_agent=MY_USER_AGENT, client_id=MY_CLIENT_ID, client_secret=MY_CLIENT_SECRET, username=USERNAME, password=PASSWORD)

	# Which subreddit?
	if debug:
		subreddit = reddit.subreddit('Alex_is_a_Scrub')
	else:
		subreddit = reddit.subreddit('Shardbound')

	if subMode:
		print("Submission stream")
		for item in subreddit.stream.submissions():
			process_item(item, True, filename)
	else:
		print("Comment stream")
		for item in subreddit.stream.comments():
			process_item(item, False, filename)

# subMode is: {True: submissionMode, False: commentMode}
def process_item(item, subMode, filename):
	# Don't do anything if the comment was posted before the bot was started
	if starttime > item.created_utc:
		print("skipped:", starttime, ">", item.created_utc)
		return

	# Normalize text to lowercase
	if subMode:
		text = item.selftext.lower()
	else:
		text = item.body.lower()

	# Search for [[CARD NAME]] patterns
	pattern = re.compile('\[\[[a-z0-9,\' !-]+\]\]')
	cardList = re.findall(pattern, text)

	logfile = open(filename, 'a')

	if len(cardList) is not 0:
		author = item.author 
		itemID = item.permalink if subMode else item.link_permalink
		logType = "submission" if subMode else "comment"
		time = datetime.datetime.now()
		logfile.write(LOG_TEMPLATE.format(time, cardList, author, logType, itemID))


	reply_text = ''
	for card in cardList:
		card = card[2:-2]
		# Make sure the card is valid
		if card in data:
			reply_text += generate_reply(data[card])
		else:
			logfile.write("Couldn't find {}\n".format(card))

	logfile.close()

	# Reply
	if subMode:
		reply_target = item.title
	else:
		reply_target = item.author

	if reply_text is not '':
		print("replying to", reply_target)
		reply_text += REPLY_FOOTER
		item.reply(reply_text)

def generate_reply(card):
	if "Artifact" in card["type"]:
		reply = MINION_REPLY_TEMPLATE.format(card["name"], card["link"], card["faction"], card["type"], card["mana"], 0, card["health"], card["tribe"], card["rarity"], card["text"], colors[card["faction"]])

	elif "Minion" in card["type"]:
		reply = MINION_REPLY_TEMPLATE.format(card["name"], card["link"], card["faction"], card["type"], card["mana"], card["attack"], card["health"], card["tribe"], card["rarity"], card["text"], colors[card["faction"]])

	elif "Spell" in card["type"]:
		reply = SPELL_REPLY_TEMPLATE.format(card["name"], card["link"], card["faction"], card["type"], card["mana"], card["rarity"], card["text"], colors[card["faction"]])

	elif "Hero" in card["type"]:
		reply = HERO_REPLY_TEMPLATE.format(card["name"], card["link"], card["faction"], card["type"], card["attack"], card["health"], card["text"], colors[card["faction"]])

	else:
		reply = SIMPLE_TEMPLATE.format(card["name"])

	return reply

if __name__ == '__main__':
	main()