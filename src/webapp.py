# This is the starting point when the platform is launched.
# Starts off Flask which is our web framework.

# Import standard python modules.
from hashlib import sha1
import hmac
import logging
import os
import subprocess

# Import certain classes.
from flask import (
    Flask,
    abort,
    flash,
    make_response,
    redirect,
    request,
    render_template,
    session,
    url_for,
)

from flask_bootstrap import Bootstrap

from market import Market
from form import (
    OfferForm,
    OfferButton,
    IssueForm,
    CancelButton,
    MatchButton,
    OffsetForm,
    ResolveForm,
)

# FIXME use a real cache
# Cache our login info.
class Cache(object):
    def __init__(self):
        self._data = {}

    def get(self, k):
        return self._data.get(k)

    def set(self, k, v, timeout=None):
        self._data[k] = v

    def delete(self, k):
        if k in self._data:
            del self._data[k]


# Basic setup
app = Flask(__name__)
app.config.from_pyfile("config.py")
print(app.config)
bootstrap = Bootstrap(app)

def handle_authorize(remote, token, user_info):
    app.logger.debug(user_info)
    user = market.lookup_user(
        host="GitHub",
        sub=user_info["sub"],
        username=user_info["preferred_username"],
        profile=user_info["profile"],
    )
    session["host"] = user.host
    session["sub"] = user.sub
    where = session.get("destination")
    if where:
        del session["destination"]
        return redirect(where)
    return redirect(url_for("index"))


def get_user():
    user = market.lookup_user(host=session.get("host"), sub=session.get("sub"))
    if user is None:
        session["destination"] = request.path
        abort(403)  # Forbidden
    if not user.balance:
        return redirect(url_for("index"))
    return user


@app.route("/localuser")
def localuser():
    if "development" != app.config.get("ENV"):
        abort(404)
    from random import randint

    sub = randint(10000, 99999)
    username = request.args.get("name", "local-%d" % sub)
    is_oracle = True
    user = market.lookup_user(
        host="local", sub=sub, username=username, profile="http://localhost/%d" % sub
    )
    user.oracle = is_oracle
    user.persist(market)
    session["host"] = user.host
    session["sub"] = user.sub
    flash("Made a new local account: %s." % username)
    market.fund_test_users()
    return redirect(url_for("index"))


@app.route("/timejump")
def timejump():
    if "development" != app.config.get("ENV"):
        abort(404)
    try:
        days = int(request.args.get("days"))
        market.time_jump(days * 86400)
        msg = "Jumping time forward %d days" % days
    except Exception as e:
        app.logger.warning(e)
        msg = "Usage: timejump.sh [DAYS]"
    return msg


# Here we are populating the homepage once the application starts up (all the
# data you see once the platform is up and running).
@app.route("/")
def index():
    has_balance = False
    try:
        user = market.lookup_user(host=session["host"], sub=session["sub"])
        has_balance = user.balance > 0
    except:
        session.clear()
        user = None
    if not has_balance:
        if "development" == app.config.get("ENV"):
            # For local test only
            market.fund_test_users()
            flash("test users funded!")
        return render_template("index.html", hidenav=True, user=user)
    else:
        messages = market.history.filter(account=user, ticker=False)
        contracts = market.position.filter(account=user)
        offers = market.offer.filter(account=user)
        for offer in offers:
            offer.cancel_button = cancel_button(user, offer)
        match_own = app.config.get("MATCH_OWN_OFFERS", False)
        for offer in offers:
            offer.match_button = match_button(user, offer, match_own)
        for contract in contracts:
            contract.offset_form = offset_form(contract)
        return render_template(
            "userinfo.html",
            user=user,
            contracts=contracts,
            offers=offers,
            messages=messages,
        )


