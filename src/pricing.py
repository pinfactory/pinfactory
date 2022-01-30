#!/usr/bin/env python3

from datetime import datetime, timedelta
from offer import Offer
from position import Position
from market import Market

import psycopg2

# This class contains pricing funcitons that take, as arguments, the prices
# specified by the two counter parties and compute the contract price in
# different ways. The methods are simple and unused at present but more
# sophisticated pricing strategies will be needed as our marketplace matures.


class Pricing(object):
    def __init__():
        return

    @classmethod
    def compute_price(price1, price2):

        return compute__average_price(price1, price2)

    @classmethod
    def compute__average_price(price1, price2):

        return (price1 + price2) / 2

    @classmethod
    def compute_min_price(price1, price2):

        return min(price1, price2)

    @classmethod
    def compute_max_price(price1, price2):

        return max(price1, price2)
