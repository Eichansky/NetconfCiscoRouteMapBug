#!/usr/bin/python
# -*-coding:Utf-8 -*
"""
This is a script to demonstrate the NETCONF bug with route-map on IOS-XE.

For the demonstration, the script uses the DevNet sandbox. For more information about the sandbox, visit https://developer.cisco.com/.
"""

## Global Variables
__author__       = "Maxim Deschenes"
__author_email__ = "maxim.deschenes@outlook.ca"
__copyright__    = "Copyright (c) 2020 Maxim Deschenes"
__license__      = "BSD-3-Clause (https://opensource.org/licenses/BSD-3-Clause)"


## Import librairies
import sys, pprint, xmltodict, netmiko
from ncclient import manager as ncclientManager

class netconf(object):
	"""
		Execute instructions via NETCONF.
	"""

	## Class variables
	host: str
	port: int
	username: str
	password: str


	def __init__(self, host: str, username: str, password: str, port: int = 830) -> object:
		"""
			Constructor that return an instantiation of the object.

			Arguments:
				host(str)       => FQDN or IP address of the NETCONF host.
				username(str)   => Username for the NETCONF host.
				passowrd(str)   => Password for the NETCONF host.
				port(int)       => Port for the Netconf host (Default = 830)

			Returns:
				object
		"""
		self.host=host
		self.port=port
		self.username=username
		self.password=password


	def getRouteMapByName(self, routeMapName: str="routeMapName") -> str:
		"""
			Read the route-map information and return the XML.

			Arguments:
				routeMapName(str)  => Name for the route-map to search (Default = "routeMapName")

			Returns:
				str
		"""

		## Variables
		netconfResponse: str
		filter: str

		## Define filter for the NETCONF request.
		filter="""
			<filter>
				<native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
					<route-map>
						<name>{routeMapName}</name>
					</route-map>
				</native>
			</filter>
		""".format(routeMapName=routeMapName)

		## Send the NETCONF request and store the result
		with ncclientManager.connect(host=self.host, port=self.port, username=self.username, password=self.password, hostkey_verify=False) as manager:
			netconfResponse=manager.get_config(source='running', filter=filter).data_xml

		## Return the list of route-map in XML format
		return netconfResponse


	def setRouteMap(self, routeMapName: str, routeMapSequence: int=10, routeMapOperation: str="permit", delete: bool=False) -> None:
		"""
			Create a route-map.

			Arguments:
				routeMapName(str)       => Name of the route-map to create.
				routeMapSequence(int)   => Sequence number of the route-map (Default = 10)
				routeMapOperation(str)  => Action to apply to the route-map [permit|deny] (Default = permit)
				delete(bool)            => If it is True, the route-map will be deleted; If it is False, the route-map information will be merged (Default = False)

			Returns:
				None

			Todo:
				Improvement: When the delete flag is "True", it delete the whole route-map and not only the sequence targeted. The idea is to move the operation="remove" to the "route-map-without-order-seq" node and to add a validation "if (last item) then (operation=remove added to "route-map" node), otherwise it will always keep "Seq=10 Ops=Permit" by default.
		"""

		## Variables
		operation: str="merge"
		config: str

		## Set action to "remove" if the delete flag is set to "True"
		if delete:
			operation="remove"
		
		## Verify if the operation is valide (permit or deny)
		if (routeMapOperation != "permit" and routeMapOperation != "deny"):
			raise ValueError("routeMapOperation must be either 'permit' or 'deny'")

		## Define the configuration
		config="""
			<config>
				<native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
					<route-map operation="{operation}">
						<name>{routeMapName}</name>
						<route-map-without-order-seq xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-route-map">
							<seq_no>{routeMapSequence}</seq_no>
							<operation>{routeMapOperation}</operation>
						</route-map-without-order-seq>
					</route-map>
				</native>
			</config>
		""".format(routeMapName=routeMapName, routeMapSequence=routeMapSequence, routeMapOperation=routeMapOperation, operation=operation)

		## NETCONF request
		with ncclientManager.connect(host=self.host, port=self.port, username=self.username, password=self.password, hostkey_verify=False) as manager:
			manager.edit_config(target="running", config=config)

		## End the function
		return None

	def getRouteMapBGPCommunity(self, routeMapName: str, routeMapSequence: int=10) -> list:
		"""
			Get the list BGP Community from a route-map.

			Arguments:
				routeMapName(str)     => Name of the route-map to get the BGP community list.
				routeMapSequence(int) => Sequence number where to get the set instructions (Default = 10)

			Returns:
				list
		"""

		## Variables
		netconfResponse: str
		filter: str
		communities: list

		## Define filter for the NETCONF request.
		filter="""
			<filter>
				<native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
					<route-map>
						<name>{routeMapName}</name>
						<route-map-without-order-seq xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-route-map">
							<seq_no>{routeMapSequence}</seq_no>
						</route-map-without-order-seq>
					</route-map>
				</native>
			</filter>
		""".format(routeMapName=routeMapName, routeMapSequence=routeMapSequence)

		## Send the NETCONF request and store the result
		with ncclientManager.connect(host=self.host, port=self.port, username=self.username, password=self.password, hostkey_verify=False) as manager:
			netconfResponse=xmltodict.parse(manager.get_config(source='running', filter=filter).data_xml)

		## Process the result
		try:
			if type(netconfResponse['data']['native']['route-map']['route-map-without-order-seq']['set']['community']['community-well-known']['community-list']) is str:
				## If the result is a string, create a list
				communities= [netconfResponse['data']['native']['route-map']['route-map-without-order-seq']['set']['community']['community-well-known']['community-list']]
			elif type(netconfResponse['data']['native']['route-map']['route-map-without-order-seq']['set']['community']['community-well-known']['community-list']) is list:
				## Else if it is already a list, just use it
				communities = netconfResponse['data']['native']['route-map']['route-map-without-order-seq']['set']['community']['community-well-known']['community-list']
			else:
				## If it is none of them, there is a problem
				raise KeyError
		except KeyError:
			## If there is a problem, return nothing
			communities = []
		
		## Return the array of BGP Communities
		return communities

	def setRouteMapBGPCommunity(self, routeMapName: str, routeMapSequence: int=10, BGPCommunity: str="1:1", delete: bool=False) -> None:
		"""
			Add the BGP community value to the targeted route-map/sequence.

			Arguments:
				routeMapName(str)       => Name of the route-map to update.
				routeMapSequence(int)   => Sequence number of the route-map (Default = 10)
				BGPCommunity(str)       => BGP community to manipulate
				delete(bool)            => If it is True, the BGP community is removed from the route-map; If it is False, the BGP Community information will be merged (Default = False)

			Returns:
				None

			Todo:
				Improvement: Veirfy if the route-map/seq exists before adding the BGP community.
		"""

		## Variables
		operation: str="merge"
		config: str

		## Set action to "remove" if the delete flag is set to "True"
		if delete:
			operation="remove"

		## Define the configuration
		config="""
			<config>
				<native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
					<route-map>
						<name>{routeMapName}</name>
						<route-map-without-order-seq xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-route-map">
							<seq_no>{routeMapSequence}</seq_no>
							<set>
								<community>
									<community-well-known>
										<community-list operation="{operation}">{BGPCommunity}</community-list>
									</community-well-known>
								</community>
							</set>
						</route-map-without-order-seq>
					</route-map>
				</native>
			</config>
		""".format(routeMapName=routeMapName, routeMapSequence=routeMapSequence, BGPCommunity=BGPCommunity, operation=operation)

		## NETCONF request
		with ncclientManager.connect(host=self.host, port=self.port, username=self.username, password=self.password, hostkey_verify=False) as manager:
			manager.edit_config(target="running", config=config)

		## End the function
		return None


	def getBGPCommunityNewFormat(self) -> bool:
		"""
			Get the information if the system uses the "new-format" to display the BGP Community. It retrurn the boolean status of the presence of the new-format (True = uses the new-format)

			Arguments:
				None

			Returns:
				bool
		"""
		## Variables
		netconfResponse: str
		filter: str

		## Define filter for the NETCONF request.
		filter="""
			<filter>
				<native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
					<ip>
						<bgp-community />
					</ip>
				</native>
			</filter>
		"""

		## Send the NETCONF request and store the result
		with ncclientManager.connect(host=self.host, port=self.port, username=self.username, password=self.password, hostkey_verify=False) as manager:
			netconfResponse=xmltodict.parse(manager.get_config(source='running', filter=filter).data_xml)

		## Veify if the configuration exist and return the associated value
		if ('native' in netconfResponse['data']):
			return True
		else:
			return False


	def setBGPCommunityNewFormat(self, delete: bool=False) -> None:
		"""
			Add the BGP community value to the targeted route-map/sequence.

			Arguments:
				delete(bool)       => If True, it will remove the new-format configuraiton

			Returns:
				None
		"""

		## Variables
		operation: str="merge"
		config: str

		## Set action to "remove" if the delete flag is set to "True"
		if delete:
			operation="remove"

		## Define the configuration
		config="""
			<config>
				<native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
					<ip>
						<bgp-community>
							<new-format operation="{operation}" />
						</bgp-community>
					</ip>
				</native>
			</config>
		""".format(operation=operation)

		## NETCONF request
		with ncclientManager.connect(host=self.host, port=self.port, username=self.username, password=self.password, hostkey_verify=False) as manager:
			manager.edit_config(target="running", config=config)

		## End the function
		return None



