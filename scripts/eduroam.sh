#!/bin/bash

if [ $1 == "d" ]
then
    echo disconnecting...
    sudo airmon-ng check kill
    sudo systemctl start NetworkManager
elif [ $1 == "c" ]
then
    echo connecting...
    sudo systemctl stop NetworkManager
    sudo wpa_supplicant -B -i wlp2s0 -c /home/zan/.config/cat_installer/cat_installer.conf
    sudo dhcpcd wlp2s0
fi


