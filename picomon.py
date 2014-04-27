import concurrent.futures
from config import *


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        def runner(check):
            return check.run(), check

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