# '/contracts' is how you tell Flask what the associated function is which is
# defined below. When the app starts, only the homepage is populated. When the
# user clicks on the contracts tab in the UI, the web browser calls Flask with
# the link to contracts which Flask interprets as calling this function below.
# This is when the contracts page gets populated.
@app.route("/contracts")
def contracts():
    user = get_user()
    include_private = False
    if user.banker:
        include_private = True
    contracts = market.position.filter(account=user)
    for contract in contracts:
        contract.offset_form = offset_form(contract)
    return render_template("contracts.html", user=user, contracts=contracts)


@app.route("/offers")
def offers():
    user = get_user()
    include_private = False
    if user.banker:
        include_private = True
    offers = market.offer.filter(include_private=include_private)
    for offer in offers:
        offer.cancel_button = cancel_button(user, offer)
        match_own = app.config.get("MATCH_OWN_OFFERS", False)
    for offer in offers:
        offer.match_button = match_button(user, offer, match_own)
    return render_template("offers.html", user=user, offers=offers)


@app.route("/login")
def login():
    if (
        "development" == app.config.get("ENV")
        and "http://localhost:5000/" != request.url_root
    ):
        # Redirect non-canonical local URLs
        return redirect("http://localhost:5000/login")
    return redirect("/github/login")


@app.route("/result")
def result():
    user = get_user()
    return render_template("result.html", user=user)


@app.route("/user")
def userinfo():
    return redirect(url_for("index"))


@app.route("/issue/<iid>", methods=["GET"])
def issue_page(iid):
    try:
        iid = int(iid)
    except:
        return redirect(url_for("issues"))
    user = get_user()
    dest_url = "/issue/" + str(iid)
    if request.args:
        return redirect(dest_url)
    issue = market.issue_by_id(iid)
    if not issue:
        return redirect(url_for("issues"))
    if (not issue.is_public) and (not user.banker):
        return redirect(url_for("issues"))
    messages = market.history.filter(issue=issue, ticker=True)
    offers = market.offer.filter(issue=issue)
    contracts = market.position.filter(issue=issue, account=user)
    for offer in offers:
        offer.cancel_button = cancel_button(user, offer)
    match_own = app.config.get("MATCH_OWN_OFFERS", False)
    for offer in offers:
        offer.match_button = match_button(user, offer, match_own)
    for contract in contracts:
        contract.offset_form = offset_form(contract)
    return render_template(
        "issue.html",
        user=user,
        issue=issue,
        offers=offers,
        contracts=contracts,
        messages=messages,
    )

@app.route("/fakeissue")
def fakeissue():
    if "development" != app.config.get("ENV"):
        abort(404)
    issue = market.issue_by_url('http://localhost/fakeorg/fakeproject/1', 'Fake Issue', True)
    app.logger.debug("fake issue %s", issue)
    return redirect(url_for("issue_page", iid=1))


@app.route("/offer/<iid>", methods=["GET"])
def offer_page(iid):
    try:
        iid = int(iid)
    except:
        return redirect(url_for("issues"))
    form = OfferForm()
    user = get_user()
    dest_url = "/offer/" + str(iid)
    if request.args:
        return redirect(dest_url)
    issue = market.issue_by_id(iid)
    if not issue:
        app.logger.debug("Bad or missing issue id %s" % iid)
        abort(404)
    form.show_errors = False
    form.issuename.data = issue.displayname
    form.issue.data = issue.id

    # Restore form values from session.
    if not form.quantity.data and session.get("quantity"):
        form.quantity.data = int(session.get("quantity"))
    if not form.price.data and session.get("price"):
        form.price.data = float(session.get("price"))
    if (form.side.data != "FIXED" and form.side.data != "UNFIXED") and session.get(
        "side"
    ):
        form.side.data = session.get("side")
    if not form.maturity.data and session.get("maturity"):
        form.maturity.data = session.get("maturity")

    maturities = market.maturities()
    offers = market.offer.filter(issue=issue)
    for offer in offers:
        offer.cancel_button = cancel_button(user, offer)
    match_own = app.config.get("MATCH_OWN_OFFERS", False)
    for offer in offers:
        offer.match_button = match_button(user, offer, match_own)
    return render_template(
        "offer.html",
        user=user,
        issue=issue,
        form=form,
        offers=offers,
        maturities=maturities,
    )


