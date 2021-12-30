# Main entry function into the marketplace once setup is complete.

#!/usr/bin/env python3

from datetime import timezone
import logging
import os
import signal
import subprocess
import sys
import time

try:
    import psycopg2
except:
    print("This needs to be run on the server or container with Python dependencies installed.")
    sys.exit(0)

import config
from account import Account
from contract import Contract, ContractType, Issue, Maturity
from export import dump_csv
from graph import Graph
from message import Message, MessageList
from offer import Offer
from position import Position

def pg_version():
    for ent in os.listdir('/var/lib/postgresql'):
        try:
            float(ent)
            return ent
        except:
            pass

class Market(object):
    FIXED = True
    UNFIXED = False

    # This is the class constructor which gets called when the class is created.
    # Class objects correspond to the concepts -- i.e., contract, position, issue,
    # and so forth. All the "scale or multiples" such as multiple positions,
    # issues, etc are all stored in the database. This makes it much leaner and
    # faster to scale. The database can only be accessed through the market class
    # to ensure 1-1 correspondence (each market has only 1 database). The connect
    # function below gives you a database connection object. This is the object
    # you need to perform sql queries into the database (retrieve or input data).
    def __init__(self, applog=None, start_demo_db=False):
        global logging
        if applog is not None:
            logging = applog
        self.logging = logging
        self.system_id = None
        self.messages = MessageList(self)
        self.contract_type = ContractType
        self.contract_type.db = self
        self.offer = Offer
        self.offer.db = self
        self.position = Position
        self.position.db = self
        self.history = Message
        self.history.db = self
        self.graph = Graph
        self.graph.db = self
        self.demo_db_pid = None
        self.time_offset = 0
        if start_demo_db:
            self.start_demo_db()
        self.connect()
        with self.conn.cursor() as curs:
            curs.execute("SELECT id FROM account WHERE system = true")
            self.system_id = int(curs.fetchone()[0])

    def connect(self):
        for i in range(5):
            try:
                self.conn = psycopg2.connect(database=config.DB_NAME, user=config.DB_USER, host=config.DB_HOST, port=config.DB_PORT)
                if i > 0:
                    logging.info("Connected to database after %d attempt(s)." % i)
                break
            except psycopg2.OperationalError:
                logging.info("Waiting for database.")
                time.sleep(2**(i+3))
        else:
            logging.error("Database connection failed")
            raise RuntimeError

    def start_demo_db(self):
        version = pg_version()
        try:
            psycopg2.connect(database=config.DB_NAME, user=config.DB_USER, host=config.DB_HOST, port=config.DB_PORT)
            return
        except psycopg2.OperationalError:
            pass
        demo_db = subprocess.Popen(["/usr/bin/sudo", "-u", "postgres", "/usr/bin/faketime", "-f",
                                    "+%ds" % self.time_offset,
                                    "/usr/lib/postgresql/%s/bin/postgres" % version,
                                    "-D", "/var/lib/postgresql/%s/main" % version,
                                    "-c", "config_file=/etc/postgresql/%s/main/postgresql.conf" % version],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info("Started test database version %s. PID is %d, time offset %d seconds" % (version, demo_db.pid, self.time_offset))

    def stop_demo_db(self):
        self.conn.close()
        version = pg_version()
        try:
            with open("/var/lib/postgresql/%s/main/postmaster.pid" % version) as pidfile:
                pidline = pidfile.readline()
            os.kill(int(pidline), signal.SIGKILL)
            logging.info("Waiting for test database to shut down.")
            time.sleep(1)
        except ProcessLookupError:
            pass

        while True:
            try:
                psycopg2.connect(database=config.DB_NAME, user=config.DB_USER, host=config.DB_HOST, port=config.DB_PORT)
            except:
                return

    def time_jump(self, seconds):
        if seconds < 0:
            raise NotImplementedError
        self.stop_demo_db()
        self.time_offset += seconds
        self.start_demo_db()
        self.connect()

    def now(self):
        with self.conn.cursor() as curs:
            curs.execute("SELECT NOW()")
            when = curs.fetchone()[0]
            when = when.replace(tzinfo=timezone.utc)
            return when

    def fund_test_users(self):
        with self.conn.cursor() as curs:
            curs.execute("UPDATE account set balance = balance + 10000000 WHERE balance < 10000000")
            curs.connection.commit()

    def lookup_user(self, host, sub, username=None, profile=None):
        # FIXME Transaction management
        try:
            return Account.lookup(self, host, sub, username, profile)
        except Exception as e:
            logging.warning(e)
            os._exit(0)

    def cleanup(self, contract_types=[]):
        Offer.cleanup(self, contract_types)
        ContractType.cleanup(contract_types)
        Maturity.cleanup(self)
        Issue.cleanup(self)

    def add_issue(self, user, issue_url):
        return Issue(url=issue_url).persist(self)

    def get_issues(self, include_private=False):
        return list(Issue.get_all(self, include_private))

    def issue_by_id(self, iid):
        return Issue.by_id(self, iid)

    def issue_by_url(self, url, title=None, is_open=True):
        return Issue.by_url(self, url, title, is_open)

    def place_order(self, user, iid, mid, side, price, quantity):
        result = []
        ctype = self.contract_type.lookup(iid, mid)
        messages = Offer(user, ctype, side, price, quantity).place()
        for message in messages:
            if message.account == user.id:
                result.append(message)
        return result

    def setup(self):
        Maturity.make_upcoming(self)

    def maturities(self):
        return Maturity.available(self)

    def ticker_csv(self):
        return dump_csv(self).getvalue()

# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
