#!/usr/bin/python
import config
import cPickle as pickle
import line_profiler
import math
import os
import praw

from datetime import datetime
from datetime import timedelta
from model.auction import Auction
from model.bid import Bid
from model.conference import Conference
from model.draft import Draft
from model.league import League
from model.player import Player
from model.team import Team
from model.team_assignments import TeamAssignments
from money import Money

# Check if we have a league saved
if os.path.isfile(config.league_file):
    with open(config.league_file, 'rb') as f:
        league = pickle.load(f)
else:
    # Create the instance of our Fantasy League
    league = League(config.league_name)

@profile
def scan_inbox():
    for message in config.reddit.inbox.messages(limit=None):
        if message.new:

            # Get our team and conference
            nominating_team = None
            nominating_conf = None

            for idx in range(len(league.conferences)):
                nominating_team = league.conferences[idx].team_assignments.team_from_coach(str(message.author))
                if nominating_team is not None:
                    nominating_conf = league.conferences[idx]
                    break

            # If this is not a message from a known coach, ignore it.
            if nominating_conf is None or nominating_team is None:
                # TODO: Add a direct link to the team thread in this message.
                message.mark_read()
                message.reply("It looks like you haven't registered your team in the team thread yet. " +
                              "Please follow the directions in the team thread to register your team and then try " +
                              "your nomination again.")
                continue

            # Create an auction for the nominated player

            # TODO: Eventually try to validate player name against Google sheet
            player_name = str(message.subject)

            try:
                trunc_value = str(message.body).translate(None, config.chars_to_strip).split(".")[0]
                bid_amount = Money(trunc_value, 'USD')
                bid_amount_str = str(bid_amount.format("en_US", '$#0', False))
            except ValueError:
                # If we can't make turn the bid into a valid bid amount, reject the nomination
                message.mark_read()
                message.reply(
                        "Unable to accept nomination for " + player_name + ". Please make sure that your " +
                        "message subject is the player you're nominating and the message body is a starting " +
                        "bid (e.g. $1). I'm unable to make cents of your bid as provided: " +
                        str(message.body) + ". Ha Ha Ha. That was a great currency pun I just made."
                )
                continue

        # Attempt to nominate the player
            player = nominating_conf.draft.nominate_player(player_name)

            if player is None:
                # We don't want to respond to this more than once.
                message.mark_read()

                # TODO: Account for nomination order
                reply_body = "That player cannot be nominated at this time."

                # Get any existing auctions with the player
                auctions_for_player = nominating_conf.draft.get_auctions_for_player(player_name)

                # Check if both copies have already been nominated
                if len(auctions_for_player) > 1:
                    reply_body = "Both copies of " + player_name + " have already been nominated."

                # Otherwise, check if the first copy is still actively being auctioned.
                elif len(auctions_for_player) == 1 and auctions_for_player[0].is_active():
                    reply_body = ("You must wait for the auction for the first copy of " + player_name +
                                  " to conclude before you may nominate the second copy.")

                message.reply(reply_body)
                break

            # TODO: Indicate which copy
            auction_comment = nominating_conf.draft.submission.reply(
                    player.name +
                    " (Copy " + str(player.copy) + ")"
            )

            nominator = nominating_conf.team_assignments.team_from_coach(str(message.author))
            auction_url = config.reddit_base_url + str(auction_comment.permalink)
            auction = Auction(player, nominator, auction_url, auction_comment.fullname, auction_comment)

            bid_comment = auction_comment.reply(bid_amount_str)

            bid = Bid(nominating_team,bid_amount,datetime.fromtimestamp(message.created_utc),bid_comment.fullname, bid_comment)
            auction.add_bid(bid)

            nominating_conf.draft.add_auction(auction)

            message.mark_read()