class ssh(object):
	"""
		Exucute instructions via SSH
	"""

	## Class variables
	host: str
	port: int
	username: str
	password: str
	ssh: object

	def __init__(self, host: str, username: str, password: str, port: int = 22) -> object:
		"""
			Constructor that return an instantiation of the object.

			Arguments:
				host(str)       => FQDN or IP address of the SSH host.
				username(str)   => Username for the SSH host.
				passowrd(str)   => Password for the SSH host.
				port(int)       => Port for the SSH host (Default = 22)

			Returns:
				object
		"""
		self.host=host
		self.port=port
		self.username=username
		self.password=password
		self.ssh= netmiko.ConnectHandler(**{'device_type': 'cisco_ios', 'host': self.host, 'username': self.username, 'password': self.password, 'port': self.port, 'timeout': 300})

	def getRouteMapConfig(self, routeMapName: str="") -> str:
		"""
			Add the BGP community value to the targeted route-map/sequence.

			Arguments:
				routeMapName(str)       => The route-map you want to search, an empty value will return all the route-map (Default = "")

			Returns:
				str
		"""
		
		command: str="show running-config | section route-map {routeMapName}"
		return self.ssh.send_command(command.format(routeMapName=routeMapName))


def main(*args: str) -> None:
	"""
		Main function for the script.

		Arguments:
			args(str) => To pass any argument to the script. Does not have any effect.

		Returns:
			None
	"""
	## Variables
	routeMapName: str="TEST_REPLICATION_BUG_NETCONF"
	netconfHost: str=""
	netconfPort: int=10000
	netconfUsername: str=""
	netconfPassword: str=""
	nc: object=netconf(
		host=netconfHost,
		username=netconfUsername,
		password=netconfPassword,
		port=netconfPort
	)
	sshHost: str=netconfHost
	sshPort: int=8181
	sshUsername: str=netconfUsername
	sshPassword: str=netconfPassword
	sshSession: object=ssh(
		host=sshHost,
		username=sshUsername,
		password=sshPassword,
		port=sshPort
	)
	communities: list       # used to store the communities
	community: str          # used as a counter

	## Message header to display when lauching the script
	print("""
======================================== Cisco NETCONF Bug ========================================
  This script is created to demonstrate the bug with NETCONF implementation on Cisco devices
  running IOS-XE. This script is meant to be used with the Cisco DevNet sandbox by default. Refer
  to the README file before running the script.

  Lines starting with a double star (**) represent an action done by the system.

  Warning: the script will erase any route-map with the same name. Do not run on a production
           environment unless you understand the risk.
===================================================================================================
""")

	##
	## PREPARATION TO EXECUTE THE SCRIPT
	##   This section will erase the route-map and put the BGP Community new-format value
	##

	print("\n ==== Initialization ====\n")

	## Make sure the BGP community new-format is turned-off
	print("    ** BGP Community New-Format set to default\n")
	nc.setBGPCommunityNewFormat(delete=True)

	## Clean-up any previous route-map with the same name
	print("    ** Delete previous route-map with the same name\n")
	nc.setRouteMap(routeMapName=routeMapName, delete=True)

	##
	## DEMO #1
	##   This demo shows what happen when you switch to "ip bgp-community new-format"
	##   1. Set the community value to 655370
	##   2. Get the list before the modification
	##   2. Set the bgp-community new-format
	##   3. Get the list after the modification
	##

	print("\n ==== Demo #1 ====\n")

	## Create the route-map with a "set" of the BGP community "655370" (equivalent to 10:10)
	print("    ** Creation of the route-map with the BGP community \"655370\"\n")
	nc.setRouteMapBGPCommunity(routeMapName=routeMapName, BGPCommunity="655370")

	## Get the list of BGP Community via NETCONF
	print("    Here is the list of the BGP community from a NETCONF standpoint:")
	communities = nc.getRouteMapBGPCommunity(routeMapName=routeMapName, routeMapSequence=10)
	for community in communities:
		print("       - " + community)
		pass
	
	## Get the route-map configuration
	print("\n    Here is the configuration from the CLI:")
	print("#########################\n" + sshSession.getRouteMapConfig("TEST_REPLICATION_BUG_NETCONF") + "\n#########################\n")

	## Enable the BGP community new-format
	print("    ** Enabling the BGP community new-format\n")
	nc.setBGPCommunityNewFormat()

	## Get the list of BGP Community after the command execution
	print("    After the modification, it remains the same:")
	communities = nc.getRouteMapBGPCommunity(routeMapName=routeMapName, routeMapSequence=10)
	for community in communities:
		print("       - " + community)
		pass

	## Get the route-map configuration after the command execution
	print("\n    But the CLI shows the expected result:")
	print("#########################\n" + sshSession.getRouteMapConfig("TEST_REPLICATION_BUG_NETCONF") + "\n#########################\n")

	##
	## DEMO #2
	##   This demo shows that we can duplicate the communitie values
	##   1. Add "10:10" (equivalent to 655370)
	##   2. Get the list after the modification
	##

	print("\n ==== Demo #2 ====\n")

	## Add "10:10"
	print("    ** Adding a duplicate entry \"10:10\" (which is equivalent to 655370)\n")
	nc.setRouteMapBGPCommunity(routeMapName=routeMapName, BGPCommunity="10:10")

	## Get the list of BGP Community after the command execution
	print("    After adding the BGP community, there is a duplicate entry in the system (from a NETCONF standpoint):")
	communities = nc.getRouteMapBGPCommunity(routeMapName=routeMapName, routeMapSequence=10)
	for community in communities:
		print("       - " + community)
		pass

	## Get the route-map configuration
	print("\n    But the CLI shows only one:")
	print("#########################\n" + sshSession.getRouteMapConfig("TEST_REPLICATION_BUG_NETCONF") + "\n#########################\n")

	##
	## DEMO #3
	##   This demo shows that deleting one of the duplicate does not remove from the list
	##   1. Delete "10:10" (equivalent to 655370)
	##   2. Get the list after the modification
	##

	print("\n ==== Demo #3 ====\n")

	## Remove "10:10"
	print("    ** Removing the entry \"10:10\" (which is equivalent to 655370)\n")
	nc.setRouteMapBGPCommunity(routeMapName=routeMapName, BGPCommunity="10:10", delete=True)

	## Get the list of BGP Community after the command execution
	print("    After removing the BGP community \"10:10\", it remains used by the system because NETCONF still have 655370.")
	print("    However, NETCONF only shows \"655370\" now:")
	communities = nc.getRouteMapBGPCommunity(routeMapName=routeMapName, routeMapSequence=10)
	for community in communities:
		print("       - " + community)
		pass

	## Get the route-map configuration
	print("\n    The CLI still shows no \"set\" statement:")
	print("#########################\n" + sshSession.getRouteMapConfig("TEST_REPLICATION_BUG_NETCONF") + "\n#########################\n")

	##
	## DEMO #4
	##   This demo shows that NETCONF does not convert when the new-format is disabled.
	##   1. Re-add "10:10" (equivalent to 655370)
	##   2. Delete "655370" (equivalent to 10:10)
	##   3. Disable the BGP-Community new-format
	##   4. Get the list after the modification
	##

	print("\n ==== Demo #4 ====\n")

	## Re-add "10:10"
	print("    ** Re-add the entry \"10:10\" (which is equivalent to 655370)")
	nc.setRouteMapBGPCommunity(routeMapName=routeMapName, BGPCommunity="10:10")

	## Delete "655370"
	print("\n    ** Delete the entry \"655370\" (which is equivalent to 10:10)")
	nc.setRouteMapBGPCommunity(routeMapName=routeMapName, BGPCommunity="655370", delete=True)

	## Remove the BGP community new-format
	print("\n    ** Set the ip bgp-community new-format to none")
	nc.setBGPCommunityNewFormat(delete=True)

	## Get the list of BGP Community after the command execution
	print("\n    After reverting to the new-format to \"disabled\", it keeps the new-format in the NETCONF database:")
	communities = nc.getRouteMapBGPCommunity(routeMapName=routeMapName, routeMapSequence=10)
	for community in communities:
		print("       - " + community)
		pass

	## Get the route-map configuration
	print("\n    And the CLI shows nothing like \"Demo #3\" :")
	print("#########################\n" + sshSession.getRouteMapConfig("TEST_REPLICATION_BUG_NETCONF") + "\n#########################\n")

	##
	## DEMO #5
	##   This demo shows that NETCONF does not re-apply the configuration.
	##   1. Keep "10:10" (equivalent to 655370)
	##   2. Re-add the BGP-Community new-format
	##   3. Get the list after the modification
	##

	print("\n ==== Demo #5 ====\n")

	## Re-add the BGP community new-format
	print("\n    ** Set the ip bgp-community new-format")
	nc.setBGPCommunityNewFormat()

	## Get the list of BGP Community after the command execution
	print("\n    Now, let's see the BGP community list as per NETCONF:")
	communities = nc.getRouteMapBGPCommunity(routeMapName=routeMapName, routeMapSequence=10)
	for community in communities:
		print("       - " + community)
		pass

	## Get the route-map configuration
	print("\n    And the CLI still shows nothing even though the new-format has been re-added :")
	print("#########################\n" + sshSession.getRouteMapConfig("TEST_REPLICATION_BUG_NETCONF") + "\n#########################\n")

	##
	## DEMO #6
	##   This demo shows what happens after re-applying the community
	##   1. Keep "10:10" (equivalent to 655370)
	##   2. Re-add the BGP-Community new-format
	##   3. Get the list after the modification
	##

	print("\n ==== Demo #6 ====\n")

	## Re-add "10:10"
	print("    ** Let's try to resend the entry \"10:10\" via NETCONF (which is equivalent to 655370)")
	nc.setRouteMapBGPCommunity(routeMapName=routeMapName, BGPCommunity="10:10")

	## Get the list of BGP Community after the command execution
	print("\n    As expected, it is present via NETCONF:")
	communities = nc.getRouteMapBGPCommunity(routeMapName=routeMapName, routeMapSequence=10)
	for community in communities:
		print("       - " + community)
		pass

	## Get the route-map configuration
	print("\n    But it is still not showing even after reapplying the configuration:")
	print("#########################\n" + sshSession.getRouteMapConfig("TEST_REPLICATION_BUG_NETCONF") + "\n#########################\n")

	##
	## CLEAN-UP & END THE SCRIPT
	##   This section will remove the route-map and default the BGP Community new-format value
	##

	print("\n ==== Clean-up and exit ====\n")

	## Remove the route-map created by the script
	print("    ** Remove the route-map")
	nc.setRouteMap(routeMapName=routeMapName, delete=True)

	## Remove the BGP community new-format command added
	print("\n    ** Set the ip bgp-community new-format to default")
	nc.setBGPCommunityNewFormat(delete=True)



if __name__ == '__main__':
	main()