#!/usr/bin/env bash

ROUTER=$1

neutron router-gateway-clear $ROUTER
for PORT in $(neutron router-port-list -F fixed_ips $ROUTER | awk '{ print $3 }' | tr -d '\n|",') ; do
		neutron router-interface-delete $ROUTER $PORT
done
neutron router-delete $ROUTER
