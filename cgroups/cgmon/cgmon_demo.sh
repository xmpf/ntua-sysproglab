#!/bin/bash

set -v

WD=/root/cgroups

cgmon daemon stop -w ${WD}

sleep 1

cgmon daemon start -w ${WD} -p ${WD}/cpu_policy.py -l ${WD}/cpu_limit.py

sleep 1

cgmon app list

sleep 1

# assuming total 2000 millicpus == 2 cpus
cgmon policy create -n platinum -p 1000
cgmon policy create -n silver -p 500
cgmon policy create -n elastic -p 50
cgmon policy list

sleep 1

cgmon app spawn -p platinum -e "stress -c 2" -n BANKDB
cgmon app spawn -p silver -e "stress -c 2" -n WEBDB
cgmon app spawn -p elastic -e "stress -c 2" -n VIDEOENC
cgmon app spawn -p elastic -e "stress -c 2" -n SPAMBOT
cgmon app list

sleep 5

# This should fail: not enough cpu
cgmon app spawn -p platinum -e "stress -c 2" -n MEDICALDB

sleep 1

# forcing it violates policies
cgmon app spawn -p platinum -e "stress -c 2" -n MEDICALDB -f

sleep 10
pkill -f stress
