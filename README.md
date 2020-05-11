# NetconfCiscoRouteMapBug
 
## Description

This script aims to demonstrate the bug within the netconf implementation on Cisco IOS-XE devices affecting the manipulation of the route-map.

The main() function is a bit chaotic, but I tried to add enough explicit comments to explain what it does.

I do not guarantee the idempotence of the results, but if your results are different than mines, feel free to share them with me. This script does a very minimal validation into the code and can crash (ex: connection timeout with the device, unexpected result, ...).

Disclaimer: The script was developed to demonstrate a bug, not to make any abusive usage of the bug. I decided to share the code for pedagogical reasons, knowing there is no security threat with it. However, I am not responsible for any action made by someone else.

## Requirements

* netmiko
* ncclient
* xmltodict
* pprint

NETCONF-YANG and SSH must be enabled on the destination host

## Configuration

Before running the script, make sure to update the following variables:
* routeMapName: Name of the route-map used for the tests. Be careful, if the route-map already exists, it will be deleted by the script.
* netconfHost: IP address or FQDN
* netconfPort: Netconf Port (Well-known port is 830)
* netconfUsername: Netconf username
* netconfPassword: Netconfg password
* sshHost: SSH host, I do not see why it should be updated though (refer to the same information as the netconf host)
* sshPort: SSH port (well-known port is 22)
* sshUsername: SSH username, update if different of the netconf credential
* sshPassword: SSH password, update if different of the netconf credential

This script has been tested on the Cisco DevNet sandbox (https://developer.cisco.com/site/sandbox/). It was tested on a CSR1000v running at the version **IOS-XE 16.09.03**. You can easily replicate by referring to the always-on sandbox credentials (https://developer.cisco.com/docs/sandbox/#!overview/all-networking-sandboxes). The credentials are not provided by default into the script by default, you must get them and update the variables.

## Usage

> python3 ./run.py

The script will launch a combination of netconf and cli(via ssh) commands.
