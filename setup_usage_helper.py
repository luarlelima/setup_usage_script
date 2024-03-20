import sys
import time
import traceback
from datetime import datetime, time as Time

import psutil
import requests


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


def publish_setup_status(name, status, url):
    # Get current date and time
    print_date = datetime.today().strftime('%Y-%m-%d')
    print_time = datetime.today().strftime('%H:%M:%S')

    # Save setup status into a file for testing purposes
    with open('setup_usage.dat', 'a+') as file:
        file.write(f'Setup name: {name}\t'
                   f'Setup status: {status}\t'
                   f'Date: {print_date}\t'
                   f'Time: {print_time}\t'
                   '\n')
    print('Setup status written to setup_usage.dat file.')

    # Generate API request URL
    full_url = f'{url}?setupName={name}&setupStatus={status}'
    print(f'API request URL: {full_url}')

    # Publish into the remote API
    try:
        response = requests.get(full_url)
        if response.status_code == 200:
            print('Request successful.')
    except requests.exceptions.RequestException as e:
        print('Request failed.')
        with open('offline_setup_usage.dat', 'a+') as file:
            file.write(f'Setup name: {name}\t'
                       f'Setup status: {status}\t'
                       f'Date: {print_date}\t'
                       f'Time: {print_time}\t'
                       '\n')
        print('Setup status written to offline_setup_usage.dat file.')
        print(e)
        traceback.print_exc()

    # Add a delay before exiting the script
    time.sleep(2)
    sys.exit(0)


def process_checker(process_list, process_name):
    """
    Checks if a specific process is running.

    Args:
        process_list (list): A list of dictionaries containing process information.
        process_name (str): The name of the process to check.

    Returns:
        bool: True if the process is found in the process list, False otherwise.
    """
    return any(process["name"] == process_name for process in process_list)


def connection_counter(process_list, process_name, port_limit):
    """
    Checks if the number of instances of a specific process exceeds a given limit.

    Args:
        process_list (list): A list of dictionaries containing process information.
        process_name (str): The name of the process to check.
        port_limit (int): The maximum number of instances allowed.

    Returns:
        bool: True if the number of instances exceeds the port limit, False otherwise.
    """
    # Count the number of instances of the specified process
    instances_count = sum(1 for process in process_list if process["name"] == process_name)

    # Check if the number of instances exceeds the port limit
    return instances_count > port_limit


def check_connection(source_process_name, destination_process_name,
                     process_iterable, connection_status='ESTABLISHED',
                     process_port=None):
    """
    Checks if two different processes are connected to each other.

    Args:
        source_process_name (str): The name of the source process.
        destination_process_name (str): The name of the destination process.
        process_iterable (iterable): An iterable containing dictionaries representing processes.
        connection_status (str): The status of the connection to consider (default is 'ESTABLISHED').
        process_port (int or None): Optional port number to check for a specific connection.

    Returns:
        bool: True if the connection is found, False otherwise.
    """
    # Extract source ports based on conditions
    source_ports = [process['local_port'] for process in process_iterable
                    if process['name'] == source_process_name and process['status'] == connection_status]

    # Extract destination ports based on conditions
    destination_ports = [process['remote_port'] for process in process_iterable
                         if process['name'] == destination_process_name and process['status'] == connection_status]

    # Check if both source and destination ports are present
    if not (source_ports and destination_ports):  # If either source or destination ports are missing
        return False

    # Check for port connection
    for port in source_ports:
        if port in destination_ports:  # If a matching port is found in both source and destination ports
            if process_port is not None and port != process_port:  # If process port is specified and doesn't match
                return False
            return True  # Connection found

    return False  # No matching connection found


def check_remote_connection(source_process_name, process_iterable,
                            connection_status='ESTABLISHED', remote_process_port=None):
    """
    Checks if a process is connected to a different machine in the network.

    Args:
        source_process_name (str): The name of the source process.
        process_iterable (iterable): An iterable containing dictionaries representing processes.
        connection_status (str): The status of the connection to consider (default is 'ESTABLISHED').
        remote_process_port (int or None): Optional remote port number to check for a specific connection.

    Returns:
        bool: True if the connection is found, False otherwise.
    """
    # Iterate through processes to find the connection
    for process in process_iterable:
        if (process['name'] == source_process_name and
                process['status'] == connection_status and
                process['remote_port'] == remote_process_port):
            return True  # Connection found

    return False  # Connection not found


def idle_time_check(milliseconds=1200):
    """
    Checks for system idle time in Windows OS.

    Args: milliseconds (int): The threshold for considering the system idle, in milliseconds. Default is 1200 (20
    minutes).

    Returns:
        bool: True if the system is idle for longer than the specified threshold, False otherwise.
    """

    def get_idle_duration():
        # Import ctypes library for interacting with C data types and functions
        import ctypes

        # Define a structure to hold last input information
        class LastInputInfo(ctypes.Structure):
            _fields_ = [
                ('cbSize', ctypes.c_uint),  # Size of the structure in bytes
                ('dwTime', ctypes.c_uint),  # Time of the last input event in milliseconds
            ]

        # Create an instance of the LastInputInfo structure
        last_input_info = LastInputInfo()

        # Structure size required by Windows API for proper data interpretation
        last_input_info.cbSize = ctypes.sizeof(last_input_info)

        # Retrieve the time of the last input event
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input_info))

        # Get the current tick count and calculate idle time in milliseconds
        tick_count = ctypes.windll.kernel32.GetTickCount()
        idle_time_milliseconds = tick_count - last_input_info.dwTime

        # Convert idle time to seconds and return
        return idle_time_milliseconds / 1000.0

    # Check if idle duration exceeds the specified threshold
    return get_idle_duration() > milliseconds / 1000.0


def working_hours_test_check():
    """
    Checks if the current time is not between 22:00 and 06:00.

    Returns:
        bool: True if the current time is within working hours, False otherwise.
    """
    # Get current time
    current_time = datetime.now().time()

    # Check if current time is within working hours
    if Time(6) <= current_time < Time(22):
        return True
    else:
        return False
