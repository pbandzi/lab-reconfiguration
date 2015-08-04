## lab-reconfiguration
Script reconfigure UCSM vnics for varios OPNFV deployers

```
Usage: reconfigUcsNet.py [options]
Options:
-h, --help            
   show this help message and exit
-i IP, --ip=IP        
   [Mandatory] UCSM IP Address
-u USERNAME, --username=USERNAME
   [Mandatory] Account Username for UCSM Login
-p PASSWORD, --password=PASSWORD
   [Mandatory] Account Password for UCSM Login
-f FILE, --file=FILE
   [Optional] Yaml file with network config you want to set for POD
   If not present only current network config will be printed
```
