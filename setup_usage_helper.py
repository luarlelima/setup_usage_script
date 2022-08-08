from datetime import datetime, time as Time
from ctypes import Structure, windll, c_uint, sizeof, byref
import time
import sys

import traceback
import winapps
import psutil
import requests


def installed_apps_list_generator():
    app_list = []
    for app in winapps.list_installed():
        app_list.append(app)
    return app_list


def process_list_generator():
    proc_list = []
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

            proc_list.append(
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
    return proc_list


def publish_setup_status(name, status, url):  # publish results
    # datetime
    print_date = datetime.today().strftime('%Y-%m-%d')
    print_time = datetime.today().strftime('%H:%M:%S')

    # save into file for testing purposes
    with open('setup_usage.dat', 'a+') as file:
        file.write(f'Setup name: {name}\t'
                   f'Setup status: {status}\t'
                   f'Date: {print_date}\t'
                   f'Time: {print_time}\t'
                   '\n')
    print('Setup status written to setup_usage.dat file.')

    # publish into remote API
    # get request domain URL from ini
    full_url = url + f'setupName={name}&setupStatus={status}'
    print(f'API request URL: {full_url}')

    try:
        response = requests.get(full_url)
        if response.status_code == 200:
            print('Request successful.')
    except requests.exceptions.ConnectionError as error_message:
        print('Request failed.')
        print(error_message)
        traceback.print_exc()

    # generate request from parameters

    time.sleep(2)
    sys.exit(0)


def vendor_support_checker(process_list, setup_name, api_url):
    for process in process_list:
        if process["name"] == "TeamViewer_Desktop.exe":  # if TeamViewer active session
            print("TeamViewer session is active - reporting 'Vendor Support' status...")
            time.sleep(2)
            publish_setup_status(setup_name, 'vendor_support', api_url)


def process_checker(process_list, process_name):
    for process in process_list:
        if process["name"] == process_name:  # check for process active session
            return True
    return False


def connection_counter(process_list, process_name, port_limit):
    port_count = 0
    for process in process_list:
        if process["name"] == process_name:  # check for process active session
            port_count += 1
            if port_count > port_limit:
                return True


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


def idle_time_check():
    def get_idle_duration():

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


def working_hours_test_check():
    # get current time
    current_time = datetime.now().time()
    # if current time between 0:00 and 6:00, report idle
    late_night = Time(0) < current_time < Time(6)
    small_hours = Time(22) < current_time < Time(23, 59, 59)
    if late_night or small_hours:
        return False
    else:
        return True
