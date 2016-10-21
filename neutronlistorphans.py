#!/usr/bin/env python

import os
import sys

from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client
import neutronclient.neutron.client

auth = v3.Password(auth_url=os.environ['OS_AUTH_URL'],
                   username=os.environ['OS_USERNAME'],
                   password=os.environ['OS_PASSWORD'],
                   project_name=os.environ['OS_PROJECT_NAME'],
                   user_domain_id=os.environ['OS_USER_DOMAIN_NAME'],
                   project_domain_name=os.environ['OS_PROJECT_DOMAIN_NAME'])

session = session.Session(auth=auth)

keystone = client.Client(session=session)
neutron = neutronclient.neutron.client.Client('2.0', session=session)

def usage():
    print "listorphans.py <object> where object is one or more of",
    print "'networks', 'routers', 'subnets', 'floatingips' or 'all'"

def get_projectids():
    return [project.id for project in keystone.projects.list()]

def get_orphaned_neutron_objects(object):
    projectids = get_projectids()
    objects = getattr(neutron, 'list_' + object)()
    orphans = []
    for object in objects.get(object):
        if object['tenant_id'] not in projectids:
            orphans.append(object['id'])
    return orphans

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'all':
            objects = [ 'networks', 'routers', 'subnets', 'floatingips' ]
        else:
            objects = sys.argv[1:]
        for object in objects:
            orphans = get_orphaned_neutron_objects(object)
            print len(orphans), 'orphan(s) found of type', object
            print '\n'.join(map(str, orphans))
    else:
        usage()
        sys.exit(1)
