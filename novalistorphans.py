#!/usr/bin/env python

import os
import sys
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

def get_tenantids():
    return [tenant.id for tenant in keystone.tenants.list()]

def get_orphaned_nova_instances():
    orphans = []
    tenantids = get_tenantids()
    for server in nova.servers.list(search_opts={'all_tenants': 1}):
        if server.tenant_id not in tenantids:
                orphans.append(server.id)
    return orphans

if __name__ == '__main__':
    orphans = get_orphaned_nova_instances()
    print len(orphans), 'orphan(ed) instance(s) found'
    print '\n'.join(map(str, orphans))
