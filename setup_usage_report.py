import configparser
import os
import sys

import setup_usage_helper as su


def read_config():
    # Read configuration file
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'setup_usage.ini'))
    return config


def get_setup_name():
    # Get setup name from environment variable
    return os.getenv('SETUP_NAME')


def check_anritsu(process_list):
    # Check for Anritsu setup and automated test
    if 'Anritsu' in setup_name:
        print('Setup identified as: Anritsu.')
        anritsu_automation = su.connection_counter(process_list, 'java.exe', 6)
        if anritsu_automation:
            print('Anritsu setup performing automated testing. Reporting...')
            su.publish_setup_status(setup_name, 'automation', api_url)


def check_keysight(process_list):
    # Check for Keysight setup and test type
    if 'Keysight' in setup_name:
        print('Setup identified as: Keysight.')
        if 'PCAT' in setup_name:
            keysight_test_running = su.process_checker(process_list, 'SAS5GSequencerDriver.exe')
        else:
            keysight_test_running = su.check_connection('SASLTESequencer.exe', 'AniteAutomationController.exe',
                                                        process_list)

        if keysight_test_running:
            keysight_automation = su.check_connection('SASTestManager.exe', 'RCMISvr.exe', process_list)
            test_type = 'automation' if keysight_automation else 'manual'
            print(f'Keysight setup performing {test_type} testing. Reporting...')
            su.publish_setup_status(setup_name, test_type, api_url)


def check_rohde_schwarz(process_list):
    # Check for Rohde-Schwarz setup and test type
    if 'RS' in setup_name:
        print('Setup identified as: Rohde-Schwarz.')
        rohde_schwarz_automation = su.check_connection('AutoMgr.exe', 'java.exe', process_list, process_port=4754) or \
                                   su.check_connection('AutoMgr.exe', 'RohdeSchwarz.Contest.exe', process_list,
                                                       process_port=4754)

        if rohde_schwarz_automation:
            print('Rohde-Schwarz setup performing automated testing. Reporting...')
            su.publish_setup_status(setup_name, 'automation', api_url)
        else:
            test_type = 'manual' if su.working_hours_test_check() else 'idle'
            print(f'Rohde-Schwarz setup performing {test_type} testing. Reporting...')
            su.publish_setup_status(setup_name, test_type, api_url)


def check_vendor(process_list):
    # Check for unrecognized vendor
    if not any(vendor in setup_name for vendor in ['Anritsu', 'Keysight', 'RS']):
        print("Unrecognized setup")
        su.publish_setup_status(setup_name, 'unrecognized_setup', api_url)
        sys.exit(1)


def setup_usage_report():
    # Read config and setup name
    config = read_config()
    global api_url
    api_url = config['setup_information']['api']
    global setup_name
    setup_name = get_setup_name()

    # Collect system process/pid/connections and save as process_list
    print('Generating list of system connections... ', end='')
    process_list = su.process_list_generator()
    print('done.')

    # Check for Anritsu setup
    check_anritsu(process_list)

    # Check for Keysight setup
    check_keysight(process_list)

    # Check for Rohde-Schwarz setup
    check_rohde_schwarz(process_list)

    # Check for unrecognized vendor
    check_vendor(process_list)

    # Determine setup state based on idle time and working hours
    if su.idle_time_check():
        setup_state = 'idle'
    elif su.working_hours_test_check():
        setup_state = 'manual'
    else:
        setup_state = 'idle'

    # Publish setup status with determined setup state
    su.publish_setup_status(setup_name, setup_state, api_url)


if __name__ == "__main__":
    setup_usage_report()
