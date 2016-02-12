#!/usr/bin/env python

import os
import sys
import argparse
import prettytable
from operator import itemgetter, attrgetter
from collections import defaultdict
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
    parser = argparse.ArgumentParser(description='OpenStack Nova instance information')
    parser.add_argument('--hypervisor', type=str, help='List instances on a given hypervisor')
    parser.add_argument('--tenant', type=str, help='List instances belonging to a given tenant ID')
    parser.add_argument('--all', action='store_true', help='List all instances along with project ID, name, and hypervisor')
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
        fields = ['Instance ID', 'Tenant ID', 'Project ID', 'Hypervisor']
        pt = prettytable.PrettyTable(fields, caching=False)
        pt.align = 'l'
        instances = get_instances()
        for k, v in instances.items():
            pt.add_row([k, v[0], v[1], v[2]])
        print pt
