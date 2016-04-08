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
    return nova.servers.find(id=serverid)

def get_group_members(groupid):
    server_group = nova.server_groups.get(groupid)
    return server_group.members

def print_group_members(server_group_id):
    fields = ['Instance', 'Instance ID', 'Hypervisor']
    pt = prettytable.PrettyTable(fields, caching=False)
    pt.align = 'l'
    for server in get_group_members(server_group_id):
        instance = get_server(server)
        hypervisor = getattr(instance, 'OS-EXT-SRV-ATTR:hypervisor_hostname'.split('.')[0])
        pt.add_row([instance.name, instance.id, hypervisor])
    print pt

def find_group_duplicates(server_group_id):
    hypervisors = []
    instances = get_group_members(server_group_id)
    for instance in instances:
        instance = get_server(instance)
        hypervisors.append(getattr(instance, 'OS-EXT-SRV-ATTR:hypervisor_hostname'))
    dupes = [k for k, v in Counter(hypervisors).items() if v > 1]
    return dupes

if __name__ == '__main__':
    args = get_args()
    group = sys.argv[2]
    if args.check:
        dupes = find_group_duplicates(group)
        if dupes:
            print "Affinity-rule for", group, "violated."
            print "Hypervisors: ",
            print ', '.join(dupes)
        else:
            print "No rules violated in server group", group
    if args.list:
        print print_group_members(group)
