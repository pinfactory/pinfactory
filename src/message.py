#!/usr/bin/env python3

import collections
import logging

# from the file, import the class
from issue import Issue
from contract import ContractType
from maturity import Maturity


class Message(object):
    def __init__(
        self,
        mclass,
        account=None,
        contract_type=None,
        side=None,
        price=None,
        quantity=None,
        expires=None,
        offer=None,
        contract=None,
        text=None,
        created=None,
        mid=None,
    ):
        self.id = mid
        self.account = account
        self.contract_type = contract_type
        self.mclass = mclass
        self.side = side
        self.price = price
        self.quantity = quantity
        self.expires = expires
        self.offer = offer
        self.contract = contract
        self.text = text
        self.created = created

    @property
    # converting price to tokens from millitokens (for display)
    def displayprice(self):
        return "%.3f" % (self.price / 1000)

    @classmethod
    def filter(cls, account=None, issue=None, ticker=False):
        all_events = not ticker
        (all_accounts, all_issues) = (False, False)
        if issue:
            iid = issue.id
        else:
            iid = None
            all_issues = True
        if account:
            uid = account.id
        else:
            uid = None
            all_accounts = True

        result = []
        with cls.db.conn.cursor() as curs:
            curs.execute(
                """SELECT issue, url, title, maturity, matures,
                            id, class, created,
                            contract_type, side, price, quantity, expires, message
                            FROM message_overview
                            WHERE (%s OR issue = %s)
                            AND (%s OR recipient = %s)
                            AND (%s OR (side = true AND
                                (class = 'contract_created' OR class = 'contract_resolved')
                                AND quantity > 0))
                            ORDER BY created DESC""",
                (all_issues, iid, all_accounts, uid, all_events),
            )
            for row in curs.fetchall():
                (
                    iid,
                    url,
                    title,
                    maturity_id,
                    matures,
                    mid,
                    mclass,
                    created,
                    cid,
                    side,
                    price,
                    quantity,
                    expires,
                    text,
                ) = row
                if ticker and (not url or not title or not matures or not maturity_id):
                    pass
                    # continue #FIXME
                (issue, maturity, contract_type) = (None, None, None)
                if iid:
                    issue = Issue(iid=iid, url=url, title=title)
                if maturity_id and matures:
                    maturity = Maturity(matures, maturity_id)
                if issue and maturity:
                    contract_type = ContractType(issue, maturity, cid=cid)
                result.append(
                    cls(
                        mclass,
                        account=account,
                        contract_type=contract_type,
                        side=side,
                        price=price,
                        quantity=quantity,
                        text=text,
                        created=created,
                        expires=expires,
                        mid=mid,
                    )
                )
            return result

    # send takes a cursor because Messages are only sent as the result of
    # a transaction.  Send does not commit the transaction. The message is only
    # sent when a transaction goes through.
    def send(self, curs, log=False):
        if self.account is None:
            curs.execute("SELECT id FROM account WHERE system = true")
            self.account = curs.fetchone()[0]
        ctype = None
        if self.contract_type:
            ctype = self.contract_type.id
        curs.execute(
            """INSERT INTO message (class, recipient,
                                           contract_type, side, price, quantity, expires, message)
                                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                           RETURNING id""",
            (
                self.mclass,
                self.account,
                ctype,
                self.side,
                self.price,
                self.quantity,
                self.expires,
                str(self),
            ),
        )
        self.id = curs.fetchone()[0]
        if log:
            logging.info(self)
        return self

    @property
    # time when the message was generated.
    def datetime(self):
        return self.created.strftime("%d %b %H:%M")

    def make_text(self):
        whichside = "UNFIXED"
        if self.side == True:
            whichside = "FIXED"
        if self.mclass == "offer_created":
            exp = " (never expires)"
            if self.expires:
                exp = " (expires %s)" % self.expires.strftime("%d %b %H:%M")
            return "Offer made: %d units of %s on %s at a (fixed) price of %.3f%s" % (
                self.quantity,
                whichside,
                self.contract_type,
                self.price / 1000,
                exp,
            )
        if self.mclass == "offer_cancelled":
            return (
                "Offer cancelled: %d units of %s on %s at a (fixed) price of %.3f"
                % (self.quantity, whichside, self.contract_type, self.price / 1000)
            )
        if self.mclass == "contract_created":
            return "Contract formed: %d units of %s %s at a (fixed) price of %.3f" % (
                self.quantity,
                whichside,
                self.contract_type,
                self.price / 1000,
            )
        if self.mclass == "position_covered":
            return "Contract on %s had %d units covered and tokens returned" % (
                self.contract_type,
                self.quantity,
            )
        if self.mclass == "contract_resolved":
            return "Contract resolved: %s for a payout of %d tokens" % (
                self.contract_type,
                (self.price * self.quantity) / 1000,
            )
        if self.text:
            return self.text

    @property
    def summary(self):
        "Summary for notifications and RSS feeds"
        value = ""
        if int(self.price) and int(self.quantity):
            value = ": %d tokens" % ((self.price * self.quantity) / 1000)
        if self.mclass == "offer_created" and self.side:
            return "New FIXED offer on %s matures %s%s" % (
                self.contract_type.project,
                self.contract_type.maturity.display,
                value,
            )
        if self.mclass == "offer_created":
            return "New UNFIXED offer on %s matures %s%s" % (
                self.contract_type.project,
                self.contract_type.maturity.display,
                value,
            )
        if self.mclass == "contract_created":
            return "New price on a %s issue: %.3f" % (
                self.contract_type.project,
                (self.price / 1000),
            )
        else:
            return self.__repr__()

    def __repr__(self):
        try:
            return self.make_text()
        except TypeError as err:
            if self.text:
                return self.text
            else:
                raise NotImplementedError

    def __str__(self):
        return self.__repr__()


# Convenient class to handle a list of messages. For example, when a contract is
# being created, a number of messages need to be sent. Message list allows us
# to build up a list of messages and send them.
class MessageList(collections.UserList):
    def __init__(self, market=None):
        self.market = market
        self.data = []

    def add(
        self,
        mclass,
        account=None,
        contract_type=None,
        side=None,
        price=None,
        quantity=None,
        expires=None,
        offer=None,
        contract=None,
        text=None,
    ):
        if account is None:
            account = self.market.system_id
        self.append(
            Message(
                mclass,
                account,
                contract_type,
                side,
                price,
                quantity,
                expires,
                offer,
                contract,
                text,
            )
        )

    def filter(self, account=None):
        result = MessageList()
        for item in self:
            if account is not None and item.account != account.id:
                continue
            result.append(item)
        return result

    def send_all(self, curs):
        for m in self:
            m.send(curs)
        return self

    def flush(self, curs):
        self.send_all(curs)
        result = MessageList()
        result.data = self.data[:]
        self.data = []
        return result

    def __repr__(self):
        return ", ".join(repr(m) for m in self)
