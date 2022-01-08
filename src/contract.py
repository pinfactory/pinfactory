#!/usr/bin/env python3

#Contract object is the external view where we keep track of forming the contract
#and position is how it gets persisted in the database (internal view).

import logging

import psycopg2

from issue import Issue
from maturity import Maturity

class Contract(object):
    def __init__(self, contract_type, fixed_holder, unfixed_holder, price, quantity):
        '''
        These are (probably) not the contracts you're looking for.

        Contracts in the _database_ are represented as a pair of Positions.

        Contract objects are used to keep track of a match between two offers.
        When they get persisted to the database, they're kept as individual
        positions of the two sides.
        '''
        self.contract_type = contract_type
        self.fixed_holder = fixed_holder
        self.unfixed_holder = unfixed_holder
        self.price = price
        self.quantity = quantity
        self.fixed_refund = 0
        self.unfixed_refund = 0
        if not self.contract_type.id:
            raise NotImplementedError

#Python: how to describe your object as a line of text. price is the price of
#the fixed side. Refund is tricky -- depends on whether you have taken an
#offsetting position.
    def __repr__(self):
        return ("fixed refund: %s unfixed refund: %s" % (self.fixed_refund, self.unfixed_refund))

    @staticmethod
    def q_and_refund(old_q, new_contract):
        '''
        Refund is how many units can be "refunded" because they're offset by a
        previous position.

        This return value is in units.
        '''
        refund_units = 0
        new_q = old_q + new_contract
        if old_q * new_contract < 0: # different signs
            refund_units = min(abs(old_q), abs(new_contract))
        return (new_q, refund_units)

#Sign of the quantity variable determines which side: positive is fixed and
#negative is unfixed. Once the contract object is persisted to the Database
#that contract object does not exist anymore, we just store positions internally.
#basis keeps track of what price you paid for what position. Any offsetting
#is taken care of here. Resolve simply resolves what exists and does not
#care about history.
    def persist_side(self, contract_type, acct, pos_price, quantity, curs):
        '''
        Store one side of a contract.
        This can result in creating a new position, updating an old position,
        or cancelling out a position.

        The pos_price argument here is the amount paid for this side, per unit.
        This is a unit price per unit not a "price of the FIXED side" as in
        other functions.
        '''
        old_q = 0
        old_basis = 0
        curs.execute("SELECT quantity, basis FROM position WHERE contract_type = %s AND account = %s",
                     (contract_type.id, acct))
        if curs.rowcount == 1:
            (old_q, old_basis) = curs.fetchone()
        (new_q, refund) = self.q_and_refund(old_q, quantity)
        new_basis = old_basis + (pos_price * abs(quantity)) - (refund * 1000)
        if new_basis < 0:
            new_basis = 0
        if old_q and new_q:
            curs.execute("UPDATE position SET quantity = %s, basis = %s WHERE contract_type = %s AND account = %s",
                        (new_q, new_basis, contract_type.id, acct))
        elif new_q:
            curs.execute("INSERT INTO position (contract_type, account, basis, quantity) VALUES (%s, %s, %s, %s)",
                         (contract_type.id, acct, new_basis, new_q))
        else:
            curs.execute("DELETE FROM position WHERE contract_type = %s AND account = %s",
                     (contract_type.id, acct))
        return refund

    def persist(self, curs):
        self.fixed_refund = self.persist_side(self.contract_type, self.fixed_holder, self.price, self.quantity, curs)
        self.unfixed_refund = self.persist_side(self.contract_type, self.unfixed_holder, 1000 - self.price, -1 * self.quantity, curs)
        return self


