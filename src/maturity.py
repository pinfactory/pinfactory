#!/usr/bin/env python3

from datetime import datetime, timedelta, timezone
import logging

import psycopg2


# Maturity has an id to help to join it to other tables. See schema.sql.
class Maturity(object):
    def __init__(self, maturity, mid=None):
        self.db = None
        try:
            self.id = int(mid)
        except TypeError:
            self.id = None
        maturity = maturity.replace(tzinfo=timezone.utc)
        self.maturity = maturity

    # When resolving we need to compare maturities to see all contracts that
    # have the same maturation, and so forth.
    def __eq__(self, other):
        # self.maturity = self.maturity.replace(tzinfo=timezone.utc)
        # other.maturity = other.maturity.replace(tzinfo=timezone.utc)
        if self.id and other.id and self.id != other.id:
            return False
        return self.maturity == other.maturity

    def __repr__(self):
        return "maturity %d at %s" % (self.id, self.display)

    # User never sees the maturity id (for internal db operations). They just see the
    # time and associated contract.
    @property
    def display(self):
        return self.maturity.strftime("%d %b")

    @property
    def tzinfo(self):
        return self.maturity.tzinfo

    # Find expiration dates after the current date/time.
    @classmethod
    def next_expiration_after(cls, when):
        "Next available expiration datetime, after the datetime given"
        # ISO Saturday = 6
        when = datetime(year=when.year, month=when.month, day=when.day)
        while True:
            when = when + timedelta(days=1)
            (weeknum, weekday) = when.isocalendar()[1:]
            if weeknum % 2 == 0 and weekday == 6:
                return when

    # Ensure there are 3 possible maturity times to choose from.
    @classmethod
    def make_upcoming(cls, db):
        result = []
        when = db.now()
        for i in range(3):
            when = cls.next_expiration_after(when)
            result.append(cls(when).persist(db))
        return result

    def persist(self, db):
        with db.conn.cursor() as curs:
            curs.execute("SELECT id FROM maturity WHERE matures = %s", (self.maturity,))
            if curs.rowcount == 1:
                self.id = curs.fetchone()[0]
                return self
            curs.execute(
                """INSERT INTO maturity (matures) VALUES (%s)
                            RETURNING id, matures""",
                (self.maturity,),
            )
            (self.id, self.matures) = curs.fetchone()
            curs.connection.commit()
            return self

    @classmethod
    def available(cls, db):
        result = []
        with db.conn.cursor() as curs:
            curs.execute(
                "SELECT matures, id FROM maturity WHERE matures > NOW() ORDER BY matures"
            )
            for row in curs.fetchall():
                result.append(cls(*row))
        return result

    @classmethod
    def cleanup(cls, db):
        expired = []
        with db.conn.cursor() as curs:
            curs.execute("SELECT id FROM maturity WHERE matures < NOW()")
            for row in curs.fetchall():
                expired.append(row[0])
        for mid in expired:
            try:
                with db.conn.cursor() as curs:
                    curs.execute("DELETE FROM maturity WHERE id = %s", (mid,))
                    db.conn.commit()
            except psycopg2.errors.ForeignKeyViolation:
                db.conn.rollback()
