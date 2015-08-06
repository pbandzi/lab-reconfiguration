##Script for adding to systemd. Suppose to be executed during startup and swap interface config if neccessar

To add into systemd copy files to:

/usr/lib/systemd/scripts/swap_public_ifcfg.sh

/usr/lib/systemd/system/swap_public_ifcfg.service


And enable service:

systemctl enable swap_public_ifcfg.service

