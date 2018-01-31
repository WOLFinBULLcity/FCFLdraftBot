#!/usr/bin/python
import config
import line_profiler
import praw

from model.player import Player

class Draft:

    # @profile
    def __init__(self, id, submission):
        self.id = id
        self.submission = submission
        self.url = None
        self.auctions = []

    # @profile
    def set_url(self, url):
        self.url = url

    # @profile
    def add_auction(self, auction):
        # Only add the auction if it's new
        for a in self.auctions:
            if a == auction:
                # If we already have this auction, exit.
                return
        self.auctions.append(auction)

    # @profile
    def auction_from_id(self, id):
        for idx in range(len(self.auctions)):
            if self.auctions[idx].id == id:
                return self.auctions[idx]
        return None

    # @profile
    def get_auctions_for_player(self, name):
        found_auctions = []
        for idx in range(len(self.auctions)):
            if self.auctions[idx].player.name == name:
                found_auctions.append(self.auctions[idx])
        return found_auctions

    # @profile
    def nominate_player(self, name):
        player_auctions = self.get_auctions_for_player(name)

        for auction in player_auctions:
            if auction.is_active():
                return None

        existing_count = len(player_auctions)

        if existing_count >= config.max_player_copies:
            return None

        return Player(name,existing_count + 1)






