import sys
import time
import subprocess
import os
import configparser

# config file setup
config = configparser.ConfigParser()
config.read('setup_usage.ini')

# read config file from same directory
config.read(os.path.join(os.path.dirname(__file__), 'setup_usage.ini'))
file_name = config['setup_information']['setup_usage_script_path']

while True:
    try:
        file_path = os.path.join(sys.path[0], file_name)
        print(f"Running {file_path} script...")
        subprocess.run(["pythonw", f"{file_path}"])
        # subprocess.run("git -C C:\Projects\setup_usage_script pull "
        #                "https://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@github.com/luarlelima/setup_usage_script.git "
        #                " --rebase --autostash", creationflags=subprocess.CREATE_NO_WINDOW)
        time.sleep(2)
        seconds = int(config['setup_information']['script_loop_time_seconds'])
    except SystemExit:
        print("Ignoring SystemExit...")
    while True:
        print(f'Waiting {seconds} seconds...')
        time.sleep(1)
        if seconds <= 0:
            break
        seconds -= 1
