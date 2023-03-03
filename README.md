# Setup Usage Script

Setup Usage Script is a client app that determines setup usage state from running processes and connections and publishes setup usage data into an remote server (Setup Usage API).

## Installation

Copy project folder, run with Python 3.7+

Install dependencies from requirements.txt (mainly psutil, requests, winapps)

Define a system environment variable named 'setup_name' containing the setup name.

ATLAS uses the following format: 
<three-letter carrier acronym>_<vendor>_<setup_identifier_plus_extras>

Examples:

ATT_Keysight_2

TMO_Anritsu_IMS

LA_RS_TDD

TMO_RS_PQA_LTE_DP

## Usage

Set up a shortcut into Windows startup apps containing:

```cmd
"<path-to-python>pythonw.exe" "<path-to-setup-usage-project>setup_usage_loader.py"
```

## Limitations

Windows support only

## Contact

Refer to luarle.sousa@sidia.com for questions or suggestions