import concurrent.futures
import signal
import argparse
from time import sleep
import config as user_config
from lib import config
from lib import mails


def usr1_handler(signum, frame):
    print ("""Signal SIGUSR1 caught, printing state of checks.

    Checks in error:""")
    for check in config.checks:
        if not check.ok:
            print ('-+' * 40)
            print ("Check %s is in error state:\n\t%s" % (check,
                   check.errmsg.strip()))
    print ('-+' * 40, """

    Other checks (usually OK but may be in retry mode):""")
    for check in config.checks:
        if check.ok:
            print ("Check %s is %s" % (check,
                   "OK" if check.retry_count == 0 else "retrying"))


if __name__ == '__main__':
    # register signal handling
    signal.signal(signal.SIGUSR1, usr1_handler)

    # Parse command line
    parser = argparse.ArgumentParser()
    parser.add_argument("-1", "--one",
                        help="single run with immediate output of " +
                             "check results (test/debug)",
                        action="store_true")
    args = parser.parse_args()

    # do the actual polling
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        def runner(check):
            return check.run(immediate=True), check

        if args.one:
            futures = []
            for check in config.checks:
                futures.append(executor.submit(runner, check))

            for future in concurrent.futures.as_completed(futures):
                success, check = future.result()
                if success:
                    print("Check %s successful!" % (str(check)))
                else:
                    print("Check %s failed:\n%s" %
                          (str(check), check.errmsg.strip()))
        else:
            # This will drift slowly as it takes (base_tick + espilon) seconds
            while True:
                for check in config.checks:
                    executor.submit(check.run)
                sleep(config.base_tick)
    mails.quit()
