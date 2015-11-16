#!/usr/bin/env python

import os
import sys
import argparse
from operator import itemgetter, attrgetter
from collections import defaultdict
from pprint import pprint
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
    parser = argparse.ArgumentParser(description='Instance information')
    parser.add_argument('--hypervisor', type=str, help='FQDN of hypervisor')
    parser.add_argument('--tenant', type=str, help='Tenant ID')
    parser.add_argument('--all', action='store_true')
    return parser.parse_args()

def get_tenants():
    tenants = {}
    for tenant in keystone.tenants.list():
        tenants[tenant.id] = tenant.name
    return tenants

def get_instances():
    tenants = get_tenants()
    instances = defaultdict(list)
    for server in nova.servers.list(search_opts={'all_tenants': 1}):
        instances[server.id].append(server.tenant_id)
        instances[server.id].append(tenants.get(server.tenant_id))
        instances[server.id].append(getattr(server, 'OS-EXT-SRV-ATTR:hypervisor_hostname').split('.')[0])
    return instances

def get_tenant_instances(tenantid):
    tenantinstances = []
    instances = get_instances()
    for k, m in instances.iteritems():
        if m[0] == tenantid:
            tenantinstances.append(k)
    return tenantinstances

def get_hypervisor_instances(hypervisor):
    hypervisorinstances = []
    instances = get_instances()
    for k, m in instances.iteritems():
        if hypervisor in m[2]:
            hypervisorinstances.append(k)
    return hypervisorinstances

if __name__ == '__main__':
    args = get_args()
    if args.hypervisor:
        hypervisorinstances = get_hypervisor_instances(args.hypervisor)
        print len(hypervisorinstances), 'instance(s) running on hypervisor:', args.hypervisor
        print '\n'.join(map(str, hypervisorinstances))
    if args.tenant:
        tenantinstances = get_tenant_instances(args.tenant)
        print len(tenantinstances), 'instance(s) owned by tenant ID:', args.tenant
        print '\n'.join(map(str, tenantinstances))
    if args.all:
        instances = get_instances()
        col_width = 0
        for k, m in instances.iteritems():
            maxcol = max(len(v) for v in m)
            if maxcol > col_width:
                col_width = maxcol
        for instance in instances:
            print instance,
            for m in instances[instance]:
                print m.ljust(col_width),
            print '\n',
