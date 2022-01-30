#!/usr/bin/env python3

import logging
import sys

from account import Account
from contract import ContractType
from issue import Issue
from maturity import Maturity


class Position(object):
    db = None

    def __init__(self, pid, account, contract_type, quantity, basis, created, modified):
        "Position"
        self.id = pid
        self.account = account
        self.contract_type = contract_type
        self.quantity = quantity
        self.basis = basis
        self.created = created
        self.modified = modified
        try:
            self.offset_form = "<!-- offset form for %s --!>" % pid
        except:
            self.offset_form = "<!-- no offset form -->"

    def __repr__(self):
        side = "FIXED"
        if self.quantity < 0:
            side = "UNFIXED"
        return "%d %s contract on %s" % (abs(self.quantity), side, self.contract_type)

    @property
    def side(self):
        return self.quantity > 0

    @property
    def datetime(self):
        return self.created.strftime("%d %b %H:%M")

    @property
    def displayprice(self):
        return "%.3f" % ((self.basis / abs(self.quantity)) / 1000)

    @property
    def display_unfixed_price(self):
        return "%.3f" % (1 - (self.basis / abs(self.quantity)) / 1000)

    @property
    def display_total_price(self):
        return "%d" % int(self.basis / 1000)

    @property
    def display_total_unfixed_price(self):
        return "%d" % int(abs(self.quantity) - self.basis / 1000)

    @property
    def displayside(self):
        if self.quantity > 0:
            return "FIXED"
        return "UNFIXED"

    @property
    def displayquantity(self):
        return abs(self.quantity)

    @classmethod
    def by_id(cls, pid):
        try:
            return cls.filter(pid=pid)[0]
        except IndexError:
            logging.warning("Could not find a position for id %d: %s" % (pid, exc))
            return None

    @classmethod
    def filter(cls, pid=None, account=None, issue=None):
        (all_pids, all_accounts, all_issues) = (False, False, False)
        if not pid:
            all_pids = True
        if account:
            uid = account.id
        else:
            uid = None
            all_accounts = True
        if issue:
            iid = issue.id
        else:
            iid = None
            all_issues = True
        result = []
        with cls.db.conn.cursor() as curs:
            curs.execute(
                """SELECT maturity.id, maturity.matures, contract_type.id,
                            contract_type.issue, issue.url, issue.title,
                            position.account, position.quantity, position.basis,
                            position.created, position.modified, position.id
                            FROM maturity JOIN contract_type ON maturity.id = contract_type.matures
                            JOIN issue ON issue.id = contract_type.issue
                            JOIN position ON contract_type.id = position.contract_type
                            WHERE (position.id = %s OR %s)
                            AND (account = %s OR %s)
                            AND (issue = %s OR %s)
                            """,
                (pid, all_pids, uid, all_accounts, iid, all_issues),
            )
            for row in curs.fetchall():
                (
                    mid,
                    matures,
                    cid,
                    iid,
                    url,
                    title,
                    uid,
                    quantity,
                    basis,
                    created,
                    modified,
                    pid,
                ) = row
                account = Account(uid=uid)
                issue = Issue(url=url, iid=iid, title=title)
                maturity = Maturity(matures, mid)
                ctype = ContractType(issue, maturity, cid)
                result.append(
                    cls(pid, account, ctype, quantity, basis, created, modified)
                )
        return result

    def offset(self, total_price):
        """
        Returns a new offer that if accepted would cancel out this position.
        """
        account = self.account
        contract_type = self.contract_type
        side = not self.side
        price = (total_price) / abs(self.quantity)
        if not self.side:
            price = 1000 - price
        quantity = abs(self.quantity)
        tmp = self.db.offer(account, contract_type, side, price, quantity)
        return tmp
