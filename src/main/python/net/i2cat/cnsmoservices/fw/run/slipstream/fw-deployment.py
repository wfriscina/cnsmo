#!/usr/bin/env python

###
# This script is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
###

import subprocess
import threading
import time

from slipstream.SlipStreamHttpClient import SlipStreamHttpClient
from slipstream.ConfigHolder import ConfigHolder

call = lambda command: subprocess.check_output(command, shell=True)


def main():
    # TODO get this from slipstream context, by inspecting roles each component has
    server_instance_id = "CNSMO_server.1"

    launch_fw(server_instance_id)


def launch_fw(server_instance_id):
    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)

    date = call('date')
    f = None
    try:
        f = open("/tmp/cnsmo/fw.log", "w+")
        f.write("Waiting for CNSMO at %s" % date)
    finally:
        if f:
            f.close()

    call('ss-display \"Waiting for CNSMO...\"')
    call("ss-get --timeout=1800 %s:net.i2cat.cnsmo.core.ready" % server_instance_id)

    redis_address = call("ss-get %s:net.i2cat.cnsmo.dss.address" % server_instance_id).rstrip('\n')

    call('ss-display \"Deploying FW components...\"')

    hostname = call('ss-get hostname').rstrip('\n')

    date = call('date')
    f = None
    try:
        f = open("/tmp/cnsmo/fw.log", "a")
        f.write("Launching Firewall server at %s" % date)
    finally:
        if f:
            f.close()

    tc = threading.Thread(target=launchFWServer, args=(hostname, redis_address, instance_id))
    tc.start()
    # TODO implement proper way to detect when the server is ready (using systemstate?)
    time.sleep(1)
    call('ss-set net.i2cat.cnsmo.service.fw.server.listening true')

    date = call('date')
    f = None
    try:
        f = open("/tmp/cnsmo/fw.log", "a")
        f.write("FW deployed at %s" % date)
    finally:
        if f:
            f.close()

    call('ss-display \"FW: FW has been created!\"')
    print "FW deployed!"


def launchFWServer(hostname, redis_address, instance_id):
    call('ss-display \"FW: Launching FW server...\"')
    call("python cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/fw/run/server.py -a %s -p 9095 -r %s -s FWServer-%s" % (hostname, redis_address, instance_id))


main()
