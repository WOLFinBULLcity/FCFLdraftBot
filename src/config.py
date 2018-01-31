#!/usr/bin/python
import praw

reddit = praw.Reddit('bot1')

subreddit = reddit.subreddit("FCFLfootball")

reddit_base_url = "http://www.reddit.com"

league_name = 'FCFL'

teams_flair = '[TEAMS]'
draft_flair = '[DRAFT]'

edit_tag = 'EDIT'

auctions_file = './pickle/auctions_file.pickle'
league_file = './pickle/league_file.pickle'
player_bids_file = './pickle/player_bids_file.pickle'
team_assignments_file = './pickle/team_assignments_file.pickle'

chars_to_strip = '$#!@%'

max_player_copies = 2

# pick_time_seconds = 86400 # Real limit -- 24 Hours
pick_time_seconds = 43200 # Test Limit -- 12 hours