@profile
def scan_conferences():
    for submission in config.subreddit.hot(limit=None):

        # Check if this is a team assignment thread
        if submission.link_flair_text == config.teams_flair:
            for comment in submission.comments:
                # Make sure the message isn't removed
                if comment.removed:
                    continue

                conference = league.conference_from_id(comment.fullname)

                # Add the conference if we don't already have it
                if conference is None:
                    conference = Conference(str(comment.body),comment.fullname)

                    # Create a Draft thread for the conference
                    submission_title = "MOCK " + conference.name + " Draft Thread"
                    submission_body = ("This is the draft thread for the " + conference.name +
                                       ". To nominate a player, send me a PM with the player name as the subject " +
                                       "and your opening bid as the message body. In order to bid, reply directly" +
                                       " to the nomination post containing the player's name. Use the 'BID NOW' " +
                                       "link for quick access to the nomination post.")
                    draft_thread = config.subreddit.submit(submission_title, submission_body)
                    draft_thread.mod.flair(text=config.draft_flair)

                    conference.draft = Draft(draft_thread.fullname, draft_thread)

                    league.add_conference(conference)

            # Scan the comment replies and update the team assignments for this conference.
                scan_teams(comment,conference.team_assignments)

@profile
def scan_teams(comment, assignments):
    for reply in comment.replies:
        # Make sure the message isn't removed
        if reply.removed:
            continue

        # Add the user to the approved submitters list
        config.subreddit.contributor.add(reply.author.name)

        # Keep our team assignments up to date
        assignments.add_team(Team(str(reply.author.name),str(reply.body), reply.fullname))
        assignments.set_url(config.reddit_base_url + str(comment.permalink))

@profile
def scan_drafts():
    for submission in config.subreddit.hot(limit=None):
        # Check if this is a draft thread
        if submission.link_flair_text == config.draft_flair:
            # check for the conference name in the thread title
            draft_conf = None
            for idx in range(len(league.conferences)):
                if league.conferences[idx].name in str(submission.title):
                    draft_conf = league.conferences[idx]
                    break

            if draft_conf is None:
                continue

            # Check if we already have a draft for this conference
            if draft_conf.draft is None:
                draft_conf.draft = Draft(submission.fullname, submission)

            needs_auctioneer = True

            for comment in submission.comments:
                # Make sure the message isn't removed
                if comment.removed:
                    continue

                # If the comment author is this bot and not stickied
                if is_mine(comment) and not comment.stickied:

                    # Retrieve the auction
                    auction = draft_conf.draft.auction_from_id(comment.fullname)
                    if auction is None:
                        # TODO: Better error handling here.
                        print("ERROR GETTING AUCTION FOR PLAYER: " + str(comment.body) + ", ID: " + comment.fullname)

                        # Remove the post
                        comment.mod.remove()
                        continue

                    for reply in comment.replies:
                        # Make sure the message isn't removed
                        if reply.removed:
                            continue

                        # Skip the opening bid post made by this bot
                        if is_mine(reply):
                            continue

                        # Get the team doing the bidding
                        bidding_team = draft_conf.team_assignments.team_from_coach(str(reply.author.name))

                        # Only count the bid if we have a valid team assignment
                        if bidding_team is not None:

                            # Try to make sense of the bid amount
                            try:

                                trunc_value = str(reply.body).translate(None, config.chars_to_strip).split(".")[0]
                                bid_amount = Money(trunc_value, 'USD')

                                # If the comment has been edited, we use the edit time instead of the created time.
                                bid_time_unix = reply.created_utc
                                if reply.edited:
                                    bid_time_unix = reply.edited

                                bid_timestamp = datetime.fromtimestamp(bid_time_unix)

                                bid = Bid(bidding_team,bid_amount,bid_timestamp,reply.fullname,reply)
                                auction.add_bid(bid)
                            except ValueError:
                                # If we can't make turn the bid into a valid bid amount, reject the nomination
                                message_subject = "Bid Error"
                                message_body = (
                                    "Unable to accept your bid for " + str(comment.body) + ". Please make sure that you " +
                                    "are only posting a dollar amount for your bid. e.g. $5. Do not include anything " +
                                    "else within your post. Your post was removed, so please try again."
                                )
                                config.reddit.redditor(reply.author).message(message_subject,message_body)
                                reply.mod.remove()
                                continue

                        else:
                            # TODO: Make this look up team/conference by author and direct to correct thread.
                            author = str(reply.author)
                            subject = "Attempted bid on " + auction.player.name
                            body = ("You have attempted to bid on " + auction.player.name +
                                    " in the " + draft_conf.name + " conference draft. " +
                                    "You either have not yet registered your team in the team thread, " +
                                    "or you are bidding in another conference's draft.")

                            config.reddit.redditor(author).message(subject,body)
                            reply.mod.remove()

                    auction.update_status()

                elif is_mine(comment) and comment.stickied:
                    # Check if anyone has replied to this post directly
                    # TODO: Make the nomination instructions be a template that can be used in multiple places.
                    for reply in comment.replies.replace_more(limit=None):
                        # Ignore if already removed.
                        if comment.removed:
                            continue

                        remove_post_bad_reply(reply)

                    needs_auctioneer = False
                    comment.edit(build_auctioneer_body(draft_conf.draft))

                else:
                    # Someone has replied to the OP, assume it's a nomination attempt and remove it.
                    remove_post_bad_reply(comment)

            # If this draft thread doesn't already have an auctioneer post, we need to add one.
            if needs_auctioneer:
                auctioneer_comment = submission.reply(build_auctioneer_body(draft_conf.draft))
                auctioneer_comment.mod.distinguish('yes',True)

