#!/usr/bin/env python3

# Issue closed means that the issue is fixed. Issue open means that its status
# remains unfixed even though there may be contracts/positions on the issue. Anyone
# else can still bid on it.

from datetime import timedelta

import psycopg2


class Issue(object):
    def __init__(
        self,
        iid=None,
        modified=None,
        url=None,
        title=None,
        is_open=True,
        offer_volume=0,
    ):
        self.db = None
        if iid:
            self.id = int(iid)
        self.modified = modified
        self.is_open = is_open
        self.fixed = None
        self.url = url
        self.title = title
        self.new = False
        self.action_button = ""
        self.offer_volume = offer_volume

    def __eq__(self, other):
        "Compare content of two issues"
        return (
            self.id == other.id
            and self.url == other.url
            and self.title == other.title
            and self.is_open == other.is_open
        )

    def __repr__(self):
        return self.displayname

    @property
    def datetime(self):
        return self.modified.strftime("%d %b %H:%M")

    # Return issue name or issue number within project name or just url.
    # Array parts[] assumes github convention to handle issue urls.
    @property
    def displayname(self):
        if self.title is not None:
            return self.title
        parts = self.url.split("/")
        try:
            return "Issue %d in project %s" % (int(parts[6]), parts[4])
        except:
            return self.url

    @property
    def projectname(self):
        parts = self.url.split("/")
        try:
            return parts[4]
        except:
            return self.url

    @property
    def issuenumber(self):
        parts = self.url.split("/")
        try:
            return int(parts[-1])
        except:
            return 0

    # Locking out simple-market from public view.
    @property
    def is_public(self):
        if self.projectname == "simple-market":
            return False
        return True

    # Writes the status of an issue to the database. xmax resolves the ON CONFLICT
    # statement in Postgres: logs whether the issue is created or updated.
    # The value of xmax is placed in "inserted".
    def persist(self, db):
        self.db = db
        with db.conn.cursor() as curs:
            curs.execute(
                """INSERT INTO issue (url, title, open) VALUES (%s, %s, %s)
                          ON CONFLICT (url) DO UPDATE SET open = %s
                          RETURNING (xmax = 0), id, title,
                          modified, fixed""",
                (self.url, self.title, self.is_open, self.is_open),
            )
            (inserted, self.id, oldtitle, self.modified, self.fixed) = curs.fetchone()
            if self.title is None:
                self.title = oldtitle
            else:
                curs.execute(
                    """UPDATE issue SET title = %s WHERE id = %s""",
                    (self.title, self.id),
                )
            if inserted:
                text = "Issue created: %s" % self.url
                self.new = True
            else:
                text = "Issue updated: %s" % self.url
            self.db.messages.add(mclass="system", text=text)
            self.db.messages.flush(curs)
            curs.connection.commit()
        return self

    @classmethod
    def by_id(cls, db, iid):
        with db.conn.cursor() as curs:
            curs.execute(
                "SELECT url, title, modified, open FROM issue WHERE id = %s", (iid,)
            )
            if not curs.rowcount:
                return None
            (url, title, modified, is_open) = curs.fetchone()
            return cls(
                iid=iid, modified=modified, url=url, title=title, is_open=is_open
            )

    @classmethod
    def get_all(cls, db, include_private=False):
        with db.conn.cursor() as curs:
            curs.execute(
                """SELECT issue.id, issue.modified, issue.url, issue.title, issue.open,
                            SUM(offer.quantity)
                            FROM issue LEFT OUTER JOIN contract_type ON contract_type.issue = issue.id
                            LEFT OUTER JOIN offer ON offer.contract_type = contract_type.id
                            GROUP BY issue.id
                            ORDER BY SUM(offer.quantity) DESC NULLS LAST,
                            open DESC,
                            modified DESC"""
            )
            for row in curs.fetchall():
                (iid, modified, url, title, is_open, volume) = row
                tmp = cls(
                    iid=iid,
                    modified=modified,
                    url=url,
                    title=title,
                    is_open=is_open,
                    offer_volume=volume,
                )
                if include_private or tmp.is_public:
                    yield (tmp)

    @classmethod
    def by_url(cls, db, url, title=None, is_open=True):
        return cls(url=url, title=title, is_open=is_open).persist(db)

    # Any issue that has been around for 4 weeks and has no trading history gets cleaned
    # up.
    @classmethod
    def cleanup(cls, db):
        expired = []
        with db.conn.cursor() as curs:
            when = db.now() - timedelta(weeks=4)
            curs.execute("SELECT id FROM issue WHERE modified < %s", (when,))
            for row in curs.fetchall():
                expired.append(row[0])
        for mid in expired:
            try:
                with db.conn.cursor() as curs:
                    curs.execute("DELETE FROM issue WHERE id = %s", (mid,))
                    db.conn.commit()
            except psycopg2.errors.ForeignKeyViolation:
                db.conn.rollback()
