Examples of existing and possible trader types and
strategies.

Killer whale
------------

A high-reputation developer with a large bankroll and
high ability to predict the results of their work.
Willing to buy FIXED at high unit prices if the
quantity is large.

For example, a developer who knows the guts of an
application well enough to add a major feature in a
week might be happy to put up 20,000 tokens in order
to receive a 20,000 token profit when the feature
is committed and accepted. (Buy 40,000 FIXED with a
price of 0.5.)

But they don't want to waste their time with small
positions that might be profitable per token invested
but do not provide enough total profit to justify
the time invested.

For this class of trader, it makes sense to offer an
"all or nothing" option on an offer.  If the whole
thing matches, then form a contract. Otherwise just
put it on the order book.

The presence of killer whales in a market provides
an opportunity for market makers (bots and humans).
If a market maker can see enough UNFIXED offers to
match all, or almost all, of the killer whale's
all-or-nothing FIXED offer, the market maker can
make a big UNFIXED offer to match the killer whale,
while hedging the position by buying FIXED to match
the small offers.


Frontrunner
-----------

A frontrunner believes that, for reasons outside the
market, a developer is likely to fix certain issues,
or that some developer is likely to fix some issue
for less profit than the market currently offers.
The frontrunner buys FIXED before a developer does,
then covers their position at a profit.


Fan
---

The fan places multiple small UNFIXED offers to
encourage their favorite developers to make their
favorite features.  Sets the offer price and quantity
to avoid creating attractive profit opportunities for
frontrunners, not to maximize profit.  Generally picks
latest possible maturity dates and rolls any profits
back into the market.


Hater
-----

The hater believes that other participants in the
market are over-estimating the likelihood that
developers will fix certain issues on time, but
that the market oracle is in general trustworthy.
Buys UNFIXED.  Avoids subjective issues that might
be closed in a developer's favor by a friendly
maintainer.

Generally buys the earliest available maturity dates.


Noob
----

Over-estimates their ability, buys more or larger
FIXED positions than they can actually complete or
convince others to help them with.

Likely to try to get out of these positions by buying
UNFIXED to offset them later.


Sniper
------

As seen on eBay. Trades at the last minute, possibly
after either opening a pull request that fixes an
issue, or posting a test that shows that a version
that everyone thought was fixed is in fact broken.

Projects can avoid sniper problems by thorough
testing of fixes and by communicating about progress
of their work.


Interpreter
-----------

Finds issues where the bug report or feature request
is unclear, but where substantial UNFIXED offers are
available. These offers might be from users wanting
a fix they can't explain or from Haters betting that
the problem is too ill-defined to fix.

The Interpreter buys FIXED, fills in the issue with
more information and possibly a test case, and then
buys UNFIXED to cover their position at a profit.
This may include translating the report, getting
additional info from the user, or defeating haters
in an online argument.


Full stack (if I have to)
-------------------------

Buys FIXED on an issue where they know they can do
all of the work, but have a unique advantage in a
certain part of it.  For example, a developer might
be really quick at developing new business logic for
a web application they know well, but slow (or no
faster than average) at designing form templates.

They do the work they're best at, then share it (in
conventional workflow, by opening a pull request for
comment) making it clear what remains to be done.
After sharing, they place an offer to buy UNFIXED to
get out of their position.

If another developer matches the offer, then they can
ignore the issue and go do something in which they
have a comparative advantage or find more fun. If
nobody matches it, then they still hold FIXED.
So they cancel the offer and complete the work.

This is another category of trader who will find
all-or-nothing offers useful.


Chicken player
--------------

A developer buys a small quantity of FIXED on an issue,
then notices that a speculator has also purchased a larger
quantity of FIXED, potentially earning more than
the developer from the developer's work.

The developer offers to sell out of their FIXED position
at a loss.  The speculator can't tell if the developer
is signaling inability to complete the work by the maturation
date, or if the developer is just playing "chicken" and
threatening to take a loss in order to inflict one on
the speculator.

The speculator can respond by offering to buy UNFIXED to
cut the developer in for a greater share of the gains,
or by continuing the game of "chicken."
