#! /bin/bash

# simple script for demonstration purposes

DEVICES="$(ls /dev/lunix* | sort)"
for i in $DEVICES; do
	echo "Reading from "$i
	timeout -s 9 5s cat $i
	echo ""
	sleep 2
done
