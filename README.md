# Setup Usage Script

Setup Usage Script is a client app that determines setup usage state from running processes and connections and publishes setup usage data into an remote server (Setup Usage API).

## Installation

Copy project folder, run with Python 3.7+

Install dependencies from requirements.txt (mainly psutil, requests, winapps)

## Usage

Set up a shortcut into Windows startup apps containing:

```cmd
"<path-to-python>pythonw.exe" "<path-to-setup-usage-project>setup_usage_loader.py"
```

## Limitations

Application meant for Windows clients

## Contact

Refer to luarle.sousa@sidia.com for questions or suggestions