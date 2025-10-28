Administration guide
====================

Supported platform
------------------

 * Debian version 11

This is the supported platform for a real deploy.  (Any platform
with bash, curl and Docker should work for development and testing,
because our tests scripts run in a Debian 11 container.)


Deploy the current version to the server
----------------------------------------

Deploy with

```
./deploy.sh
```

This will copy the current configuration from the server if available.

If you don't have the production configuration file (with GitHub key) this should fail.



Roll back to an earlier version of the code
-------------------------------------------

TK


Print money
-----------

To add tokens to the system you now need to do some SQL.

In the future, users with the `banker` role will be able to increase their balance.


First, start a psql session:

```
psql --user postgres -d market
```

Find the user you want

```
select account.id, userid.username, account.balance from account join userid on account.id = userid.account;
```

Increase the balance:

```
update account set balance = balance + 1000000 where id = 2;
```

(That will increase the balance by 1000 tokens. Balances are stored as millitokens.)



Let's Encrypt certificate
-------------------------

Install packages.

`sudo apt install certbot python-certbot-apache`

Put the server name in `/etc/apache2/sites-enabled/000-default.conf`.

Get the certificate.

`sudo certbot --apache`


GitHub webhook
--------------

The market has a webhook at the path `/webhook`.  This is where
GitHub POSTs, to inform us about new issues, and changes to issues.

To configure it on the GitHub side, go to "Settings" and select "Webhooks."

Payload URL should be `https://market.pinfactory.org/webhook`

Content type should be `application/json`

Fill in the secret for your project.

Under **Which events would you like to trigger this webhook?** select "Issues."

Make sure "Active" is checked.


Log in with GitHub
------------------

"Authorization callback URL" should be:

https://market.pinfactory.org/github/auth


Troubleshooting
---------------

**Postgres primary key sequence out of sync?** The `id` column in some tables is a `SERIAL PRIMARY KEY`.
This can cause `psycopg2.errors.UniqueViolation` exceptions.

To check for errors:

```
SELECT MAX(id) FROM the_table;
SELECT nextval(pg_get_serial_sequence('the_table', 'id'));
```

If the first value is higher than the second, the sequence needs to be reset.

```
SELECT setval(pg_get_serial_sequence('the_table', 'id'), (SELECT MAX(id) FROM the_table) + 1);
```

References
----------

[Secure HTTP Traffic with Certbot](https://www.linode.com/docs/quick-answers/websites/secure-http-traffic-certbot/)

[Certbot on Debian](https://certbot.eff.org/lets-encrypt/debianstretch-apache.html)

[Webhooks | GitHub Developer Guide](https://developer.github.com/webhooks/)

[Basics of Authentication | GitHub Developer Guide](https://developer.github.com/v3/guides/basics-of-authentication/)


