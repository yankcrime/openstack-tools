#!/usr/bin/env python

import os
import sys
from keystoneclient import session
from keystoneclient.auth.identity import v2
from keystoneclient.v2_0 import client as ksclient
from novaclient import client as nclient
from glanceclient import client as gclient

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
glance = gclient.Client(2, session=sess)

def get_tenantids():
    return [tenant.id for tenant in keystone.tenants.list()]

def get_orphaned_glance_images():
    orphans = []
    tenantids = get_tenantids()
    for image in glance.images.list():
        if image.owner not in tenantids:
            orphans.append(image.id)
    return orphans

if __name__ == '__main__':
    orphans = get_orphaned_glance_images()
    print 'Found', len(orphans),' orphaned images.'
    print '\n'.join(map(str, orphans))
