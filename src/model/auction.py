#!/usr/bin/python
import config
import line_profiler

from datetime import datetime
from datetime import timedelta
from money import Money

# @profile
def bid_str(bid):
    return str(bid.amount.format("en_US", '$#0', False))

class Auction:
    status_active = 'ACTIVE'
    status_closed = 'CLOSED'

    # @profile
    def __init__(self, player, nominator, url, id, comment):
        self.player = player
        self.nominator = nominator
        self.url = url
        self.id = id
        self.comment = comment
        self.bids = []
        self.top_bid =  None
        self.status = self.status_active

    # @profile
    def __str__(self):
        return str(self.__dict__)

    # @profile
    def __eq__(self, other):
        return (
            self.id == other.id and
            self.player == other.player and
            self.nominator == other.nominator and
            self.url == other.url
        )

    # @profile
    def add_bid(self, bid):
        # Only add the bid if it's new
        for b in self.bids:
            if b == bid:
                # If we already have this bid, exit.
                return True

        # If it's a new bid, make sure it's higher than the top bid.
        if self.top_bid is None or bid.amount > self.top_bid.amount:
            self.bids.append(bid)
            self.top_bid = bid
            return True
        else:
            return False

    # @profile
    def time_remaining(self):
        if self.top_bid is None or not self.is_active():
            return None
        expire_time = self.top_bid.time + timedelta(seconds=config.pick_time_seconds)
        now = datetime.now()
        return expire_time - now

    # @profile
    def update_status(self):
        if self.time_remaining() is None:
            return
        if self.status == self.status_active and self.time_remaining().total_seconds() < 0:
            self.status = self.status_closed
            self.comment.reply("**AUCTION CLOSED**" + '''
'''
            + "Winning bid: " + str(self.top_bid.amount.format("en_US", '$#0', False)) +
                               " from " + self.top_bid.team.name
            )
        else:
            self.status = self.status_active

    # @profile
    def strfdelta(self,tdelta):
        hours, rem = divmod(tdelta.total_seconds(), 3600)
        minutes, seconds = divmod(rem, 60)
        return str(int(hours)) + " hour(s) and " + str(int(minutes)) + " minute(s)"

    # @profile
    def is_active(self):
        return self.status == self.status_active

    # @profile
    def announce(self):
        if self.top_bid is None or not self.is_active():
            return ""
        else:
            return str(
                    "**" + self.player.name + " (Copy " + str(self.player.copy) + ")**: " +
                    "Top Bid = " + str(self.top_bid.amount.format("en_US", '$#0', False)) +
                    " by " + self.top_bid.team.name +
                    " with " + self.strfdelta(self.time_remaining()) + " remaining. " +
                    "[BID NOW!](" + str(self.url) + ")"
            )
