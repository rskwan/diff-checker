diff-checker
============

Checks for differences in webpages and sends SMS messages if detected. Currently checks every 10 seconds for differences, which is probably not a good idea.

Making It Better
----------------

* Allow user to set interval for checking
* Let user request a message at 6PM every Thursday, for example
* Make a non-testing Flask configuration

Tools
-----

* Flask: website
* Twilio: sending SMS messages
* SQLite: storing user data
* APScheduler: running update function every *n* time units.

Team
----

Just me, [Ronald Kwan](http://www.ocf.berkeley.edu/~rkwan/).