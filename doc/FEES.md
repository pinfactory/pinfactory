Fees
====

There is a 10% fee on resolved contracts.


Fairness and painlessness
=========================

In order to get traders to accept the fee, it needs to appear both fair and painless.

 * Winner pays: you pay a fee when you are already feeling "up" from a market gain.

 * Fee on your gains only: if you do arbitrage that results in multiple contracts being
   resolved on the same contract type (issue, maturity pair), then you pay a fee on the net amount.
   (If the fee were imposed on the entire contract amount, then nobody who put up < 10%
   for the fix of an unlikely issue would earn anything!)

 * Fee appears fair and proportional to services provided.

 * Endowment effect: Fee is not levied on money that the user already believes is "theirs."


Enabling one kind of fee avoidance
==================================

Let's look at a simple use case with and without
fee avoidance.  All prices are expressed as the
price of the FIXED side of the contract.  Here's the
first option:

 * Adam offers to buy 100 UNFIXED at a contract price of 10%, putting up 90 tokens.

 * Beth offers to buy 100 FIXED at the same price, putting up 10 tokens.

 * Contract is formed. Adam holds the UNFIXED side, Beth holds the FIXED side.

 * Beth fixes the issue and the contract is resolved in Beth's favor. Beth makes
   a gain of 90 and pays a fee of 9.  Adam is down 90 (but has his issue fixed, so
   he's happy.)  The final score: Adam: -90. Beth: +81. Market: +9.


Here's a variant.

 * Adam offers to buy 100 UNFIXED at a contract price of 10%, putting up 90 tokens.

 * Beth offers to buy 100 FIXED at the same price, putting up 10 tokens.

 * Contract is formed. Adam holds the UNFIXED side, Beth holds the FIXED side.

 * Beth fixes the issue, then offers to buy 100 UNFIXED at a price of 91, to cancel
   out her position at a profit.

 * Adam sees that his issue is fixed. He offers to buy 100 FIXED at a price of 95.

 * A second contract is formed. In this one, Adam holds the FIXED side, Beth holds
   the UNFIXED side.

Now both sides are going to get the same amount back,
no matter how the oracle resolves the contract.
Beth has put in a total of 15, and can only win one
contract, so earns a profit of 85.  Adam has put in a
total of 185, but wins one contract, for a loss of 85.

In this situation, we don't actually have to run the
oracle at all.  And Adam and Beth have done some very
helpful things for us.

 * Putting out a price signal before contract resolution

 * Put 2x the money into the system (to make the second contract).

 * Save us having to run the oracle on this contract, with all the
   possible disputes that might have to be handled.

All good for helping the market to grow and scale.

There is a subset of contracts on which the oracle
does not need to run, because no party has a net
exposure to the result.  This occurs when everyone
who is invested in that contract type owns an equal
number of units of FIXED and UNFIXED.

What about detecting no-oracle-needed contract type
maturities, and waiving the fee?

This is even more interesting when speculators
are involved.  Speculators would be incentivized to
get out of their positions before market maturity,
feeding more information into the system.

Paying customers could even auto-avoid the fee
by buying out small positions, giving a small-time
participant a guaranteed win in exchange for resolving
the whole contract type without the oracle.

So how would we still make money?

 * Basic futures market is generic!  Already published, and
   we still risk that GitHub or another player could implement
   a competing system. We have to focus on value added products
   and those are  made more valuable
   by feeding more info and money into the system.

 * Monthly or quarterly fees. (We will need
   some fee for money in/out by way of the payment
   processor anyway.)

 * Raise the percentage fee on oracle-required transactions?