@app.route("/offer", methods=["POST"])
def offer():
    """
    This gets called when the offer form is submitted with data.
    """
    form = OfferForm()
    try:
        iid = int(form.issue.data)
    except:
        app.logger.debug("Could not get issue from form data.")
        return redirect(url_for("issue"))
    user = get_user()
    app.logger.debug("issue arg is %s url is %s" % (iid, request.path))
    for field in ["quantity", "price", "side", "issue", "maturity"]:
        if form.data.get(field):
            app.logger.debug("saving %s: %s" % (field, str(form.data[field])))
            session[field] = str(form.data[field])
    app.logger.debug("Session: %s" % session)
    if form.validate_on_submit():
        iid = int(form.issue.data)
        if form.side.data == "FIXED":
            side = True
        if form.side.data == "UNFIXED":
            side = False
        price = int(form.price.data * 1000)
        if price < 0 or price > 1000:
            raise RuntimeError
        if price * form.quantity.data <= user.balance:
            res = market.place_order(
                user,
                form.issue.data,
                form.maturity.data,
                side,
                price,
                form.quantity.data,
            )
            for item in res:
                tmp = str(item)
                flash(tmp)
        else:
            flash(
                "Insufficient balance to place that order. Your balance: %s"
                % user.display_balance
            )
    else:
        flash("Complete the form to make an offer.")
    dest_url = "/issue/%s" % iid
    return redirect(dest_url)


@app.route("/cancel", methods=["POST"])
def cancel():
    user = get_user()
    form = CancelButton()
    try:
        if not user:
            raise RuntimeError
        oid = int(form.offer.data)
        offer = market.offer.by_id(oid)
        for message in offer.cancel(user=user):
            tmp = str(message)
            flash(tmp)
    except Exception as e:
        app.logger.info(e)
        flash("Offer already cancelled or does not match your account.")
    return redirect(
        request.referrer
    )  # FIXME -- should use issue ID from offer's contract type


@app.route("/match", methods=["POST"])
def match():
    "Generate an offer to match an existing offer."
    form = MatchButton()
    offer = market.offer.by_id(int(form.offer.data))
    app.logger.debug("found offer %s" % offer)
    if not offer:
        flash("Could not locate offer to match.")
        return redirect(request.referrer)
    session["price"] = offer.price / 1000
    session["quantity"] = offer.quantity
    if offer.side:
        session["side"] = "UNFIXED"
    else:
        session["side"] = "FIXED"
    session["maturity"] = offer.contract_type.maturity.id
    app.logger.debug(session)
    flash(
        "Generated offer to match the one you clicked on. Click the Place Offer button to place it."
    )
    return redirect("/offer/%d" % offer.contract_type.issue.id)


@app.route("/offset", methods=["POST"])
def offset():
    "Generate an offer to offset an existing position."
    form = OffsetForm()
    try:
        position = market.position.filter(pid=int(form.position.data))[0]
        app.logger.debug("Found position %s" % position)
    except IndexError:
        flash("Could not location position to offset.")
        return redirect(request.referrer)
    price = 0
    try:
        price = int(form.price.data)
    except:
        pass
    if not price:
        flash("Enter a positive integer to offer to sell your position.")
        return redirect(request.referrer)
    offset = position.offset(price * 1000)
    session["price"] = "%.3f" % (offset.price / 1000)
    session["side"] = offset.displayside
    session["quantity"] = str(offset.quantity)
    session["maturity"] = offset.contract_type.maturity.id
    destination = "/offer/%d" % offset.contract_type.issue.id
    app.logger.debug(session)
    app.logger.debug("destination: %s" % destination)
    flash(
        "Generated offer to offset your position. Click the Place Offer button to place it."
    )
    return redirect(destination)


