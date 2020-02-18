#!/usr/bin/env python3

class Account(object):

    def __init__(self, uid=None, system=False, banker=False, oracle=False,
                 enabled=True, balance=0, host=None, sub=None,
                 username=None, profile=None, db=None):
        if balance != int(balance):
            raise RuntimeError
        self.db = db
        self.id = uid
        self.system = system
        self.banker = banker
        self.oracle = oracle
        self.enabled = enabled
        self._balance = balance
        self.host = host
        if sub:
            self.sub = str(sub)
        else:
            self.sub = None
        self.username = username
        self.profile = profile
        if self.host is None or self.sub is None:
            return
        # FIXME account permissions stuff
        if self.host == 'GitHub' and int(self.sub) == 48007:
            self.banker = True
            self.oracle = True
        if self.host == 'GitHub' and int(self.sub) == 29267677:
            self.banker = True
            self.oracle = True

    def __repr__(self):
        return "Account %d (%s %s) balance %d" % (self.id, self.host, self.sub, self._balance)

    def __eq__(self, other):
        if self.id and other.id:
            if self.id == other.id:
                return True
            else:
                return False
        if self.host != other.host or self.sub != other.sub:
            return False
        if self.username != other.username or self.profile != other.profile:
            return False
        if self.system != other.system or self.banker != other.banker or self.oracle != other.oracle:
            return False
        if self.enabled != other.enabled:
            return False
        return True
        
    def persist(self, db=None):
        if db:
            self.db = db
        if self._balance != int(self._balance):
            raise RuntimeError
        with db.conn.cursor() as curs:
            if self.id is not None:
                curs.execute('''UPDATE account SET system = %s, banker = %s, oracle = %s,
                              enabled = %s, balance = %s WHERE id = %s''',
                    (self.system, self.banker, self.oracle, self.enabled, self._balance, self.id))
            else:
                curs.execute('''INSERT INTO account (system, banker, oracle, enabled, balance)
                                VALUES (%s, %s, %s, %s, %s) RETURNING id''',
                    (self.system, self.banker, self.oracle, self.enabled, self._balance))
                self.id = curs.fetchone()[0]
            if self.host is not None or self.sub is not None:
                if self.host is None or self.sub is None:
                    raise RuntimeError
                if self.username is None or self.profile is None:
                    curs.connection.rollback()
                    return None
                curs.execute('''INSERT INTO userid (account, host, sub, username, profile)
                                VALUES (%s, %s, %s, %s, %s) ON CONFLICT (host, sub) DO
                                UPDATE SET account = %s, host = %s, sub = %s, username = %s, profile = %s''',
                                (self.id, self.host, self.sub, self.username, self.profile,
                                self.id, self.host, self.sub, self.username, self.profile))
            db.messages.add('new_account', text="New account %s created: %s %s" % (self.id, self.host, self.sub))
            db.messages.flush(curs)
            curs.connection.commit()
        return self

    @property
    def display_balance(self):
        "Balance in whole tokens, for UI."
        return self.balance/1000

    @property
    def display_date(self):
        "Current date/time"
        assert(self.db)
        return self.db.now().strftime("%d %b %H:%M")

    @property
    def balance(self):
        "Balance in millitokens."
        # If a freshly looked up user, then the private _balance will be populated
        # and db will be None.  FIXME: this should be clearer.
        if not self.db:
            return self._balance
        with self.db.conn.cursor() as curs:
            curs.execute("SELECT balance FROM account WHERE id = %s",
                (self.id,))
            return curs.fetchone()[0]

    @property
    def total(self):
        total = 0
        with self.db.conn.cursor() as curs:
            curs.execute("SELECT balance FROM account WHERE id = %s",
                (self.id,))
            total = curs.fetchone()[0]
            curs.execute("SELECT price, quantity FROM offer WHERE account = %s AND side = %s",
                (self.id, self.db.FIXED))
            for row in curs.fetchall():
                (p, q) = row
                total += p * q
            curs.execute("SELECT price, quantity FROM offer WHERE account = %s AND side = %s",
                (self.id, self.db.UNFIXED))
            for row in curs.fetchall():
                (p, q) = row
                total += (1000 - p) * q
        return total

    @classmethod
    def get_by_oauth(cls, curs, host, sub, db=None):
        curs.execute('''SELECT account.id, enabled, balance, username, profile, banker, oracle
                        FROM account JOIN userid ON account.id = userid.account
                        WHERE userid.host = %s AND userid.sub = %s''',
                        (host, sub))
        if curs.rowcount == 1:
            (uid, enabled, balance, username, profile, banker, oracle) =\
                curs.fetchone()
            return cls(uid=uid, banker=banker, oracle=oracle, enabled=enabled, balance=balance,
                       host=host, sub=sub, username=username, profile=profile, db=db)
        elif curs.rowcount == 0:
            return None
        else:
            raise RuntimeError

    @classmethod
    def lookup(cls, db, host, sub, username=None, profile=None):
        '''
        Look up an account. If it doesn't exist, create it.
        If username or profile are different, update them.
        '''
        sub = str(sub)
        with db.conn.cursor() as curs:
            do_persist = False
            acct = cls.get_by_oauth(curs, host, sub, db)
            if acct is None:
                if username is None or profile is None:
                    logging.warning("No username or profile for %s" % sub)
                    return None
                acct = cls(host=host, sub=sub, username=username, profile=profile)
                acct.persist(db)
                curs.connection.commit()
                return acct
            # update username and/or profile if they have changed.
            if username and username != acct.username:
                acct.username = username
                do_persist = True
            if profile and profile != acct.profile:
                acct.profile = profile
                do_persist = True
            if do_persist:
                acct.persist(db)
                curs.connection.commit()
            acct.db = db
            return acct

# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
