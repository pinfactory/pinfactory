#!/usr/bin/env python3

import logging
import os
import sys

from account import Account
from contract import Contract, ContractType, Issue, Maturity

class Offer(object):
    db = None

    @staticmethod
    def reduce_offer(curs, i, q_to_remove):
        '''Reduce the quantity of an existing offer (an argument of None is
           treated as the amount of the offer.)  Return the tokens to the
           account. Delete the offer if reduced to zero.'''
        curs.execute("SELECT account, price, side, quantity, all_or_nothing FROM offer WHERE id = %s", (i,))
        if curs.rowcount != 1:
            raise RuntimeError
        (a, p, s, q, aon) = curs.fetchone()
        if q_to_remove is None:
            q_to_remove = q
        if q_to_remove <= 0:
            raise RuntimeError
        if q_to_remove > q:
            raise RuntimeError
        if aon and q_to_remove < q: 
            raise RuntimeError("All or nothing offers cannot be reduced, only removed entirely")
        if s: # FIXED
            total = p * q_to_remove
        else: # UNFIXED
            total = (1000 - p) * q_to_remove
        curs.execute("UPDATE account SET balance = balance + %s WHERE id = %s",
            (total, a))
        if q_to_remove == q:
            curs.execute("DELETE FROM offer WHERE id = %s", (i,))
        else:
            curs.execute("UPDATE offer SET quantity = %s WHERE id = %s",
                (q - q_to_remove, i))
        if curs.rowcount != 1:
            raise RuntimeError

    def make_contract(self, curs, contract_type, fixed_holder, unfixed_holder, price, quantity):
        con = Contract(contract_type, fixed_holder, unfixed_holder, price, quantity).persist(curs)
        curs.execute("UPDATE account SET balance = balance - %s WHERE id = %s",
            (price * quantity - con.fixed_refund * 1000, fixed_holder))
        curs.execute("UPDATE account SET balance = balance - %s WHERE id = %s",
            ((1000 - price) * quantity - con.unfixed_refund * 1000, unfixed_holder))
        self.db.messages.add('contract_created', fixed_holder, contract_type,
                             self.db.FIXED, price, quantity, contract=con)
        self.db.messages.add('contract_created', unfixed_holder, contract_type,
                             self.db.UNFIXED, price, quantity, contract=con)
        if con.fixed_refund:
            self.db.messages.add('position_covered', fixed_holder, contract_type, quantity=con.fixed_refund, contract=con)
        if con.unfixed_refund:
            self.db.messages.add('position_covered', unfixed_holder, contract_type, quantity=con.unfixed_refund, contract=con)

    def make_offer(self, curs, account, contract_type, side, price, quantity, all_or_nothing):
        if side == self.db.UNFIXED:
            total = (1000 - price) * quantity
        else:
            total = price * quantity
        curs.execute("UPDATE account SET balance = balance - %s WHERE id = %s",
            (total, account))
        curs.execute("""INSERT INTO offer (account, contract_type, side, price, quantity, all_or_nothing)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            (account, contract_type.id, side, price, quantity, all_or_nothing))
        self.id = curs.fetchone()[0]
        self.db.messages.add('offer_created', account, contract_type, side, price, quantity, offer=self)

    def __init__(self, account, contract_type, side, price, quantity, oid=None, created=None, all_or_nothing=False):
        self.id = oid
        self.account = account
        self.contract_type = contract_type
        self.side = side
        self.price = price
        self.quantity = quantity
        self.created = created
        self.all_or_nothing = all_or_nothing
        if not self.contract_type.id:
            raise NotImplementedError

    def __eq__(self, other):
        if self.id is not None and other.id is not None and self.id != other.id:
            return False
        if self.account != other.account:
            logging.debug ("%s doesn't match %s" % (self.account, other.account))
            return False
        if self.contract_type != other.contract_type:
            logging.debug ("%s doesn't match %s" % (self.contract_type, other.contract_type))
            return False
        if self.all_or_nothing != other.all_or_nothing:
            logging.debug ("%s doesn't match %s" % (self.contract_type, other.contract_type)) 
            return false
        return self.side == other.side and self.price == other.price and self.quantity == other.quantity

    def __repr__(self):
        which = "UNFIXED"
        if self.side:
            which = "FIXED"
        aon = ''
        if self.all_or_nothing:
            aon = " (all or nothing)"
        return "%s Offer for %d units at %.3f on %s%s" % (which, self.quantity, self.price/1000, self.contract_type, aon)

    @classmethod
    def by_id(cls, oid):
        "Look up offers by id."
        try:
            return cls.filter(oid=oid, include_private=True)[0]
        except IndexError:
            return None

    @classmethod
    def filter(cls, oid=None, account=None, issue=None, include_private=False):
        "Look up offers."
        (all_ids, all_accounts, all_issues) = (False, False, False)
        if not oid:
            all_ids = True
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
            curs.execute('''SELECT account,
                            maturity, matures,
                            contract_type, issue, url, title,
                            side, price, quantity, id, created, 
                            all_or_nothing
                            FROM offer_overview WHERE 
                            (id = %s OR %s) AND
                            (account = %s OR %s) AND
                            (issue = %s OR %s)
                            ''', (oid, all_ids, uid, all_accounts, iid, all_issues))
            for row in curs.fetchall():
                (uid, mid, matures, cid, iid, url, title, side, price, quantity, oid, created, all_or_nothing) = row
                account = Account(uid=uid)
                issue = Issue(url=url, iid=iid, title=title)
                if (not include_private) and (not issue.is_public):
                    continue
                maturity = Maturity(matures, mid)
                ctype = ContractType(issue, maturity, cid)
                result.append(cls(account, ctype, side, price, quantity, oid, created, all_or_nothing))
        return result

    @property
    def datetime(self):
        return self.created.strftime("%d %b %H:%M")

    @property
    def displayprice(self):
        return "%.3f" % (self.price / 1000)

    @property
    def displayside(self):
        if self.side:
            return "FIXED"
        return "UNFIXED"

    @property
    def exists(self):
        "Check that the offer is in the database."
        if self.id is None:
            return False
        return Offer.by_id(self.id) is not None

    def place(self):
        result = []
        with self.db.conn.cursor() as curs:
            if self.side == self.db.FIXED:
                curs.execute("""SELECT id, account, price, quantity, all_or_nothing
                                FROM offer WHERE contract_type = %s AND side = %s and price <= %s
                                ORDER BY price, created""",
                    (self.contract_type.id, self.db.UNFIXED, self.price))
                for row in curs.fetchall():
                    (i, a, p, q, aon) = row
                    # Don't match existing all or nothing offers with a new smaller offer
                    if aon and q > self.quantity:
                        continue
                    # Don't match a new offer to an existing smaller offer
                    if self.all_or_nothing and q < self.quantity:
                        continue
                    if q <= self.quantity:
                        csize = q
                    else:
                        csize = self.quantity
                    self.reduce_offer(curs, i, csize)
                    contract_price = self.price # FIXME whoever gets an offer in first should get the best price (?)
                    self.make_contract(curs,
                                       contract_type = self.contract_type,
                                       fixed_holder = self.account.id,
                                       unfixed_holder = a,
                                       price = contract_price,
                                       quantity = csize)
                    self.quantity = self.quantity - csize
                    if self.quantity == 0:
                        break
                else: # No matching items, just make the offer
                    self.make_offer(curs, self.account.id, self.contract_type, self.side,
                                    self.price, self.quantity, self.all_or_nothing)
            else: # side is UNFIXED
                curs.execute("""SELECT id, account, price, quantity, all_or_nothing
                                FROM offer WHERE contract_type = %s AND side = %s and price >= %s
                                ORDER BY price DESC, created""",
                    (self.contract_type.id, self.db.FIXED, self.price))
                for row in curs.fetchall():
                    (i, a, p, q, aon) = row
                    if aon and q > self.quantity:   
                        continue
                    if self.all_or_nothing and q < self.quantity:
                        continue
                    if q <= self.quantity:
                        csize = q
                    else:
                        csize = self.quantity
                    self.reduce_offer(curs, i, csize)
                    contract_price = self.price  # FIXME whoever gets an offer in first should get the best price (?)
                    self.make_contract(curs,
                                       contract_type = self.contract_type,
                                       fixed_holder = a,
                                       unfixed_holder = self.account.id,
                                       price = contract_price,
                                       quantity = csize)
                    self.quantity = self.quantity - csize
                    if self.quantity == 0:
                        break
                else:
                    self.make_offer(curs, self.account.id, self.contract_type, self.side,
                                    self.price, self.quantity, self.all_or_nothing) 
            result = self.db.messages.flush(curs)
            curs.connection.commit()
        return result

    def cancel(self, user=None):
        if user and user != self.account:
            logging.info("Failed attempt to cancel offer %d by %s" % (self.id, user))
            return []
        with self.db.conn.cursor() as curs:
            (contract_type, price, quantity) = (self.contract_type, self.price, self.quantity)
            self.reduce_offer(curs, self.id, None)
            self.db.messages.add('offer_cancelled', self.account.id, contract_type=contract_type, price=price, quantity=quantity, offer=self)
            result = self.db.messages.flush(curs)
            curs.connection.commit()
            return result

    @classmethod
    def cleanup(cls, db, contract_types=[]):
        '''
        Remove any offers on contract types with a maturity date in the past.
        Refund and send a message to the user who placed the offer.
        '''
        expired = []

        for ctype in contract_types:
            todo = cls.filter(issue=ctype.issue)
            for item in todo:
                if item.contract_type == ctype:
                    expired.append(item.id)

        when = db.now()
        with db.conn.cursor() as curs:
            curs.execute('''SELECT offer.id FROM offer JOIN contract_type ON offer.contract_type = contract_type.id
                            JOIN maturity on contract_type.matures = maturity.id
                            WHERE maturity.matures <= %s''', (when,))
            for row in curs.fetchall():
                expired.append(row[0])

        for oid in expired:
            offer = cls.by_id(oid)
            with db.conn.cursor() as curs:
                offer.reduce_offer(curs, offer.id, None)
                db.messages.add('offer_cancelled',
                                offer.account.id, contract_type=offer.contract_type, side=offer.side,
                                price=offer.price, quantity=offer.quantity, offer=offer)
                db.messages.add('info', offer.account.id,
                    text="An offer from you has been cancelled because the maturity date is in the past.")
                db.messages.flush(curs)
                curs.connection.commit()

