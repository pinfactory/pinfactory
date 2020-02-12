Administration guide
====================

Supported platform
------------------

 * Debian version 9

This is the supported platform for a real deploy.
(Any platform with bash and Docker should work for
development and testing.)


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

TODO: Add the certbot renew to the weekly cron.


GitHub webhook
--------------

The market has a webhook at the path `/webhook`.
This is where GitHub POSTs to in order to inform us
about new issues, and changes to issues.

To configure it on the GitHub side, go to

"Webhooks" under "Project settings" and select "Issues".


Log in with GitHub
------------------

"Authorization callback URL" should be:

https://market.pinfactory.ca/github/auth


References
----------

[Secure HTTP Traffic with Certbot](https://www.linode.com/docs/quick-answers/websites/secure-http-traffic-certbot/)

[Certbot on Debian](https://certbot.eff.org/lets-encrypt/debianstretch-apache.html)

[Webhooks | GitHub Developer Guide](https://developer.github.com/webhooks/)

[Basics of Authentication | GitHub Developer Guide](https://developer.github.com/v3/guides/basics-of-authentication/)