@profile
def is_mine(comment):
    return comment.author == config.reddit.user.me()

@profile
def remove_post_bad_reply(comment):
    # Ignore if already removed.
    if comment.removed:
        return

    comment.mod.remove()

    author = str(comment.author)
    subject = "Nomination Instructions"
    body = ("You have replied either to the OP or to the active auctions post. Your comment will be removed. " +
            "If you are attempting to nominate a player, please send me a PM with the player's " +
            "name as the subject line and a starting bid (e.g. $1) as the message body.")
    if author is not None:
        config.reddit.redditor(author).message(subject,body)

@profile
def build_auctioneer_body(draft):
    post_body = '''
Active Auctions:


'''

    for idx in range(len(draft.auctions)):
        if draft.auctions[idx].is_active():
            post_body += (
'''

'''
            + draft.auctions[idx].announce() +
'''

'''
            )
    return post_body

# scan the team thread for new conference team/coach assignments
scan_conferences()

# scan inbox for player nominations
scan_inbox()

# scan the draft threads for new auctions/bids
scan_drafts()



# # Print Conference and Team assignments
# for c in league.conferences:
#     print("==============================\n")
#     print(c.name + " Team List: ")
#     for team in c.team_assignments.teams:
#         print("Team: " + team.name + ", Coach: " + team.coach)
#     print("==============================\n")



# Print all auction data
for c_idx in range(len(league.conferences)):
    c = league.conferences[c_idx]
    print("==============================\n")
    print("======= " + c.name + " ======")

    for a_idx in range(len(league.conferences[c_idx].draft.auctions)):
        a = league.conferences[c_idx].draft.auctions[a_idx]
        print("==============================\n")
        print("Player: " + a.player.name + ", Copy " + str(a.player.copy))
        print("Auction ID: " + a.id)
        print("Nominated By: " + a.nominator.name)
        print("Auction Status: " + a.status)
        print("Top Bid: " + str(a.top_bid.amount.format("en_US", '$#0', False)) + " by team " + a.top_bid.team.name)
        print("Top Bid Time: " + a.top_bid.time.strftime('%Y-%m-%d %H:%M:%S'))
        print("URL: " + a.url)
        print("==============================\n")


# Save records
with open(config.league_file, 'wb') as f:
    pickle.dump(league, f)