@app.route("/resolve", methods=["GET"])
def resolve():
    user = get_user()
    if not user.oracle:
        flash("permission denied")
        return redirect(url_for("index"))
    contract_types = market.contract_type.resolvable()
    for ctype in contract_types:
        tmp = ResolveForm()
        tmp.contract_type.data = ctype.id
        tmp.issue.data = ctype.issue.id
        tmp.maturity.data = ctype.maturity.id
        ctype.resolve_form = tmp
    return render_template("resolve.html", user=user, contract_types=contract_types)


@app.route("/resolve", methods=["POST"])
def post_resolve():
    user = get_user()
    if not user.oracle:
        flash("permission denied")
        return redirect(url_for("index"))
    form = ResolveForm()
    iid = int(form.issue.data)
    mid = int(form.maturity.data)
    if form.side.data == "FIXED":
        side = True
    elif form.side.data == "UNFIXED":
        side = False
    else:
        flash("Please complete the form to resolve.")
        return redirect(url_for("resolve"))
    contract_type = market.contract_type.lookup(iid, mid)
    if not contract_type or contract_type.id != int(form.contract_type.data):
        raise NotImplementedError
    contract_type.resolve(side)
    message = "Resolved %s as %s" % (contract_type, form.side.data)
    flash(message)
    return redirect(url_for("resolve"))


@app.route("/history", methods=["GET"])
def history():
    user = get_user()
    messages = market.history.filter(ticker=True)
    return render_template("history.html", user=user, messages=messages)


@app.route("/feed", methods=["GET"])
def feed():
    messages = []
    (prev_contract, prev_price) = (None, 0)
    history = market.history.filter()
    for mess in history:
        if not mess.contract_type:
            continue
        # Don't repeat the same contract/price
        if mess.contract_type == prev_contract and mess.price == prev_price:
            continue
        (prev_contract, prev_price) = (mess.contract_type, mess.price)
        if (
            mess.mclass == "offer_created"
            or mess.mclass == "contract_created"
            or (mess.mclass == "contract_resolved" and mess.price)
        ):
            messages.append(mess)
        if len(messages) >= 15:
            break
    res = make_response(render_template("feed.xml", messages=messages))
    res.headers["Content-type"] = "application/xml; charset=utf-8"
    return res


@app.route("/ticker", methods=["GET"])
def ticker():
    user = get_user()
    result = make_response(market.ticker_csv())
    #    result.headers["Content-Disposition"] = "attachment; filename=export.csv"
    result.headers["Content-type"] = "text/csv"
    return result


@app.route("/graph/<w>/<h>", methods=["GET"])
def graph(w, h):
    user = get_user()
    gfilter = request.args.to_dict()
    try:
        (width, height) = (int(w), int(h))
    except:
        raise
        return redirect(url_for("measure_frame"))
    try:
        result = make_response(market.graph(**gfilter).as_html(height, width))
    except Exception as e:
        app.logger.warning(e)
        return "", 204
    return result


@app.route("/measure_frame", methods=["GET"])
def measure_frame():
    return make_response(
        """
        <html><head><script>window.location = '//' + window.location.host + '/graph/' +
                            (window.innerWidth-100) + '/' + (window.innerHeight-100) +
                            window.location.search</script></head></html>
    """
    )


def offer_button(issue):
    form = OfferButton()
    form.issue.data = issue.id
    return form


def match_button(user, offer, match_own):
    if match_own or user.id != offer.account.id:
        form = MatchButton()
        form.offer.data = offer.id
        return form
    else:
        return None


def cancel_button(user, offer):
    if user.id == offer.account.id:
        form = CancelButton()
        form.offer.data = offer.id
        return form
    else:
        return None


def offset_form(position):
    form = OffsetForm()
    try:
        form.position.data = int(position.id)
        return form
    except:
        app.logger.error(
            "Can't make offset form for %s with id: %s" % (position, position.id)
        )
        return "<!-- failed to make offset form for %s -->" % position


