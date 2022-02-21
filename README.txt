### Setup Usage ###

Required libraries

psutil
winapps

Setup states criteria

    Powered off
        No updates into specified time window

    Powered on
        Running automation test
            Anritsu
                Pending
            Keysight
                SAS Test Manager (SASTestManager.exe) has a established connection into local port 6667 from Keysight RCMI Server (RCMISvr.exe)
                Terminal Automation Gateway (TerminalAutomationGateway.exe) has a established connection into local port 6667 from SAS LTE Sequencer (SASLTESequencer.exe)
                SAS LTE Sequencer (SASLTESequencer.exe) has a established connection into Terminal Automation Gateway (TerminalAutomationGateway.exe) remote port 6667
            R&S
                Pending
        Running manual test
            Anritsu
                Pending
            Keysight
                SAS LTE Sequencer (SASLTESequencer.exe) has a established connection into Anite Automation Controller (AniteAutomationController.exe) remote port 50012
                or
                Any connection from SAS (sas.exe) to remote port 1235
            R&S
                Pending
        Performing remote testing (done, needs testing)
            Chrome Remote Desktop session is active
            More than one instance of Chrome Remote Host process running (remoting_host.exe)
        Vendor support
            TeamViewer session is active
            TeamViewer Remote Desktop process (TeamViewer_Desktop.exe) is running
        Local support
            Automation, maintenance, tool development and testing-related tasks
            System idle time lower than 20 minutes
        Idle (done, needs testing)
            System idle time higher than 20 minutes