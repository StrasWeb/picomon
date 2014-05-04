import concurrent.futures
from config import *
import signal
import argparse
from time import sleep


def usr1_handler(signum, frame):
    print ("""Signal SIGUSR1 caught, printing state of checks.

    Checks in error:""")
    for check in checks:
        if not check.ok:
            print ('-' * 10)
            print ("Check %s is in error state:\n\t%s" % (check,
                check.errmsg.strip()))
    print ('-' * 10, """

    Other checks (usually OK):""")
    for check in checks:
        if check.ok:
            print ('-' * 10)
            print ("Check %s is OK" % check)
    print ('-' * 10)


if __name__ == '__main__':
    # register signal handling
    signal.signal(signal.SIGUSR1, usr1_handler)

    # Parse command line
    parser = argparse.ArgumentParser()
    parser.add_argument("-1", "--one",
        help="single run with immediate output of check results (test/debug)",
        action="store_true")
    args = parser.parse_args()

    # do the actual polling
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        def runner(check):
            return check.run(immediate=True), check

        if args.one:
            futures = []
            for check in checks:
                futures.append(executor.submit(runner, check))

            for future in concurrent.futures.as_completed(futures):
                success, check = future.result()
                if success:
                    print("Check %s successful!" % (str(check)))
                else:
                    print("Check %s failed:\n%s" %
                          (str(check), check.errmsg))
        else:
            # This will drift slowly as it takes (base_tick + espilon) seconds
            while True:
                for check in checks:
                    executor.submit(check.run())
                sleep(base_tick)
