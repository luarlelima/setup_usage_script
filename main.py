import psutil
import sys
import time
import configparser

import winapps
from ctypes import Structure, windll, c_uint, sizeof, byref

# get list of installed apps
installed_apps = []
print('Generating list of installed apps... ', end='')

for app in winapps.list_installed():
    installed_apps.append(app)

print('done.')

# collect system process/pid/connections and save as process_list
process_list = []
local_connections_list = []
remote_connections_list = []
print('Generating list of system connections... ', end='')

for i in psutil.net_connections():
    try:
        process_name = psutil.Process(i.pid).name()
        process_pid = i.pid

        if len(i.laddr) == 0:
            local_ip = i.laddr
            local_port = i.laddr
        else:
            local_ip = i.laddr.ip
            local_port = i.laddr.port

        if len(i.raddr) == 0:
            remote_ip = i.raddr
            remote_port = i.raddr
        else:
            remote_ip = i.raddr.ip
            remote_port = i.raddr.port

        status = i.status

        process_list.append(
            {
                "name": process_name,
                "pid": process_pid,
                "local_ip": local_ip,
                "local_port": local_port,
                "remote_ip": remote_ip,
                "remote_port": remote_port,
                "status": status
            }
        )

    except psutil.NoSuchProcess:
        continue

print('done.')


# publish results
def publish_setup_status(name, status):
    print('################################################################')
    print(f'Setup name: {name}')
    print(f'Setup status: {status}')
    print('################################################################')
    time.sleep(1)
    sys.exit(0)


# get equipment name
config = configparser.ConfigParser()
config.read('setup_usage.ini')
setup_name = config['setup_information']['setup_name']

# Vendor Support
for process in process_list:
    if process["name"] == "TeamViewer_Desktop.exe":  # if TeamViewer active session
        print("TeamViewer session is active - reporting 'Vendor Support' status...")
        time.sleep(2)
        publish_setup_status(setup_name, 'vendor_support')

# Remote Testing
chrome_remote_desktop_pids = 0
for process in process_list:
    if process["name"] == "remoting_host.exe":  # check for Chrome Remote Desktop/Remote Assistance active session
        chrome_remote_desktop_pids += 1
        if chrome_remote_desktop_pids > 7:
            print("Chrome Remote Desktop session is active - reporting 'Remote Test' status...")
            time.sleep(2)
            publish_setup_status(setup_name, 'remote_testing')


# automation / manual
# identify setup

def setup_vendor(installed_apps_list, *args):
    # anritsu_apps_list = ['Rapid Test Designer']
    # keysight_apps_list = ['Keysight']
    # rohde_schwarz_apps_list = ['R&S CMW']

    apps_list = []
    for i in args:
        apps_list.append(i)

    matched_apps_list = []
    for j in apps_list:
        for app in installed_apps_list:
            if str(app.name).startswith(j):
                matched_apps_list.append(True)
                break
            else:
                continue

    if len(apps_list) == len(matched_apps_list):
        return True
    else:
        return False


def check_connection(source_process_name, destination_process_name,
                     process_iterable, connection_status='ESTABLISHED',
                     process_port=None):
    l_ports = []
    r_ports = []
    # get source_process and destination_process connections from process list
    for process in process_iterable:
        if process['name'] == source_process_name and process['status'] == connection_status:
            l_ports.append(process['local_port'])
        elif process['name'] == destination_process_name and process['status'] == connection_status:
            r_ports.append(process['remote_port'])

    if not any([l_ports, r_ports]):  # if source_process or destination_process not found
        return False

    # if any source_process port matches any destination_process port, return True
    port_connection = None
    for port in l_ports:
        if port in r_ports:
            port_connection = port
            break
    if process_port is not None:  # check for 'port number' default parameter
        if port_connection == process_port:
            return True
        else:
            return False
    elif port_connection:
        return True


# check for IDLE setup
def idle_time_check():
    """Determines if a Windows system idle time exceeds 20 minutes."""

    def get_idle_duration():
        """Retrieves system idle time from user32.dll."""

        class LastInputInfo(Structure):
            _fields_ = [
                ('cbSize', c_uint),
                ('dwTime', c_uint),
            ]

        last_input_info = LastInputInfo()
        last_input_info.cbSize = sizeof(last_input_info)
        windll.user32.GetLastInputInfo(byref(last_input_info))
        idle_time_milliseconds = windll.kernel32.GetTickCount() - last_input_info.dwTime
        return idle_time_milliseconds / 1000.0

    if get_idle_duration() > 1200:  # 20 minutes timeout
        return True
    else:
        return False


# vendor variable
vendor = ''
print('Identifying current setup... ', end='')

# Anritsu setup check
if setup_vendor(installed_apps, 'Rapid Test Designer', 'Common Interface Driver'):
    vendor = 'anritsu'
    print('Setup identified as: Anritsu.')
    pass

# Keysight setup check
elif setup_vendor(installed_apps, 'Anite Automation', 'Anite Licensing', 'Keysight Core', 'Keysight SAS'):
    vendor = 'keysight'
    print('Setup identified as: Keysight.')
    # check for Keysight test
    print('Checking for test in Keysight... ')
    keysight_test_running = check_connection('SASLTESequencer.exe', 'AniteAutomationController.exe', process_list)
    # check for automated test
    keysight_automation = check_connection('SASTestManager.exe', 'RCMISvr.exe', process_list)

    if keysight_test_running:
        if keysight_automation:
            print('Keysight setup performing automated testing. Reporting... ')
            publish_setup_status(vendor, 'automation')
        else:
            print('Keysight setup performing manual testing. Reporting... ')
            publish_setup_status(vendor, 'manual')
    else:
        pass

# Rohde-Schwarz check
elif setup_vendor(installed_apps, 'R&S CMW1'):
    vendor = 'rohde-schwarz'
    print('Setup identified as: Rohde-Schwarz.')
    pass

elif setup_vendor(installed_apps, 'Intel'):  # dummy
    vendor = 'intel'
    print('Setup identified as: Dummy.')

# Vendor check
if vendor not in ['anritsu', 'keysight', 'rohde-schwarz', 'intel']:
    print("Unrecognized setup")
    sys.exit(1)

# Idle time check
if idle_time_check():
    publish_setup_status(setup_name, 'idle')

else:
    publish_setup_status(setup_name, 'local support')
