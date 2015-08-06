#!/bin/bash
# In order to be able to connect to public IP of Installer host 
# after vnic reconfiguration we also need to swap 
# network config in /etc/sysconfig/network-script/ifcfg-...
# Beacuse Fuel uses 1st interface as a public and foreman 3rd.


PUBLIC_GW='172.30.10.1'
NET_RECONF_LOG=/var/log/net_reconf.log

function swap_ifcfg()
{
    local src=/etc/sysconfig/network-scripts/ifcfg-enp6s0
    local dst=/etc/sysconfig/network-scripts/ifcfg-enp8s0
    echo swap configs of $src and $dst
    mv $src ${src}_backup && mv $dst $src && mv ${src}_backup $dst
    /etc/init.d/network restart
}


function gw_reachable()
{
    if ping -c 1 $PUBLIC_GW; then
        echo "OK. Gateway is Reachable."
        exit 0
    else
        swap_ifcfg
        return 1
    fi  
}


date > $NET_RECONF_LOG
n=0
until gw_reachable || [ $n -eq 2 ]; do
    echo "Trying again..."
    (( n++ ))
done 2>&1 >> $NET_RECONF_LOG

echo "ERROR: Cannot ping default GW" >> $NET_RECONF_LOG
