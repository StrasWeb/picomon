Picomon
=======

Picomon is a very small and minimal alerting tool


Dependencies
------------

Written in Python, it needs at least python 3.2 for the ThreadPools.

On Debian Wheezy the package is `python3`.

Some checks are implemented using Nagios' checks,
available under Debian in package `nagios-plugins-basic`.

The DNS zone check calls [Bortzmeyer's](https://github.com/bortzmeyer/check_dns_soa)
(introduced [here](http://www.bortzmeyer.org/go-dns-icinga.html)).


Usage
-----

    usage: picomon.py [-h] [-1]

    optional arguments:
      -h, --help  show this help message and exit
      -1, --one   single run with immediate output of check results (test/debug)


Configuration
-------------

Everything can be configured from config.py: notified email(s), base tick, hosts and checks.

The `base_tick` option defines the base granularity (in seconds) for polling.
`Host`s are shorthands to avoid repeating addresses within checks.
Checks are then defined as a list of `Check`-derived class instances that
implement every single check (see picomon/checks.py).

Each check may be initialised with some options:

  * `every`: run every `every` × `base_tick` seconds;
  * `retry`: number of retries before considering a failure (so failure is after `every` × (`retry`+1) × `base_tick` seconds;
  * `timeout`: subcommand timeout, to avoid stalling checks (defaults to 2 seconds);
  * `target_name`: human-readable name of the target of the check (automatically set by the `name` option if using `Host` instances).

In addition some checks have specific options, see picomon/checks.py for examples.

In case you want to check lesser important services and configure very long check intervals, you may
want to have another interval, global to all checks, for error retries. This can be set with the `error_every` option.

For a full list of all available options, see the picomon/__init__.py file.

Current state output
--------------------

Just send the `SIGUSR1` signal to the process: it will first print the checks
in error state and then the successful checks to the standard output.

Please note that this will cancel the current `base_tick` sleeping period
and thus trigger a new run.


Alert emails
------------

An email can be sent each time a check switches to error state or recovers from
an error. These two emails are bound together so that a threading MUA will assemble
failure/recovery notifications together.


Global reports
--------------
Picomon can send global reports as a reminder of failed checks.
They are sent on a regular basis (configured with option `emails.report.every`)
only if there are some checks in an error state.


Test it!
--------

You have several solutions :

  * Install with `distutils`, for example: `setup.py install --user` then run it from your local bin/ directory;
  * Run directly with something like `python3 -m picomon`
  * Set python module path by hand: `PYTHONPATH=. bin/picomon`

The default config file is `config.py`, so either copy/link the sample one, write
your own or use the `-s` command line argument.


License
-------

This project is placed under GNU GPLv3. See COPYING.
