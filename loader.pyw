import sys
import time
import subprocess
import os

file_name = 'main.py'

while True:
    try:
        file_path = os.path.join(sys.path[0], file_name)
        print(f"Running {file_path} script...")
        subprocess.run(["pythonw", f"{file_path}"])
        time.sleep(2)
        seconds = 300
    except SystemExit:
        print("Ignoring SystemExit...")
    while True:
        print(f'Waiting {seconds} seconds...')
        time.sleep(1)
        if seconds <= 0:
            break
        seconds -= 1
