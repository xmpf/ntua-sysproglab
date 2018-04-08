#!/bin/bash

group="kvm"
mode="664"

# if `kvm` not a valid group, default is `wheel`
grep -q '^kvm:' /etc/group || group="wheel"

# Make sure the node for the first serial port is there.
mknod /dev/ttyS0 c 4 64

# Lunix:TNG nodes: 16 sensors, each has 3 nodes.
for sensor in $(seq 0 1 15); do
	mknod /dev/lunix$sensor-batt c 60 $[$sensor * 8 + 0]
	mknod /dev/lunix$sensor-temp c 60 $[$sensor * 8 + 1]
	mknod /dev/lunix$sensor-light c 60 $[$sensor * 8 + 2]
done

# setting permissions
chgrp $group /dev/lunix${sensor}-{batt,temp,light}
chmod $mode  /dev/lunix${sensor}-{batt,temp,light}