@app.route("/issues", methods=["GET", "POST"])
def issues():
    form = IssueForm()
    user = get_user()
    include_private = False
    if not user:
        return redirect(url_for("index"))
    if form.validate_on_submit():
        issue = market.add_issue(user, form.url.data)
        verb = "updated"
        if issue.new:
            verb = "added"
        flash("%s %s" % (issue.displayname, verb))
        return redirect(url_for("issue"))
    if user.banker:
        include_private = True
    project = request.args.get("project")
    issues = market.get_issues(include_private, project)
    if project:
        issueheader = "Issues for project %s" % project
    else:
        issueheader = "All issues in the market"

    for issue in issues:
        issue.action_button = offer_button(issue)
    return render_template(
        "issues.html",
        issueheader=issueheader,
        user=user,
        form=form,
        issues=issues,
        title="Issues",
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    flash("404 page not found")
    return (render_template("result.html"), 404)


@app.errorhandler(403)
def permission_denied(e):
    return redirect(url_for("login"))


# This is a route that Github calls when something changes on their side.
# Github's server has a webhook to our site that enables Github to notify us When
# a change happens at their end.
@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Hub-Signature", "")
    if signature:
        app.logger.info("Received webhook signature %s" % signature)
        signature = signature.split("=")[1]
    else:
        app.logger.warning("Missing webhook signature")
    key = app.config.get("GITHUB_WEBHOOK_SECRET").encode()
    mac = hmac.new(key, msg=request.data, digestmod=sha1)
    if not hmac.compare_digest(mac.hexdigest(), signature):
        app.logger.warning(
            "Bad or missing signature in webhook does not match %s" % mac.hexdigest()
        )
        app.logger.warning("signature: %s" % signature)
        app.logger.warning("hmac digest: %s" % mac.hexdigest())
        # FIXME
        #  return 'OK'
    else:
        app.logger.debug("Good signature in webhook.")

    try:
        payload = request.get_json()
        action = payload.get("action")
    except AttributeError:
        app.logger.warning("Failed to get JSON from webhook request")
        # FIXME: raise an error here
        return "OK"

    app.logger.debug("Webhook action is %s" % action)
    if not action in ("opened", "edited", "deleted", "closed", "reopened"):
        return "OK"
    try:
        issue_url = payload["issue"]["html_url"]
        if payload["issue"]["state"] == "open":
            is_open = True
        else:
            is_open = False
    except Exception as e:
        app.logger.info("Could not get issue URL or state from webhook payload: %s" % e)
        return "OK"
    try:
        issue_title = payload["issue"]["title"]
        app.logger.info(
            "Issue title for %s with open=%s is: %s" % (issue_url, is_open, issue_title)
        )
    except Exception as e:
        app.logger.info("Could not get title from webhook payload: %s" % e)
        issue_title = None
    try:
        issue = market.issue_by_url(issue_url, issue_title, is_open)
        app.logger.info("Successfully processed webhook for %s" % issue)
    except Exception as e:
        app.logger.warning("Failed to create or update issue from webhook: %s" % e)
    return "OK"


# This lets us use Github for logins. Note: the "defs" are just defining functions.
# They are only run when invoked. So this code gets run after the basic setup is
# complete.

app.logger.setLevel(logging.DEBUG)

app.logger.info("App %s started. Env is %s" % (__name__, app.config.get("ENV")))
app.logger.debug("Logging at DEBUG level.")

print("env is ", app.config.get("ENV"))

# Market object gets created here, unless this is a temporary process.
market = Market(applog=app.logger)
app.logger.debug("Market connected.")
market.setup()

if "development" == app.config.get("ENV"):
    app.logger.info(
        """

#################################################################################
#                                                                               #
# Welcome to the local market test environment.                                 #
#                                                                               #
#   * To log in with your real GitHub credentials: http://localhost:5000        #
#                                                                               #
#   * To log in as a temporary local test user: http://localhost:5000/localuser #
#                                                                               #
# YOUR ACTIONS ON THIS TEST SERVER WILL NOT BE REFLECTED ON THE LIVE SERVER.    #
#                                                                               #
#################################################################################
"""
    )

# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
