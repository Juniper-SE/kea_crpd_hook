#!/bin/bash


#echo "Script called with:"
#echo $@
#env


case "$1" in
    "leases4_committed")
	echo "$1 : $LEASES4_AT0_ADDRESS"
        echo $LEASES4_AT0_ADDRESS > /tmp/myfifo
        ;;
    *)
	echo "Doing nothing, script called with: ${*}"
        ;;
esac
