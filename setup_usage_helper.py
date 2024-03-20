import sys
import time
import traceback
from ctypes import Structure, windll, c_uint, sizeof, byref
from datetime import datetime, time as Time

import psutil
import requests
import winapps


def installed_apps_list_generator():  # generates a list with all running installed apps
    app_list = []
    for app in winapps.list_installed():
        app_list.append(app)
    return app_list


def process_list_generator():
    """
    Generate a list of dictionaries containing information about running processes and their connections.

    Returns:
        list: A list of dictionaries where each dictionary contains the following keys:
            - "name": Name of the process.
            - "pid": Process ID.
            - "local_ip": Local IP address of the connection, or None if not applicable.
            - "local_port": Local port of the connection, or None if not applicable.
            - "remote_ip": Remote IP address of the connection, or None if not applicable.
            - "remote_port": Remote port of the connection, or None if not applicable.
            - "status": Connection status.

    Note:
        If a process cannot be found, it is skipped and not included in the final list.
    """
    processes = []
    try:
        for connection in psutil.net_connections():
            process_name = psutil.Process(connection.pid).name()
            process_pid = connection.pid
            local_ip = connection.laddr.ip if connection.laddr else None
            local_port = connection.laddr.port if connection.laddr else None
            remote_ip = connection.raddr.ip if connection.raddr else None
            remote_port = connection.raddr.port if connection.raddr else None
            status = connection.status

            processes.append({
                "name": process_name,
                "pid": process_pid,
                "local_ip": local_ip,
                "local_port": local_port,
                "remote_ip": remote_ip,
                "remote_port": remote_port,
                "status": status
            })
    except psutil.NoSuchProcess:
        pass  # Handle NoSuchProcess exception if required
    return processes


def publish_setup_status(name, status, url):  # publish results into Setup Usage API
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

    # get request domain URL from ini
    full_url = url + f'setupName={name}&setupStatus={status}'
    print(f'API request URL: {full_url}')

    # publish into remote API
    try:
        response = requests.get(full_url)
        if response.status_code == 200:
            print('Request successful.')
    except requests.exceptions.ConnectionError as error_message:
        print('Request failed.')
        with open('offline_setup_usage.dat', 'a+') as file:
            file.write(f'Setup name: {name}\t'
                       f'Setup status: {status}\t'
                       f'Date: {print_date}\t'
                       f'Time: {print_time}\t'
                       '\n')
        print('Setup status written to offline_setup_usage.dat file.')
        print(error_message)
        traceback.print_exc()

    # generate request from parameters
    time.sleep(2)
    sys.exit(0)


def process_checker(process_list, process_name):  # checks if specific process is running
    for process in process_list:
        if process["name"] == process_name:  # check for process active session
            return True
    return False


def connection_counter(process_list, process_name, port_limit):  # checks instances of a passed process
    port_count = 0
    for process in process_list:
        if process["name"] == process_name:  # check for process active session
            port_count += 1
            if port_count > port_limit:
                return True


def check_connection(source_process_name, destination_process_name,
                     process_iterable, connection_status='ESTABLISHED',
                     process_port=None):  # checks if two different processes are connected to each other
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


def check_remote_connection(source_process_name, process_iterable,
                            connection_status='ESTABLISHED', remote_process_port=None):  # checks if a process is
    # connected to a different machine in the network

    for process in process_iterable:  # get source_process and destination_process connections from process list
        if process['name'] == source_process_name \
                and process['status'] == connection_status \
                and process['remote_port'] == remote_process_port:
            return True
    return False


def idle_time_check(milliseconds=1200):  # check for system idle time in Windows OS
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

    if get_idle_duration() > milliseconds:  # 20 minutes timeout
        return True
    else:
        return False


def working_hours_test_check():  # checks if time not between 22pm-6am
    # get current time
    current_time = datetime.now().time()
    # if current time between 0:00 and 6:00, report idle
    late_night = Time(0) < current_time < Time(6)
    small_hours = Time(22) < current_time < Time(23, 59, 59)
    if late_night or small_hours:
        return False
    else:
        return True
