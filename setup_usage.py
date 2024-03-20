import time

from setup_usage_report import setup_usage_report

while True:
    try:
        setup_usage_report()
    except SystemExit:
        pass
    print(f'Waiting 60 seconds...')
    time.sleep(60)
