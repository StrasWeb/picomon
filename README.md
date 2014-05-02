Picomon
=======

Picomon is a very small and minimal alerting tool


Dependencies
------------

Written in Python, it needs at least python 3.2 for the ThreadPools.

On Debian Wheezy the package is `python3`.


Usage
-----

    usage: picomon.py [-h] [-1]

    optional arguments:
      -h, --help  show this help message and exit
      -1, --one   single run with immediate output of check results (test/debug)


Configuration
-------------

Everything can be configured from config.py: base tick, hosts and checks.

The `base_tick` option defines the base granularity (in seconds) for polling.
`Host`s are shorthands to avoid repeating addresses within checks.
Checks are then defined as a list of `Check`-derived class instances that
implement every single check (see lib/checks.py).


Current state output
--------------------

Just send the `SIGUSR1` signal to the process: it will first print the checks
in error state and then the successful checks to the standard output.


License
-------

This project is placed under GNU GPLv3. See COPYING.
