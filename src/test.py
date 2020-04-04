#!/usr/bin/env python3

from datetime import timedelta, timezone
import logging
import signal
import sys
import time
import unittest
import uuid

try:
    import psycopg2
except:
    print("This should be run on the server or container with Python dependencies installed.")
    print("To start the container and run tests, use test.sh")
    sys.exit(0)

from market import Market, Account, Issue, Maturity

class BogusObject(object):
    def __init__(self):
        self.id = 90210

class MarketTestCase(unittest.TestCase):

    @staticmethod
    def make_contract_type(testdb, when=None):
        "Helper function to make a contract type for testing"
        if when is None:
            when = testdb.now() + timedelta(weeks=1)
        testissue = Issue(url='http://bug.example.com/%s/' % uuid.uuid4()).persist(testdb)
        testmaturity = Maturity(when).persist(testdb)
        return testdb.contract_type(testissue, testmaturity).persist()

    def test_db_time(self):
        '''
        Sanity test: is the time on the database close to the time in the application?
        '''
        testdb = Market()
        from datetime import datetime
        self.assertAlmostEqual(testdb.now().timestamp(), datetime.now().timestamp(), delta = 0.2)

    def test_time_jump(self):
        '''
        Sanity test: is the time on the database close to the time in the application?
        '''
        return None
        ff_seconds = 7 * 24 * 60 * 60
        testdb = Market(start_demo_db=True)
        from datetime import datetime
        self.assertAlmostEqual(testdb.now().timestamp(), datetime.now().timestamp(), delta = 0.2)
        testdb.time_jump(ff_seconds)
        self.assertAlmostEqual(testdb.now().timestamp(), datetime.now().timestamp() + ff_seconds, delta = 0.2)

    def test_q_and_refund(self):
        '''
        Arguments: old quantity, new contract (UNFIXED is negative)
        Returns: tuple (new quantity, refund due)
        '''
        from market import Contract
        con = Contract
        self.assertEqual(con.q_and_refund(0,0), (0,0))
        self.assertEqual(con.q_and_refund(-10,10), (0,10))
        self.assertEqual(con.q_and_refund(-10,4), (-6,4))
        self.assertEqual(con.q_and_refund(-1,10), (9,1))
        self.assertEqual(con.q_and_refund(0,20), (20,0))

    def test_filter_messages(self):
        "Users only get their own messages when filtered."
        testdb = Market()
        from market import MessageList
        user1 = Account(balance=1000000).persist(testdb)
        user2 = Account(balance=1000000).persist(testdb)
        mlist = MessageList()
        mlist.add("info", user1.id, text="user1 text")
        mlist.add("info", user2.id, text="user2 text")
        result1 = mlist.filter(account=user1)
        self.assertEqual(1, len(result1))
        self.assertEqual("user1 text", result1[0].text)
        result2 = mlist.filter(account=user2)
        self.assertEqual(1, len(result2))
        self.assertEqual("user2 text", result2[0].text)

    def test_no_negative_balance_account(self):
        "An account's balance must be non-negative."
        testdb = Market()
        with self.assertRaises(psycopg2.errors.CheckViolation):
            Account(balance = -1).persist(testdb)

    def test_no_fractional_balance_account(self):
        "An account's balance must be an integer."
        testdb = Market()
        with self.assertRaises(RuntimeError):
            Account(balance = 3.14159).persist(testdb)

    def test_persist_and_lookup_account(self):
        "We can persist an account to the database and get the same account back."
        testdb = Market()
        testuser = Account(host="GitHub", sub=31337, username="jrdobbs", profile="https://bob.dobbs/")
        testuser = testuser.persist(testdb)
        uid = testuser.id
        testuser = testuser.persist(testdb)
        self.assertEqual(uid, testuser.id)
        market = Market()
        founduser = market.lookup_user('GitHub', 31337)
        self.assertEqual(testuser, founduser)

    def test_update_account(self):
        "Updating an account's username and profile works."
        testdb = Market()
        testuser = testdb.lookup_user(host="GitHub", sub=31337, username="jrdobbs", profile="https://bob.dobbs/")
        sameuser = testdb.lookup_user(host="GitHub", sub=31337)
        self.assertEqual('https://bob.dobbs/', sameuser.profile)
        testuser = testdb.lookup_user(host="GitHub", sub=31337, username="bob", profile="https://bob.dobbs/")
        sameuser2 = testdb.lookup_user(host="GitHub", sub=31337)
        self.assertEqual(testuser, sameuser)
        self.assertEqual('https://bob.dobbs/', sameuser2.profile)
        self.assertEqual('bob', sameuser2.username)

    def test_malformed_account(self):
        "An account that has a host must also have a uid on that host (OAuth 'sub')"
        testdb = Market()
        testuser = Account(host="GitHub")
        with self.assertRaises(RuntimeError):
            testuser = testuser.persist(testdb)

    def test_add_issue(self):
        "Create an issue with timestamp."
        testdb = Market()
        testissue = Issue(url='http://bug.example.com/%s/' % uuid.uuid4()).persist(testdb)
        testissue.modified = testissue.modified.replace(tzinfo=timezone.utc)
        self.assertIsNotNone(testissue.id)
        self.assertFalse(testissue.fixed)
        self.assertLess(testissue.modified, testdb.now())
        self.assertGreater(testissue.modified, testdb.now() - timedelta(minutes=1))

    def test_lookup_issue(self):
        "Create an issue and update the title."
        testdb = Market()
        url = 'http://bug.example.com/%s/' % uuid.uuid4()
        testdb.issue_by_url(url, 'fix the thing')
        test_issue = testdb.issue_by_url(url)
        self.assertEqual('fix the thing', test_issue.title)

        url2 = 'http://bug.example.com/%s/' % uuid.uuid4()
        testdb.issue_by_url(url2)
        testdb.issue_by_url(url2, 'fix the thing again')
        test_issue_2 = testdb.issue_by_url(url2)
        self.assertEqual('fix the thing again', test_issue_2. title)

    def test_add_dup_issue(self):
        '''
        Issue URLs are unique.  Attempting to persist the same URL twice will
        update the existing record.
        '''
        testdb = Market()
        issue_a = Issue(url='http://bug.example.com/1/').persist(testdb)
        issue_b = Issue(url='http://bug.example.com/1/').persist(testdb)
        self.assertEqual(issue_a, issue_b)

    def test_add_maturity(self):
        '''
        Maturity dates are unique. If you make the same maturity twice it
        will have the same id.
        '''
        testdb = Market()
        when = testdb.now() + timedelta(weeks=1)
        testmaturity = Maturity(when).persist(testdb)
        self.assertEqual(testmaturity.maturity, when)
        dup_maturity = Maturity(when).persist(testdb)
        self.assertEqual(testmaturity, dup_maturity)

    def test_add_upcoming_maturities(self):
        "Contracts expire at the beginning of the day Saturday GMT"
        testdb = Market()
        result = Maturity.make_upcoming(testdb)
        for i in range(len(result) - 1):
            self.assertEqual(result[i].maturity + timedelta(days=14), result[i+1].maturity)
        Maturity.make_upcoming(testdb)
        Maturity.available(testdb) # FIXME check that all newly created ones are there

    def test_add_contract_type(self):
        "Contract types are unique."
        testdb = Market()
        when = testdb.now() + timedelta(weeks=1)
        testissue = Issue(url='http://bug.example.com/1337/').persist(testdb)
        testmaturity = Maturity(when).persist(testdb)
        testdb.contract_type(testissue, testmaturity).persist()
        with self.assertRaises(psycopg2.errors.UniqueViolation):
            testdb.contract_type(testissue, testmaturity).persist()

    def test_lookup_contract_type(self):
        "Looking up the same contract type produces the same result"
        testdb = Market()
        when = testdb.now() + timedelta(weeks=1)
        testmaturity = Maturity(when).persist(testdb)
        testissue = Issue(url='http://bug.example.com/%s/' % uuid.uuid4()).persist(testdb)
        test_ctype_a = testdb.contract_type.lookup(testissue.id, testmaturity.id)
        test_ctype_b = testdb.contract_type.lookup(testissue.id, testmaturity.id)
        self.assertEqual(test_ctype_a, test_ctype_b)

    def test_contract_type_data(self):
        "Looking up a contract type produces the right values."
        testdb = Market() 
        when = testdb.now() + timedelta(weeks=1)
        testissue = Issue(url='http://bug.example.com/%s/' % uuid.uuid4()).persist(testdb)
        testmaturity = Maturity(when).persist(testdb)
        orig = testdb.contract_type(testissue, testmaturity).persist()
        fetched = testdb.contract_type.lookup(testissue.id, testmaturity.id)
        self.assertEqual(orig, fetched)

    def test_resolve_and_re_add_contract_type(self):
        "Contract types can be recreated."
        testdb = Market()
        when = testdb.now() + timedelta(weeks=1)
        testissue = Issue(url='http://bug.example.com/90210/').persist(testdb)
        testmaturity = Maturity(when).persist(testdb)
        test_contract_type = testdb.contract_type(testissue, testmaturity).persist()
        test_contract_type.resolve(True)
        testdb.contract_type(testissue, testmaturity).persist()
        test_contract_type.resolve(True)

    def test_add_offer(self):
        "We can add a good offer and fail to add a bad offer."
        testdb = Market()
        testuser = Account(balance=1000000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)
        good_test_offer = testdb.offer(testuser, test_contract_type, Market.FIXED, 500, 100)
        msglist = good_test_offer.place()
        result = testdb.offer.filter(issue=test_contract_type.issue)
        self.assertEqual(good_test_offer.contract_type.maturity.maturity, 
                         result[0].contract_type.maturity.maturity)
        user_messages = testdb.history.filter(account=testuser)
        self.assertEqual(1, len(user_messages))
        self.assertEqual(msglist[0].id, user_messages[0].id)
        self.assertEqual(good_test_offer, testdb.offer.filter(account=testuser)[0])
        with self.assertRaises(psycopg2.errors.CheckViolation):
            testdb.offer(testuser, test_contract_type, Market.FIXED, -1, 100).place()

    def test_filter_offers(self):
        "We can add a good offer and fail to add a bad offer."
        testdb = Market()
        start = len(list(testdb.offer.filter()))
        testuser1 = Account(balance=1000000).persist(testdb)
        testuser2 = Account(balance=1000000).persist(testdb)
        test_contract_type_1 = self.make_contract_type(testdb)
        test_contract_type_2 = self.make_contract_type(testdb)
        for acct in (testuser1, testuser2):
            for ctype in (test_contract_type_1, test_contract_type_2):
                testdb.offer(acct, ctype, Market.FIXED, 500, 100).place()
        res = testdb.offer.filter()
        self.assertEqual(4 + start, len(list(res)))
        res = testdb.offer.filter(account=testuser1)
        self.assertEqual(2, len(list(res)))
        res = testdb.offer.filter(issue=test_contract_type_1.issue)
        self.assertEqual(2, len(list(res)))

    def test_lookup_offer_by_id_and_account(self):
        "After we persist an offer we can find it based on its id and on the account that placed it."
        testdb = Market()
        testuser = Account(balance=1000000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)
        test_offer = testdb.offer(testuser, test_contract_type, Market.FIXED, 500, 100)
        messages = test_offer.place()
        oid = messages[0].offer.id
        market = Market()
        found_offer = market.offer.by_id(oid)
        self.assertEqual(test_offer, found_offer)
        issue_offer = market.offer.filter(issue=test_contract_type.issue)[0]
        self.assertEqual(test_offer, issue_offer)
        account_offer = testdb.offer.filter(account=testuser)[0]
        self.assertEqual(test_offer, account_offer)
        both_offer = market.offer.filter(issue=test_contract_type.issue, account=testuser)[0]
        self.assertEqual(test_offer, both_offer)

    def test_add_multiple_offers(self):
        testdb = Market()
        testuser = Account(balance=10000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)
        testdb.offer(testuser, test_contract_type, Market.FIXED, 100, 5).place()
        self.assertEqual(testuser.total, 10000)
        testdb.offer(testuser, test_contract_type, Market.FIXED, 200, 5).place()
        self.assertEqual(testuser.total, 10000)
        test_contract_type.resolve(True)
        self.maxDiff = None
        lines = testdb.ticker_csv().splitlines()
        for line in lines:
            if not test_contract_type.issue.url in line:
                continue
            (created, url, matures, mclass, side, price, quantity) = line.split(',')
            self.assertEqual(test_contract_type.issue.url, url)

    def test_add_and_cancel_offer(self):
        testdb = Market()
        testuser = Account(balance=1000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)
        mlist = testdb.offer(testuser, test_contract_type, Market.FIXED, 100, 10).place()
        self.assertEqual(testuser.total, 1000)
        offer1 = mlist[0].offer
        offer1.cancel()
        self.assertEqual(0, len(list(testdb.offer.filter(account=testuser))))
        self.assertEqual(testuser.total, 1000)
        testdb.offer(testuser, test_contract_type, Market.FIXED, 100, 10).place()
        self.assertEqual(testuser.total, 1000)

    def test_place_offer_and_cancel_offer_from_new_session(self):
        testdb = Market()
        testuser = testdb.lookup_user('GitHub', 1, 'joe', 'https://example.org/')
        self.assertIsNotNone(testuser.id)
        testdb.fund_test_users()
        test_contract_type = self.make_contract_type(testdb)
        mlist = testdb.offer(testuser, test_contract_type, Market.FIXED, 100, 10).place()
        placed = mlist[0].offer
        market = Market()
        user = market.lookup_user('GitHub', 1)
        self.assertEqual(testuser, user)
        offer = market.offer.by_id(placed.id)
        self.assertEqual(placed, offer)
        offer2 = market.offer.filter(account=testuser)[0]
        self.assertEqual(offer, offer2)
        self.assertEqual(offer.account, user)
        mlist = offer.cancel(user=user)
        self.assertEqual(1, len(mlist))
        self.assertEqual(placed, mlist[0].offer)
        gone = market.offer.by_id(placed.id)
        self.assertIsNone(gone)

    def test_add_oversized_offer(self):
        testdb = Market()
        testuser = Account(balance=100).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)
        with self.assertRaises(psycopg2.errors.CheckViolation):
            testdb.offer(testuser, test_contract_type, Market.FIXED, 999, 20000).place()

    def test_fail_zero_offer(self):
        testdb = Market()
        testuser = Account(balance=10000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)
        with self.assertRaises(psycopg2.errors.CheckViolation):
            testdb.offer(testuser, test_contract_type, Market.FIXED, 0, 0).place()

    def test_fail_add_late_offer(self):
        "An offer cannot be placed after the contract type's maturity date."
        testdb = Market()
        testuser = Account(balance=10000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb, when = testdb.now() - timedelta(seconds=1))
        with self.assertRaises(psycopg2.errors.RaiseException):
            testdb.offer(testuser, test_contract_type, Market.FIXED, 100, 100).place()

    def test_fail_late_contract(self):
        "A contract cannot be formed after the contract type's maturity date."
        testdb = Market()
        testuser = Account(balance = 9000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb, when = testdb.now() + timedelta(seconds=1))
        self.assertIsNotNone(test_contract_type.id)
        testdb.offer(testuser, test_contract_type, Market.UNFIXED, 100, 10).place()
        time.sleep(4)
        testfixer = Account(balance = 1000).persist(testdb)
        with self.assertRaises(psycopg2.errors.RaiseException):
            testdb.offer(testfixer, test_contract_type, Market.FIXED, 100, 10).place()

    def test_add_bogus_offer(self):
        "Don't allow offers that don't match a contract type."
        testdb = Market()
        with self.assertRaises(psycopg2.errors.ForeignKeyViolation):
            testdb.offer(BogusObject(), BogusObject(), Market.FIXED, 500, 100).place()

    def test_cleanup(self):
        "Offers, maturities, and contract types are removed from the database on cleanup."
        testdb = Market()
        testuser = Account(balance=10000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb, when = testdb.now() + timedelta(seconds=1))
        testdb.offer(testuser, test_contract_type, Market.FIXED, 100, 10).place()
        self.assertEqual(9000, testuser.balance)
        self.assertEqual(1, len(list(testdb.offer.filter(account=testuser))))
        before_maturities = list(Maturity.available(testdb))
        for m in before_maturities:
            if m.maturity == test_contract_type.maturity.maturity:
                break
        else:
            raise NotImplementedError # FIXME look up the right error here
        time.sleep(1)
        testdb = Market()
        testdb.cleanup()
        self.assertEqual(0, len(list(testdb.offer.filter(account=testuser))))
        after_maturities = list(Maturity.available(testdb))
        for m in after_maturities:
            if m.maturity == test_contract_type.maturity.maturity:
                raise NotImplementedError
        testuser._balance = None
        self.assertEqual(10000, testuser.balance)

    def test_add_matching_offers_user_first(self):
        '''
        This is an example of a use case narrative as a test.  We want to be able to show that
        the software's behavior matches our user stories, and that we don't introduce any
        incorrect market behavior when we change anything.

        Let's say you're a h8r and believe that a bug is 90% likely to go unfixed.  Or you're
        a user and you are willing to accept a loss of 90 tokens to see a bug get fixed by a
        developer who puts up 10.  It's all the same to the market.
        
        So you make an Offer with a price of 100 (remember, that's the price of the fixed side)
        and a quantity of 100 units.  The winner will end up with 100,000 millitokens.  You are
        putting up 900 * 100 = 90,000 of that.  The developer (or front-runner betting that the
        developer will fix it for free lol) puts up 100 * 100 = 10,000 millitokens.

        The system forms a contract as soon as the developer puts in their offer.
        '''

        # Set up the prerequisites for the test: two accounts, one user and one fixer,
        # and a contract type to trade on.
        testdb = Market()
        testuser = Account(balance = 9000).persist(testdb)
        testfixer = Account(balance = 1000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        # create the user offer: the side is UNFIXED, the price is 100, the quantity is 10 units.
        user_offer = testdb.offer(testuser, test_contract_type, Market.UNFIXED, 100, 10)

        # Place the user offer and receive a one-item message list. The message states that
        # the offer has been placed.  And the offer exists in the market database.
        mlist = user_offer.place()
        self.assertEqual(1, len(mlist))
        self.assertEqual(('offer_created', testuser.id, Market.UNFIXED, 100, 10),
                         (mlist[0].mclass, mlist[0].account, mlist[0].side, mlist[0].price, mlist[0].quantity))
        self.assertTrue(user_offer.exists)

        # The test user put all 9000 of their millitokens into this offer, because they are
        # buying the UNFIXED side of a contract with a price of 100.  So their balance is 0.
        # The "total" includes account balance plus cancellable offers, and is equal to the value
        # of the user's one offer.
        self.assertEqual(0, testuser.balance)
        self.assertEqual(9000, testuser.total) 

        # Now place the fixer offer. This time, two messages will be returned because both
        # sides receive a message that the contract has been formed.
        fixer_offer = testdb.offer(testfixer, test_contract_type, Market.FIXED, 100, 10)
        mlist = fixer_offer.place()
        self.assertEqual(2, len(mlist))
        self.assertEqual(('contract_created', testfixer.id, Market.FIXED, 100, 10),
                         (mlist[0].mclass, mlist[0].account, mlist[0].side, mlist[0].price, mlist[0].quantity))
        self.assertEqual(('contract_created', testuser.id, Market.UNFIXED, 100, 10),
                         (mlist[1].mclass, mlist[1].account, mlist[1].side, mlist[1].price, mlist[1].quantity))

        # And neither offer remains in the database.  The user offer is gone because it was placed,
        # committed to the database, and then later matched. The fixer offer is not there because it
        # was matched immediately on being placed.
        self.assertFalse(user_offer.exists)
        self.assertFalse(fixer_offer.exists)

        self.assertEqual(0, testfixer.balance)
        fixerposition = testdb.position.filter(account=testfixer)[0]
        self.assertEqual(10, fixerposition.quantity)
        # Now we resolve the contract type as FIXED.
        # The fixer has a profit of 9000 millitokens, and pays an oracle fee of 1 token on the gain (because
        # rounding.)  That means a total payout of 10 tokens minus the fee == 9 tokens.
        msglist = test_contract_type.resolve(True)
        fixer_msgs = msglist.filter(account=testfixer)
        self.assertEqual(fixer_msgs[0].contract_type, test_contract_type)
        self.assertEqual(fixer_msgs[0].side, True)
        self.assertEqual(fixer_msgs[0].quantity, 9)
        self.assertEqual(fixer_msgs[0].price, 1000)
        self.assertEqual(9000, testfixer.balance)
        # And the user received no payout (but got their bug fixed, so yay for them)
        user_msgs = msglist.filter(account=testuser)
        self.assertEqual(user_msgs[0].contract_type, test_contract_type)
        self.assertEqual(user_msgs[0].account, testuser.id)
        self.assertEqual(user_msgs[0].side, False)
        self.assertEqual(user_msgs[0].price, 0)
        self.assertEqual(user_msgs[0].quantity, 10)
        self.assertEqual(0, testuser.balance)

    def test_add_matching_offers_fixer_first(self):
        '''
        Let's say you're a developer who wants to get paid to fix a certain bug, and will put
        up 10 tokens for a total payout of 100 and a profit of 90.  Similar case to the above,
        but the fixer offer goes in first.

        This time the system forms a contract when the user (or h8r) puts in their offer.
        '''

        # same prerequsites
        testdb = Market()
        testuser = Account(balance = 18000).persist(testdb)
        testfixer = Account(balance = 2000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        # create the fixer offer: the side is FIXED, the price is 100, the quantity is 10 units.
        fixer_offer = testdb.offer(testfixer, test_contract_type, Market.FIXED, 100, 20)
                
        # Place the user offer, get a message.
        mlist = fixer_offer.place()
        self.assertEqual(1, len(mlist))
        self.assertEqual(('offer_created', testfixer.id, Market.FIXED, 100, 20),
                         (mlist[0].mclass, mlist[0].account, mlist[0].side, mlist[0].price, mlist[0].quantity))
        
        # Now place the user offer and form the contract. Messages are in the same order as last time.
        user_offer = testdb.offer(testuser, test_contract_type, Market.UNFIXED, 100, 20)
        mlist = user_offer.place()
        self.assertEqual(2, len(mlist))
        self.assertEqual(('contract_created', testfixer.id, Market.FIXED, 100, 20),
                         (mlist[0].mclass, mlist[0].account, mlist[0].side, mlist[0].price, mlist[0].quantity))
        self.assertEqual(('contract_created', testuser.id, Market.UNFIXED, 100, 20),
                         (mlist[1].mclass, mlist[1].account, mlist[1].side, mlist[1].price, mlist[1].quantity))

        # Now resolve the contract.  This time it goes unfixed.
        # The user put in 18000 millitokens and has a profit of 2, 1 of which goes to pay the oracle fee.
        # So the user gets a payout of 19000 and the fixer gets 0.
        test_contract_type.resolve(False)
        self.assertEqual(19000, testuser.balance)
        self.assertEqual(0, testfixer.balance)

    def test_add_part_match_existing(self):
        '''
        In this test, the user offers to buy 80 units of UNFIXED at a contract price of 100.
        The fixer matches 50 units, leaving a remaining offer of 30.
        '''

        # setup
        testdb = Market()
        testuser = Account(balance = 72000).persist(testdb)
        testfixer = Account(balance = 5000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        # Create and place the user offer, check the resulting message.
        user_offer = testdb.offer(testuser, test_contract_type, Market.UNFIXED, 100, 80)
        mlist = user_offer.place()
        self.assertEqual(1, len(mlist))
        self.assertEqual(('offer_created', testuser.id, Market.UNFIXED, 100, 80),
                         (mlist[0].mclass, mlist[0].account, mlist[0].side, mlist[0].price, mlist[0].quantity))

        # The user still has a total of 72000 millitokens because the offer is unmatched.
        self.assertEqual(72000, testuser.total) 

        # Now place the fixer offer and check the contract formed messages.
        fixer_offer = testdb.offer(testfixer, test_contract_type, Market.FIXED, 100, 50)
        mlist = fixer_offer.place()
        self.assertEqual(2, len(mlist))
        self.assertEqual(('contract_created', testfixer.id, Market.FIXED, 100, 50),
                         (mlist[0].mclass, mlist[0].account, mlist[0].side, mlist[0].price, mlist[0].quantity))
        self.assertEqual(('contract_created', testuser.id, Market.UNFIXED, 100, 50),
                         (mlist[1].mclass, mlist[1].account, mlist[1].side, mlist[1].price, mlist[1].quantity))

        # And the user's total is down to 27000 millitokens because 50 units of the offer have been matched.
        self.assertEqual(27000, testuser.total) 

        # The fixer has a total of 0.
        self.assertEqual(0, testfixer.total) 

        # When we resolve this as FIXED, the user is still at 27000 and the fixer gets 46000.
        # Total value of their 50 units is 50 tokens, of which 45 is profit on which the fee
        # applies.  So the fixer gets 50000 millitokens minus a fee of 4000 millitokens.

        test_contract_type.resolve(True)
        self.assertEqual(27000, testuser.total)
        self.assertEqual(46000, testfixer.total) 

    def test_add_part_match_new(self):
        '''
        The user makes an offer with a quantity of 10, then the developer with a
        quantity of 25.  Result is a contract with a quantity of 10, and a FIXED
        offer with a quantity of 15.
        '''

        testdb = Market()
        testuser = Account(balance = 7500).persist(testdb)
        testfixer = Account(balance = 6250).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        testdb.offer(testuser, test_contract_type, Market.UNFIXED, 250, 10).place()
        
        # Now place the fixer offer and check that it is partly matched.
        fixer_offer = testdb.offer(testfixer, test_contract_type, Market.FIXED, 250, 25)
        mlist = fixer_offer.place()
        self.assertEqual(3, len(mlist))
        self.assertEqual(('contract_created', testfixer.id, Market.FIXED, 250, 10),
                         (mlist[0].mclass, mlist[0].account, mlist[0].side, mlist[0].price, mlist[0].quantity))
        self.assertEqual(('contract_created', testuser.id, Market.UNFIXED, 250, 10),
                         (mlist[1].mclass, mlist[1].account, mlist[1].side, mlist[1].price, mlist[1].quantity))
        self.assertEqual(('offer_created', testfixer.id, Market.FIXED, 250, 15),
                         (mlist[2].mclass, mlist[2].account, mlist[2].side, mlist[2].price, mlist[2].quantity))

        # And the fixer's total is down to 2500 millitokens because 10 units have been matched.
        self.assertEqual(3750, testfixer.total) 

    def test_best_price_for_existing_user(self):
        '''
        The user is willing to accept a price of 100 (and put up 900 per unit).  The developer
        is willing to put up 200.  The price is 200.
        '''

        testdb = Market()
        testuser = Account(balance = 9000).persist(testdb)
        testfixer = Account(balance = 2000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        # After placing the offer the user has a 0 balance.
        testdb.offer(testuser, test_contract_type, Market.UNFIXED, 100, 10).place()
        self.assertEqual(9000, testuser.total)
        self.assertEqual(0, testuser.balance)

        fixer_offer = testdb.offer(testfixer, test_contract_type, Market.FIXED, 200, 10)
        mlist = fixer_offer.place()
        self.assertEqual(mlist[1].price, 200) 
        self.assertEqual(0, testfixer.total)

        # User has 1000 back in their balance.
        self.assertEqual(1000, testuser.balance)

    def test_no_contract_for_developer_below_user(self):
        '''
        The user is willing to accept a price of 200 (and put up 800 per unit).  The developer
        is willing to put up 100.  No contract is formed.
        '''

        testdb = Market()
        testuser = Account(balance = 8000).persist(testdb)
        testfixer = Account(balance = 2000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        # After placing the offer the user has a 0 balance.
        testdb.offer(testuser, test_contract_type, Market.UNFIXED, 200, 10).place()
        self.assertEqual(0, testuser.balance)

        # The developer's offer is placed but not matched.
        fixer_offer = testdb.offer(testfixer, test_contract_type, Market.FIXED, 100, 10)
        mlist = fixer_offer.place()
        self.assertEqual(mlist[0].mclass, 'offer_created')

        # Each side has an offer on this issue.
        offers = testdb.offer.filter(issue=test_contract_type.issue)
        self.assertEqual(2, len(offers))

        # No contracts exist on this issue.
        offers = testdb.offer.filter(issue=test_contract_type.issue)
        self.assertEqual(2, len(offers))

    def test_best_price_for_existing_fixer(self):
        '''
        The developer is willing to put up 200 (FIXED price = 200). A user then
        offers to put up 900, for a FIXED price of 100.  The price is 100.
        '''

        testdb = Market()
        testuser = Account(balance = 9000).persist(testdb)
        testfixer = Account(balance = 2000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        testdb.offer(testfixer, test_contract_type, Market.FIXED, 200, 10).place()

        user_offer = testdb.offer(testuser, test_contract_type, Market.UNFIXED, 100, 10)
        mlist = user_offer.place()
        self.assertEqual('contract_created', mlist[0].mclass)
        self.assertEqual(100, mlist[0].price)
        self.assertEqual(0, testuser.total)
        pos = testdb.position.filter(account=testuser)[0]
        self.assertEqual(testuser, pos.account)
        self.assertEqual(-10, pos.quantity)
        self.assertEqual(9000, pos.basis) # Total paid for this position
        # Developer has 1000 back in their balance.
        self.assertEqual(1000, testfixer.balance)

    def test_no_deal_user_first(self):
        '''
        No contract is formed when the price in the developer's offer is higher than the price
        in the user's offer.
        '''
        testdb = Market()
        testuser = Account(balance = 8000).persist(testdb)
        testfixer = Account(balance = 1000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        testdb.offer(testuser, test_contract_type, Market.UNFIXED, 200, 10).place()
        mlist = testdb.offer(testfixer, test_contract_type, Market.FIXED, 100, 10).place()
        self.assertEqual('offer_created', mlist[0].mclass)
        self.assertEqual(8000, testuser.total)
        self.assertEqual(1000, testfixer.total)

    def test_no_deal_fixer_first(self):
        '''
        As above, but with offers coming in a different order.
        '''
        testdb = Market()
        testfixer = Account(balance = 1000).persist(testdb)
        testuser = Account(balance = 8000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        testdb.offer(testfixer, test_contract_type, Market.FIXED, 100, 10).place()
        mlist = testdb.offer(testuser, test_contract_type, Market.UNFIXED, 200, 10).place()
        self.assertEqual('offer_created', mlist[0].mclass)
        self.assertEqual(8000, testuser.total)
        self.assertEqual(1000, testfixer.total)

    def test_add_match_many(self):
        '''
        One FIXED offer from one fixer matches two existing UNFIXED offers from users.
        '''

        testdb = Market()
        testuser1 = Account(balance = 9000).persist(testdb)
        testuser2 = Account(balance = 9000).persist(testdb)
        testfixer = Account(balance = 2000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        testdb.offer(testuser1, test_contract_type, Market.UNFIXED, 100, 10).place()
        testdb.offer(testuser2, test_contract_type, Market.UNFIXED, 100, 10).place()

        # Now place the fixer offer. This time, four messages will be returned because
        # two contracts are formed and both sides are notified of each.
        fixer_offer = testdb.offer(testfixer, test_contract_type, Market.FIXED, 100, 20)
        mlist = fixer_offer.place()
        self.assertEqual(4, len(mlist))
        self.assertEqual(('contract_created', testfixer.id, Market.FIXED, 100, 10),
                         (mlist[0].mclass, mlist[0].account, mlist[0].side, mlist[0].price, mlist[0].quantity))
        self.assertEqual(('contract_created', testuser1.id, Market.UNFIXED, 100, 10),
                         (mlist[1].mclass, mlist[1].account, mlist[1].side, mlist[1].price, mlist[1].quantity))
        self.assertEqual(('contract_created', testfixer.id, Market.FIXED, 100, 10),
                         (mlist[2].mclass, mlist[2].account, mlist[2].side, mlist[2].price, mlist[2].quantity))
        self.assertEqual(('contract_created', testuser2.id, Market.UNFIXED, 100, 10),
                         (mlist[3].mclass, mlist[3].account, mlist[3].side, mlist[3].price, mlist[3].quantity))

    def test_add_match_best_user_offers(self):
        '''
        One FIXED offer from one fixer matches two existing UNFIXED offers from users.
        '''

        testdb = Market()
        testuser1 = Account(balance = 9000).persist(testdb)
        testuser2 = Account(balance = 9000).persist(testdb)
        testuser3 = Account(balance = 8000).persist(testdb)
        testfixer = Account(balance = 2000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        # Two users want the developer to put up 100, one wants 200.
        good_offer_1 = testdb.offer(testuser1, test_contract_type, Market.UNFIXED, 100, 10)
        good_offer_1.place()
        good_offer_2 = testdb.offer(testuser2, test_contract_type, Market.UNFIXED, 100, 10)
        good_offer_2.place()
        bad_offer = testdb.offer(testuser3, test_contract_type, Market.UNFIXED, 200, 10)
        bad_offer.place()

        # Now place the fixer offer. The bad offer is left unmatched.
        testdb.offer(testfixer, test_contract_type, Market.FIXED, 100, 20).place()
        self.assertFalse(good_offer_1.exists)
        self.assertFalse(good_offer_2.exists)
        self.assertTrue(bad_offer.exists)

    def test_cancel_partly_filled_offer(self):
        '''
        A user places an offer that is partly matched by a developer.  Then the user cancels the
        offer.  They get back their tokens for the uncanceled part.
        '''

        testdb = Market()
        testuser = Account(balance = 9000).persist(testdb)
        testfixer = Account(balance = 500).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        testoffer = testdb.offer(testuser, test_contract_type, Market.UNFIXED, 100, 10)
        testoffer.place()
        self.assertEqual(0, testuser.balance)
        testdb.offer(testfixer, test_contract_type, Market.FIXED, 100, 5).place()
        testoffer.cancel()
        self.assertEqual(4500, testuser.balance)

    def test_fail_cancel_filled_offer(self):
        '''
        A user places an offer that is matched by a developer.  Then the user tries to cancels the
        offer and fails.
        '''
        testdb = Market()
        testuser = Account(balance = 9000).persist(testdb)
        testfixer = Account(balance = 1000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        testoffer = testdb.offer(testuser, test_contract_type, Market.UNFIXED, 100, 10)
        testoffer.place()
        testdb.offer(testfixer, test_contract_type, Market.FIXED, 100, 10).place()
        with self.assertRaises(RuntimeError):
            testoffer.cancel()

    def test_offset_offers(self):
        '''
        A user places an offer that is matched by a developer.  Then the user buys the developer out
        early and gets a little back.
        '''
        testdb = Market()
        testuser = Account(balance = 18500).persist(testdb)
        testfixer = Account(balance = 1000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        testdb.offer(testuser, test_contract_type, Market.UNFIXED, 100, 10).place()
        testdb.offer(testfixer, test_contract_type, Market.FIXED, 100, 10).place()
        # So far it looks like the user will lose 9000 and the fixer will gain 9000
        # when the contract matures.  But wait. The user offers to resolve 
        # immediately for a 5% "discount".
        testdb.offer(testuser, test_contract_type, Market.FIXED, 950, 10).place()

        # Fixer agrees.  Instead of making 9000 on the deal they'll make 8500.
        mlist = testdb.offer(testfixer, test_contract_type, Market.UNFIXED, 950, 10).place()
        self.assertEqual(4, len(mlist))
        self.assertEqual('position_covered', mlist[2].mclass)
        self.assertEqual(10, mlist[2].quantity) 
        self.assertEqual('position_covered', mlist[3].mclass)
        self.assertEqual(10, mlist[3].quantity) 
        # User started with 18500, keeps 10000 of it. Fixer is up 8500.
        self.assertEqual(10000, testuser.total)
        self.assertEqual(9500, testfixer.total)

    def test_make_offset(self):
        '''
        Generate offers that get out of positions.
        '''
        testdb = Market()
        testuser = Account(balance = 18500).persist(testdb)
        testfixer = Account(balance = 1000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        testdb.offer(testuser, test_contract_type, Market.UNFIXED, 100, 10).place()
        testdb.offer(testfixer, test_contract_type, Market.FIXED, 100, 10).place()
        
        user_position = testdb.position.filter(account=testuser)[0]
        user_offset = user_position.offset(9000)
        self.assertEqual(user_offset.price, 100)
        user_offset = user_position.offset(8000)
        self.assertEqual(user_offset.price, 200)
        fixer_position = testdb.position.filter(account=testfixer)[0]
        fixer_offset = fixer_position.offset(1000)
        self.assertEqual(user_offset.price, 200)
        fixer_offset = fixer_position.offset(2000)
        self.assertEqual(user_offset.price, 200)
        user_offset.place()
        fixer_offset.place()
        self.assertEqual([], testdb.position.filter(account=testuser))
        self.assertEqual([], testdb.position.filter(account=testfixer))

    def test_crowdfunding(self):
        '''
        A developer offers to fix an issue and gets a little support from a bunch of users.
        '''

        user_count = 800
        testdb = Market()
        testfixer = Account(balance = user_count * 500).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)
        testdb.offer(testfixer, test_contract_type, Market.FIXED, 500, user_count).place()

        testusers = []
        for i in range(user_count):
            testusers.append(Account(balance=500).persist(testdb))
        for i in range(user_count):
            testdb.offer(testusers[i], test_contract_type, Market.UNFIXED, 500, 1).place()

        positions = testdb.position.filter(issue=test_contract_type.issue)
        self.assertEqual(1 + user_count, len(positions))
        for position in positions:
            m = position.contract_type.maturity.maturity
            self.assertEqual(timezone.utc.utcoffset(m), position.contract_type.maturity.tzinfo.utcoffset(m))
            self.assertEqual(test_contract_type, position.contract_type)
            if position.account == testfixer:
                self.assertEqual(user_count * 500, position.basis)
            else:
                self.assertEqual(500, position.basis)

        test_contract_type.resolve(True)
        profit = 500 * user_count
        fee = profit * 0.1
        self.assertEqual(testfixer.balance, 1000 * user_count - fee)
        for i in range(user_count):
            self.assertEqual(testusers[i].balance, 0)

    def test_partial_work(self):
        "Two developers cooperate on an issue in series."

        testdb = Market()
        testuser= Account(balance=180000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        # User needs something fixed.
        testdb.offer(testuser, test_contract_type, Market.UNFIXED, 150, 100).place()
        self.assertEqual(testuser.balance, 95000)

        # JS developer takes it on. 
        js_developer = Account(balance=90000).persist(testdb)
        testdb.offer(js_developer, test_contract_type, Market.FIXED, 150, 100).place()

        # JS developer: Oh noes, I'm stuck on the CSS but I made a bunch of progress.
        # Will someone else finish this?
        testdb.offer(js_developer, test_contract_type, Market.UNFIXED, 600, 100).place()

        # CSS developer: I can do that.
        css_developer = Account(balance=80000).persist(testdb)
        testdb.offer(css_developer, test_contract_type, Market.FIXED, 600, 100).place()

        # User: this fix looks good to me. Let's resolve this early. I'll get out of my position.
        testdb.offer(testuser, test_contract_type, Market.FIXED, 950, 100).place()

        # CSS developer: Sure, I'll take 95 now instead of 100 later.
        testdb.offer(css_developer, test_contract_type, Market.UNFIXED, 950, 100).place()

        # resolve here pretty much does nothing because everyone already collaborated.
        test_contract_type.resolve(True)

        # JS developer bought 100 units at 150 and sold at 600.
        # Profit of 45000.
        self.assertEqual(js_developer.balance, 135000)

        # CSS developer bought 100 units at 600 and sold at 950.
        self.assertEqual(css_developer.balance, 115000)

        # User was only ever on the UNFIXED side, bought in at 150, sold at 950, for a loss
        self.assertEqual(testuser.balance, 100000)

    def test_j_cyber_sec_3_1_fixed(self):
        "Example 3.1 from the paper"
        testdb = Market()
        test_contract_type = self.make_contract_type(testdb)

        # Example 3.1. (Base Case: Fixing Issue)
        # User Adam finds a software bug. Adam has heard of a futures trading market 
        # where he can get the bug fixed for a price.
        adam = Account(balance=160000).persist(testdb)

        # Adam documents the bug in an issue tracker (now identified as bug #1337) and goes to the trading market.
        test_contract_type = self.make_contract_type(testdb) 

        # Adam creates an offer with a maturation date in two weeks for a payout of $200.
        # Adam buys 200 units — $1 potential payout each — at a unit price of $0.8, paying
        # $160, by depositing the money into escrow.
        # Note: Adam is buying the UNFIXED side, so paying 800.
        testdb.offer(adam, test_contract_type, Market.UNFIXED, 200, 200).place()

        # Developer Beth sees the offer, has time to fix bug #1337 within two weeks, and decides
        # to accept the offer.
        beth = Account(balance = 40000).persist(testdb)

        # Beth buys the 200 units at a unit price of $0.2, paying $40,
        # by depositing the money into escrow.
        testdb.offer(beth, test_contract_type, Market.FIXED, 200, 200).place()

        # The contract is now formed: Adam owns the UNFIXED position and Beth owns the
        # If bug #1337 is fixed then the issue is closed: Beth earns the reward of $160 and gets her $40 deposit back.
        # The amount here is different from the amount in the paper because Beth has paid a 10% fee
        # on her profit of 160.
        test_contract_type.resolve(True)
        self.assertEqual(184000, beth.balance)
        self.assertEqual(0, adam.balance)

    def test_j_cyber_sec_3_1_unfixed(self):
        "Example 3.1 from the paper"
        testdb = Market()
        test_contract_type = self.make_contract_type(testdb)

        # Example 3.1. (Base Case: Fixing Issue)
        # User Adam finds a software bug. Adam has heard of a futures trading market 
        # where he can get the bug fixed for a price.
        adam = Account(balance=160000).persist(testdb)

        # Adam documents the bug in an issue tracker (now identified as bug #1337) and goes to the trading market.
        test_contract_type = self.make_contract_type(testdb) 

        # Adam creates an offer with a maturation date in two weeks for a payout of $200.
        # Adam buys 200 units — $1 potential payout each — at a unit price of $0.8, paying
        # $160, by depositing the money into escrow.
        # Note: Adam is buying the UNFIXED side, so paying 800.
        testdb.offer(adam, test_contract_type, Market.UNFIXED, 200, 200).place()

        # Developer Beth sees the offer, has time to fix bug #1337 within two weeks, and decides
        # to accept the offer.
        beth = Account(balance = 40000).persist(testdb)

        # Beth buys the 200 units at a unit price of $0.2, paying $40,
        # by depositing the money into escrow.
        testdb.offer(beth, test_contract_type, Market.FIXED, 200, 200).place()

        # The contract is now formed: Adam owns the UNFIXED position and Beth owns the
        # If bug #1337 is unfixed then the issue remains open: Beth loses her $40 deposit while Adam receives his and 
        # Beth’s deposits, earning $40.
        # The amount here is different from the amount in the paper because Adam has paid a 10% fee
        # on her profit of 40.
        test_contract_type.resolve(False)
        self.assertEqual(0, beth.balance)
        self.assertEqual(196000, adam.balance)

    def test_j_cyber_sec_3_2_fixed(self):
        "Example 3.2 from the paper"
        testdb = Market()
        test_contract_type = self.make_contract_type(testdb)

        # Example 3.1. (Base Case: Fixing Issue)
        # User Adam finds a software bug. Adam has heard of a futures trading market 
        # where he can get the bug fixed for a price.
        adam = Account(balance=160000).persist(testdb)

        # Adam documents the bug in an issue tracker (now identified as bug #1337) and goes to the trading market.
        test_contract_type = self.make_contract_type(testdb) 

        # Adam creates an offer with a maturation date in two weeks for a payout of $200.
        # Adam buys 200 units — $1 potential payout each — at a unit price of $0.8, paying
        # $160, by depositing the money into escrow.
        # Note: Adam is buying the UNFIXED side, so paying 800.
        testdb.offer(adam, test_contract_type, Market.UNFIXED, 200, 200).place()

        # Developer Beth sees the offer, has time to fix bug #1337 within two weeks, and decides
        # to accept the offer.
        beth = Account(balance = 160000).persist(testdb)

        # Beth buys the 200 units at a unit price of $0.2, paying $40,
        # by depositing the money into escrow.
        testdb.offer(beth, test_contract_type, Market.FIXED, 200, 200).place()

        # One week later, Beth realizes that she does not have the expertise to fully
        # fix bug #1337.  Beth decides to submit a partial fix and sell her FIXED position.
        testdb.offer(beth, test_contract_type, Market.UNFIXED, 400, 200).place()

        # Charles buys the 200 units of the FIXED position from Beth at a unit price
        # of $0.4, paying $80 to Beth
        charles = Account(balance = 80000).persist(testdb)
        testdb.offer(charles, test_contract_type, Market.FIXED, 400, 200).place()
        self.assertEqual(charles.balance, 0)
        self.assertEqual(beth.balance, 200000)

        # If bug #1337 is fixed then the issue is closed: Charles earns the reward of $200
        # for a net gain of $120.
        # The amount here differs from the amount in the paper because Charles pays
        # a 10% fee on his profit of 120.
        test_contract_type.resolve(True)
        self.assertEqual(charles.balance, 188000)

        # Beth has earned a profit of 40 (not subject to oracle fee)
        self.assertEqual(beth.balance, 200000)

    def test_j_cyber_sec_3_2_unfixed(self):
        "Example 3.2 from the paper, unfixed case"
        testdb = Market()
        test_contract_type = self.make_contract_type(testdb)

        # Example 3.1. (Base Case: Fixing Issue)
        # Same trades as above.
        adam = Account(balance=160000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb) 
        testdb.offer(adam, test_contract_type, Market.UNFIXED, 200, 200).place()

        beth = Account(balance = 160000).persist(testdb)
        testdb.offer(beth, test_contract_type, Market.FIXED, 200, 200).place()

        testdb.offer(beth, test_contract_type, Market.UNFIXED, 400, 200).place()
        charles = Account(balance = 80000).persist(testdb)
        testdb.offer(charles, test_contract_type, Market.FIXED, 400, 200).place()
        self.assertEqual(charles.balance, 0)
        self.assertEqual(beth.balance, 200000)

        # If bug #1337 is fixed then the issue is closed: Charles earns the reward of $200
        # for a net gain of $120.
        # The amount here differs from the amount in the paper because Charles pays
        # a 10% fee on his profit of 120.

        # If bug #1337 is unfixed then the issue remains open: Charles receives nothing but
        # loses the $80 paid to Beth, while Adam receives his and Beth’s deposits from escrow,
        # earning $40. 
        # Here Adam pays the oracle fee on his profit of 40.
        test_contract_type.resolve(False)
        self.assertEqual(charles.balance, 0)
        self.assertEqual(adam.balance, 196000)

        # In both cases, Beth earned $40 for her partial work.
        self.assertEqual(beth.balance, 200000)

    def test_j_cyber_sec_3_3(self):
        "Example 3.3 from the paper"
        testdb = Market()
        test_contract_type = self.make_contract_type(testdb)

        # Example 3.3. (Selling Position) As before (Example 3.1), Adam ($160 for the UNFIXED position)
        # and Beth ($40 for FIXED position) enter into a futures contract worth a payout of $200 
        # in two weeks depending on the status of bug #1337.
        adam = Account(balance = 300000).persist(testdb)
        beth = Account(balance = 40000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb) 
        testdb.offer(adam, test_contract_type, Market.UNFIXED, 200, 200).place()
        testdb.offer(beth, test_contract_type, Market.FIXED, 200, 200).place()
        self.assertEqual(adam.balance, 140000)
        self.assertEqual(beth.balance, 0)

        # After 2 days Adam decides he wants his money back. He sells his UNFIXED position
        # of the contract to Bob.
        testdb.offer(adam, test_contract_type, Market.FIXED, 300, 200).place()

        # Bob buys the 200 units of the UNFIXED position at a unit price of $0.7,
        # paying $140 to Adam.
        bob = Account(balance=140000).persist(testdb)
        testdb.offer(bob, test_contract_type, Market.UNFIXED, 300, 200).place()
        self.assertEqual(bob.balance, 0) 

        # Adam has paid $20 for 2 days of development. Bob pays $140 for the remaining days
        # until maturation.  Beth is unaffected and continues developing.
        self.assertEqual(adam.balance, 280000)
        self.assertEqual(beth.balance, 0)

    def test_messages_for_issue(self):
        testdb = Market()
        testuser = Account(balance = 9000).persist(testdb)
        testfixer = Account(balance = 2000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)
        testdb.offer(testfixer, test_contract_type, Market.FIXED, 200, 10).place()
        testdb.offer(testuser, test_contract_type, Market.UNFIXED, 100, 10).place()
        test_contract_type.resolve(True)
        msgs = testdb.history.filter(issue=test_contract_type.issue, ticker=True)
        self.assertEqual(2, len(msgs))
        self.assertEqual('contract_resolved', msgs[0].mclass)
        self.assertEqual('contract_created', msgs[1].mclass)
        self.assertEqual(test_contract_type, msgs[0].contract_type)
        self.assertEqual(test_contract_type, msgs[1].contract_type)

    def test_graph(self):
        testgraph = Market().graph().as_html(100, 100)
        graph = testgraph

    def test_fail_partly_match_existing_all_or_nothing_offer(self):
        '''
        A developer places an all or nothing offer that is not matched by a small offer placed
        by a user.  Both offers can be cancelled.
        '''

        testdb = Market()
        testuser = Account(balance = 25000).persist(testdb)
        testfixer = Account(balance = 50000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        testoffer = testdb.offer(testfixer, test_contract_type, Market.FIXED, 500, 100, all_or_nothing = True)
        testoffer.place()
        self.assertEqual(0, testfixer.balance)
        test_user_offer = testdb.offer(testuser, test_contract_type, Market.UNFIXED, 500, 25)
        mlist = test_user_offer.place()
        self.assertEqual(1, len(mlist))
        self.assertEqual('offer_created', mlist[0].mclass)
        test_user_offer.cancel()
        testoffer.cancel()
        self.assertEqual(25000, testuser.balance)
        self.assertEqual(50000, testfixer.balance)

    def test_new_all_or_nothing_fail_match_existing_small_offer(self):
        '''
        A developer places an all or nothing offer when an existing small offer exists. No match
        occurs and the developer can cancel.
        '''

        testdb = Market()
        testuser = Account(balance = 25000).persist(testdb)
        testfixer = Account(balance = 50000).persist(testdb)
        test_contract_type = self.make_contract_type(testdb)

        testdb.offer(testuser, test_contract_type, Market.UNFIXED, 500, 10).place()
        testoffer = testdb.offer(testfixer, test_contract_type, Market.FIXED, 500, 100, all_or_nothing=True)
        mlist = testoffer.place()
        self.assertEqual(1, len(mlist))
        self.assertEqual('offer_created', mlist[0].mclass)
        testoffer.cancel()
        self.assertEqual(50000, testfixer.balance)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    demo_db = Market(start_demo_db=True)
    unittest.main(failfast=True)
    demo_db.stop_demo_db()

# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
