#!/bin/bash

if [ "$1" ]; then
echo "Removing extra stuff"
rm -rf monitor/monitor.pid
pkill -f stress
pkill -f cgmon
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RELEASE_AGENT="/usr/local/bin/cgmon-cgroup-cb"
MPATH="/sys/fs/cgroup/monitor"

mount -o remount,rw /sys/fs/cgroup
mkdir -p $MPATH
if ! mountpoint -q $MPATH ; then
    if ! mount -n -t cgroup -o none,rw,nosuid,nodev,noexec,relatime,xattr,release_agent=$RELEASE_AGENT,name=monitor monitor $MPATH ; then
        echo "ERROR: Could not mount monitor hierarchy" && exit 1
    fi
fi
#echo "$DIR/cgmond/scripts/cb.py" > /sys/fs/cgroup/monitor/release_agent
echo "$RELEASE_AGENT" > $MPATH/release_agent
echo 1 > $MPATH/notify_on_release
mkdir -p $MPATH/monitor
