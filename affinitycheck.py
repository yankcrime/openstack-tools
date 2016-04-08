#!/usr/bin/env python

import os
import sys
import argparse
import prettytable
from operator import itemgetter, attrgetter
from collections import defaultdict, Counter
from keystoneclient import session
from keystoneclient.auth.identity import v2
from keystoneclient.v2_0 import client as ksclient
from novaclient import client as nclient

def get_credentials():
    d = {}
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['username'] = os.environ['OS_USERNAME']
    d['password'] = os.environ['OS_PASSWORD']
    d['tenant_name'] = os.environ['OS_TENANT_NAME']
    return d

credentials = get_credentials()
keystone = ksclient.Client(**credentials)
auth = v2.Password(**credentials)
sess = session.Session(auth=auth)
nova = nclient.Client(2, session=sess)

def get_args():
    parser = argparse.ArgumentParser(description="Affinity rule checker")
    parser.add_argument('--check', type=str)
    parser.add_argument('--list', type=str)
    return parser.parse_args()

def get_server(serverid):
    return nova.servers.get(serverid)

def get_group_members(groupid):
    server_group = nova.server_groups.get(groupid)
    return server_group.members

def print_group_members(server_group_id):
    fields = ['Instance ID', 'Instance', 'Hypervisor']
    pt = prettytable.PrettyTable(fields, caching=False)
    pt.align = 'l'
    for server in get_group_members(server_group_id):
        instance = get_server(server)
        hypervisor = getattr(instance, 'OS-EXT-SRV-ATTR:hypervisor_hostname'.split('.')[0])
        pt.add_row([instance.id, instance.name, hypervisor])
    print pt

def print_group_duplicates(server_group_id):
    hypervisors = []
    instances = defaultdict(list)
    for instance in get_group_members(server_group_id):
        cur = get_server(instance)
        instances[instance].append(cur.name)
        instances[instance].append(getattr(cur, 'OS-EXT-SRV-ATTR:hypervisor_hostname'))
    for instance_id, [instance_name, hypervisor] in instances.items():
        hypervisors.append(hypervisor)
    dupes = [k for k, v in Counter(hypervisors).items() if v > 1]
    if dupes:
        print "Anti-affinity rules violated in Server Group", server_group_id, ":"
        fields = ['Instance ID', 'Instance', 'Hypervisor']
        pt = prettytable.PrettyTable(fields, caching=False)
        pt.align = 'l'
        for instance_id, [instance_name, hypervisor] in instances.items():
            if hypervisor in dupes:
                pt.add_row([instance_id, instance_name, hypervisor])
        print pt
    else:
        print "No anti-affinity rules violated for Server Group", server_group_id, "."

if __name__ == '__main__':
    args = get_args()
    group = sys.argv[2]
    if args.check:
        print_group_duplicates(group)
    if args.list:
        print_group_members(group)
