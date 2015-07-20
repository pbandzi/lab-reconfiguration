#!/usr/bin/python
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This script reconfigure UCSM vnics for varios OPNFV deployers
# Usage: reconfigUcsNet.py [options]
#
# Options:
# -h, --help            show this help message and exit
# -i IP, --ip=IP        [Mandatory] UCSM IP Address
# -u USERNAME, --username=USERNAME
#                       [Mandatory] Account Username for UCSM Login
# -p PASSWORD, --password=PASSWORD
#                       [Mandatory] Account Password for UCSM Login
# -n NETWORK, --network=NETWORK
#                       [Optional] Network config you want to set for POD 
#                       Available options: FUEL, FOREMAN
#                       If not present only current network config will be printed
#

import getpass
import optparse
import platform
from UcsSdk import *
from collections import defaultdict
from UcsSdk.MoMeta.OrgOrg import OrgOrg
from UcsSdk.MoMeta.LsServer import LsServer
from UcsSdk.MoMeta.VnicEther import VnicEther
from UcsSdk.MoMeta.VnicEtherIf import VnicEtherIf

# Interfaces with assigned vnic templates.
networks = {
    "FUEL": ( 
            ("eth0","fuel-public"), 
            ("eth1","fuel-tagged") ),
    "FOREMAN": ( 
            ("eth0","foreman-storage"), 
            ("eth1","foreman-control"), 
            ("eth2","foreman-public"),
            ("eth3","foreman-traffic") )}

def getpassword(prompt):
    if platform.system() == "Linux":
        return getpass.unix_getpass(prompt=prompt)
    elif platform.system() == "Windows" or platform.system() == "Microsoft":
        return getpass.win_getpass(prompt=prompt)
    else:
        return getpass.getpass(prompt=prompt)


def get_servers(handle=None):
    """
    Return list of servers
    """
    orgObj = handle.GetManagedObject(None, OrgOrg.ClassId(), {OrgOrg.DN : "org-root"})[0]
    servers = handle.GetManagedObject(orgObj, LsServer.ClassId())
    for server in servers:
        if server.Type == 'instance' and "POD-2" in server.Dn:
            yield server

def get_vnics(handle=None, server=None):
    """
    Return list of vnics for given server
    """
    vnics = handle.ConfigResolveChildren(VnicEther.ClassId(), server.Dn, None, YesOrNo.TRUE)
    return vnics.OutConfigs.GetChild()


def get_network_config(handle=None):
    """
    Print current network config
    """
    print "\nCURRENT NETWORK CONFIG:"
    for server in get_servers(handle):
        print ' {}'.format(server.Name)
        for vnic in get_vnics(handle, server):
            print '  {}'.format(vnic.Name)
            print '   {}'.format(vnic.Addr)
            vnicIfs = handle.ConfigResolveChildren(VnicEtherIf.ClassId(), vnic.Dn, None, YesOrNo.TRUE)
            for vnicIf in vnicIfs.OutConfigs.GetChild():
                print '    Vlan: {}'.format(vnicIf.Vnet)


def add_interface(handle=None, lsServerDn=None, vnicEther=None, templName=None, order=None):
    """
    Add interface to server specified by server.DN name
    """
    print " Adding interface: {}, template: {}, server.Dn: {}".format(vnicEther, templName, lsServerDn)
    obj = handle.GetManagedObject(None, LsServer.ClassId(), {LsServer.DN:lsServerDn})
    vnicEtherDn = lsServerDn + "/ether-" + vnicEther
    params = {
        VnicEther.STATS_POLICY_NAME: "default", 
        VnicEther.NAME: vnicEther, 
        VnicEther.DN: vnicEtherDn, 
        VnicEther.SWITCH_ID: "A-B",
        VnicEther.ORDER: order,
        "adminHostPort": "ANY", 
        VnicEther.ADMIN_VCON: "any", 
        VnicEther.NW_TEMPL_NAME: templName, 
        VnicEther.MTU: "1500"}
    handle.AddManagedObject(obj, VnicEther.ClassId(), params, True)


def remove_interface(handle=None, vnicEtherDn=None):
    """
    Remove interface specified by Distinguished Name (vnicEtherDn)
    """
    print " Removing interface: {}".format(vnicEtherDn)
    obj = handle.GetManagedObject(None, VnicEther.ClassId(), {VnicEther.DN:vnicEtherDn})
    handle.RemoveManagedObject(obj)


def set_network(handle=None, network=None):
    """
    Configure VLANs on POD according specified network
    """
    # add interfaces and bind them with vNIC templates
    # TODO: make sure MAC address for admin is still same
    print "\nRECONFIGURING VNICs..."
    for server in get_servers(handle):
        desired_order = 1
        for iface, template in networks[network]:
            add_interface(handle, server.Dn, iface, template, desired_order)
            desired_order += 1
        # Remove other interfaces which have not assigned required vnic template
        vnics = get_vnics(handle, server)
        for vnic in vnics:
            if not any(tmpl in vnic.OperNwTemplName for iface, tmpl in networks[network]):
                remove_interface(handle, vnic.Dn)
                print "  {} removed, template: {}".format(vnic.Name, vnic.OperNwTemplName)


if __name__ == "__main__":    
    # Latest urllib2 validate certs by default 
    # The process wide "revert to the old behaviour" hook is to monkeypatch the ssl module
    # https://bugs.python.org/issue22417
    import ssl
    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context 
    try:
        handle = UcsHandle()
        parser = optparse.OptionParser()
        parser.add_option('-i', '--ip',dest="ip",
                        help="[Mandatory] UCSM IP Address")
        parser.add_option('-u', '--username',dest="userName",
                        help="[Mandatory] Account Username for UCSM Login")
        parser.add_option('-p', '--password',dest="password",
                        help="[Mandatory] Account Password for UCSM Login")
        parser.add_option('-n', '--network',dest="network",
                        help="[Optional] Network config you want to set on UCS POD1 [fuel or foreman]")
        (options, args) = parser.parse_args()

        if not options.ip:
            parser.print_help()
            parser.error("Provide UCSM IP Address")
        if not options.userName:
            parser.print_help()
            parser.error("Provide UCSM UserName")
        if not options.password:
            options.password=getpassword("UCSM Password:")

        handle.Login(options.ip, options.userName, options.password)

        if (options.network != None):           
            set_network(handle, options.network.upper())
        get_network_config(handle)       
        
        handle.Logout()

    except Exception, err:
        handle.Logout()
        print "Exception:", str(err)
        import traceback, sys
        print '-'*60
        traceback.print_exc(file=sys.stdout)
        print '-'*60
