import concurrent.futures
import signal
import argparse
from time import sleep
import config as user_config
from lib import config
from lib import mails


def create_report():
    has_error = False
    report = ''
    report += "\n    Checks in error:\n"
    for check in config.checks:
        if not check.ok:
            has_error = True
            report += '-+' * 40 + '\n'
            report += "%s: %s\n\t%s\n" % (check.target_name, check,
                      check.errmsg.strip())
    report += '-+' * 40 + "\n\n    Other checks (usually OK but may be in retry mode):\n"
    for check in config.checks:
        if check.ok:
            report += "Check %s is %s\n" % (check,
                      "OK" if check.retry_count == 0 else "retrying")

    return (report, has_error)

def usr1_handler(signum, frame):
    (report, err) = create_report()
    print ("Signal SIGUSR1 caught, printing state of checks.")
    print (report)

def alarm_handler(signum, frame):
    (report, err) = create_report()
    if err:
        mails.send_email_report(report)


if __name__ == '__main__':
    # register signal handling
    signal.signal(signal.SIGUSR1, usr1_handler)
    signal.signal(signal.SIGALRM, alarm_handler)

    # register report signal interval
    if config.emails.report.every > 0:
        signal.setitimer(signal.ITIMER_REAL, 60, config.emails.report.every)

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
