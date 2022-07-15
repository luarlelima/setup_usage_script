import os

import configparser
import sys
import time

import setup_usage_helper as su

# config file setup
config = configparser.ConfigParser()
# read config file from same directory
config.read(os.path.join(os.path.dirname(__file__), 'setup_usage.ini'))
# read server URL from config file
api_url = config['setup_information']['api']

# get equipment name
setup_name = os.getenv('SETUP_NAME')

# get list of installed apps
print('Generating list of installed apps... ', end='')
installed_apps = su.installed_apps_list_generator()
print('done.')

# collect system process/pid/connections and save as process_list
print('Generating list of system connections... ', end='')

print('done.')
process_list = su.process_list_generator()

# Vendor Support
su.vendor_support_checker(process_list, setup_name, api_url)

# Anritsu setup check ########
if 'Anritsu' in setup_name:
    print('Setup identified as: Anritsu.')

    # check for Anritsu (automated) test
    print('Checking for test in Anritsu... ')
    anritsu_automation = su.connection_counter(process_list, 'java.exe', 6)

    if anritsu_automation:
        print('Anritsu setup performing automated testing. Reporting... ')
        su.publish_setup_status(setup_name, 'automation', api_url)

# Keysight setup check ########
elif 'Keysight' in setup_name:
    print('Setup identified as: Keysight.')

    # check for Keysight test
    print('Checking for test in Keysight... ')
    keysight_test_running = su.check_connection('SASLTESequencer.exe', 'AniteAutomationController.exe', process_list)

    # check for automated test
    keysight_automation = su.check_connection('SASTestManager.exe', 'RCMISvr.exe', process_list)

    if keysight_test_running:
        if keysight_automation:
            print('Keysight setup performing automated testing. Reporting... ')
            su.publish_setup_status(setup_name, 'automation', api_url)
        else:
            print('Keysight setup performing manual testing. Reporting... ')
            su.publish_setup_status(setup_name, 'manual', api_url)

# Rohde-Schwarz check ########
elif 'RS' in setup_name:
    print('Setup identified as: Rohde-Schwarz.')

    # check for automated test
    rohde_schwarz_automation = su.check_connection('AutoMgr.exe', 'java.exe', process_list, process_port=4754)

    if rohde_schwarz_automation:
        print('Rohde-Schwarz setup performing automated testing. Reporting... ')
        su.publish_setup_status(setup_name, 'automation', api_url)
    else:
        print('Rohde-Schwarz setup performing manual testing. Reporting... ')
        su.publish_setup_status(setup_name, 'manual', api_url)

# Vendor check
else:
    print("Unrecognized setup")
    su.publish_setup_status(setup_name, 'unrecognized_setup', api_url)
    sys.exit(1)
# Idle check - do not send "manual" outside working hours
if su.idle_time_check():
    su.publish_setup_status(setup_name, 'idle', api_url)
else:
    if su.working_hours_test_check():
        su.publish_setup_status(setup_name, 'manual', api_url)
    else:
        su.publish_setup_status(setup_name, 'idle', api_url)