class ContractType(object):
    db = None

    def __init__(self, issue, maturity, cid=None):
        self.id = cid
        self.issue = issue
        self.maturity = maturity
        self.resolve_form = None

    def __eq__(self, other):
        if self and not other:
            return False
        if other and not self:
            return False
        if self.id and other.id and self.id != other.id:
            return False
        if self.maturity != other.maturity:
            return False
        if self.issue != other.issue:
            return False
        return True

    def __repr__(self):
        return "%s (%d) with %s" % (self.issue, self.issue.issuenumber, self.maturity)

    @property
    def project(self):
        try:
            return ('/').join(self.issue.url.split('/')[3:5])
        except Exception as e:
            return "an open source project"

    def persist(self):
        with self.db.conn.cursor() as curs:
            curs.execute("INSERT INTO contract_type (issue, matures) VALUES (%s, %s) RETURNING id",
                (self.issue.id, self.maturity.id))
            self.id = curs.fetchone()[0]
            curs.connection.commit()
        return self

    @classmethod
    def resolvable(cls):
        result = []
        with cls.db.conn.cursor() as curs:
            curs.execute('''SELECT DISTINCT maturity.matures, maturity.id, issue.url, issue.title, issue.id, contract_type.id
                            FROM maturity JOIN contract_type on maturity.id = contract_type.matures
                            JOIN issue ON issue.id = contract_type.issue
                            JOIN position ON contract_type.id = position.contract_type
                            WHERE maturity.matures < NOW()
                            ORDER BY maturity.matures''')
            for row in curs.fetchall():
                (matures, mid, url, title, iid, cid) = row
                issue = Issue(url=url, iid=iid, title=title)
                maturity = Maturity(matures, mid)
                result.append(cls(issue, maturity, cid))
        return result

    @classmethod
    def lookup(cls, iid, mid):
        with cls.db.conn.cursor() as curs:
            curs.execute('''INSERT INTO contract_type (issue, matures) VALUES (%s, %s)
                            ON CONFLICT (issue, matures) DO UPDATE set matures = %s RETURNING id''',
                            (iid, mid, mid))
            cid = curs.fetchone()[0]
            curs.execute('''SELECT maturity.matures, issue.url, issue.title
                            FROM maturity JOIN contract_type on maturity.id = contract_type.matures
                            JOIN issue ON issue.id = contract_type.issue
                            WHERE contract_type.id = %s''', (cid,))
            (matures, url, title) = curs.fetchone()
            issue = Issue(url=url, iid=iid, title=title)
            maturity = Maturity(matures, mid)
            return cls(issue, maturity, cid)

    @classmethod
    def cleanup(cls, contract_types=[]):
        "Remove contract types that are no longer in use."
        expired = []
        for ctype in contract_types:
            expired.append(ctype.id)
        with cls.db.conn.cursor() as curs:
            curs.execute('''SELECT contract_type.id FROM contract_type JOIN maturity
                          ON contract_type.matures = maturity.id
                          WHERE maturity.matures < NOW()''')
            for row in curs.fetchall():
                expired.append(row[0])
        for cid in expired:
            try:
                with cls.db.conn.cursor() as curs:
                    curs.execute("DELETE FROM contract_type WHERE id = %s", (cid,))
                    cls.db.conn.commit()
            except psycopg2.errors.ForeignKeyViolation:
                cls.db.conn.rollback()

    def resolve(self, side):
        '''
        True = fixed, False = unfixed.
        '''
        total = 0
        result = []
        self.db.cleanup(contract_types=[self])
        with self.db.conn.cursor() as curs:
            while True:
                curs.execute('''SELECT id, account, basis, quantity FROM position
                             WHERE contract_type = %s LIMIT 1''',
                             (self.id,))
                if curs.rowcount == 0:
                    break
                (pid, account, basis, quantity) = curs.fetchone()
                total += quantity
                position_side = False
                if quantity > 0:
                    position_side = True
                quantity = abs(quantity)
                if ((position_side and side) or ((not position_side) and (not side))):
                    # Winner
                    # Oracle fee is 10% of the profit, rounded to the nearest token, minimum 1 token.
                    fee_tokens = ((quantity * 1000 - basis) * 0.1)/1000
                    fee = 1000 * max(1, round(fee_tokens))
                    payout = max(0, quantity * 1000 - fee)
                    curs.execute("UPDATE account SET balance = balance + %s WHERE id = %s",
                                 (payout, account))
                    self.db.messages.add('contract_resolved', account, self, side=position_side,
                                         price=1000, quantity=payout/1000)
                else:
                    # Loser.
                    self.db.messages.add('contract_resolved', account, self, side=position_side,
                                         price=0, quantity=quantity)
                # Done with this position, delete it.
                curs.execute("DELETE from position WHERE id = %s", (pid,))
            # Done with all positions.  Total is always 0.
            if total != 0:
                raise RuntimeError
            result = self.db.messages.flush(curs)
            curs.connection.commit()

        self.db.cleanup(contract_types=[self])
        return result

# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
