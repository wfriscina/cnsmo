import getopt
import logging
import shlex
import subprocess
import iptools

import sys
from flask import Flask
from flask import json
from flask import request

log = logging.getLogger('cnsmoservices.fw.app.server')


app = Flask(__name__)

GET = "GET"
POST = "POST"
DELETE = "DELETE"

DIRECTION = "direction"
PROTOCOL = "protocol"
DST_PORT = "dst_port"
IP_RANGE = "ip_range"
ACTION = "action"
DEST_SRC = "dst_src"
POLICY = "policy"

RULE_FORMAT = '{"direction":"in/out", "protocol":"tcp/udp/...", "dst_port":"[0,65535]", "dst_src":"dst/src",' \
              '"ip_range":"cidr_notation", "action":"drop/acpt"} or {"policy":"denyall"}'


@app.route("/fw/build/", methods=[POST])
def build_server():
    try:
        if app.config["service_built"]:
            return "Service already built", 409
        if app.config["service_building"]:
            return "Service is being built", 409

        app.config["service_building"] = True
        log.debug("building docker...")
        subprocess.check_call(shlex.split("docker build -t fw-docker ."))
        log.debug("docker built")
        app.config["service_built"] = True
        app.config["service_building"] = False
        return "", 204
    except Exception as e:
        return str(e), 500


@app.route("/fw/", methods=[POST])
def add_rule():
    if not app.config["service_built"]:
        return "Service is not yet built", 409

    rule = json.loads(request.data)
    if not is_valid(rule):
        return "Invalid rule. Expected format is {}".format(RULE_FORMAT), 400

    try:
        command = "docker run -t --rm --net=host --privileged fw-docker"
        if is_valid_policy(rule):
            arguments = " -p {policy}".format(**rule)
        else:
            arguments = " add {direction} {protocol} {dst_port} {dst_src} {ip_range} {action}".format(**rule)

        log.debug("running docker add...")
        output = subprocess.check_call(shlex.split(command + arguments))
        log.debug("docker run. output: " + str(output))
        return "", 204
    except Exception as e:
        return str(e), 500


@app.route("/fw/", methods=[DELETE])
def delete_rule():
    if not app.config["service_built"]:
        return "Service is not yet built", 409

    rule = json.loads(request.data)
    if not is_valid(rule):
        return "Invalid rule. Expected format {}".format(RULE_FORMAT), 400

    if is_valid_policy(rule):
        return "Unsupported operation. Cannot delete policy", 409

    try:
        command = "docker run -t --rm --net=host --privileged fw-docker"
        arguments = " del {direction} {protocol} {dst_port} {dst_src} {ip_range} {action}".format(**rule)

        log.debug("running docker DEL...")
        output = subprocess.check_call(shlex.split(command + arguments))
        log.debug("docker run. output: " + str(output))
        return "", 204

    except Exception as e:
        return str(e), 500


def is_valid(rule):
    valid = is_valid_policy(rule)
    if not valid:
        valid = is_valid_rule(rule)
    return valid


def is_valid_rule(rule):
    # check rule contains all mandatory fields
    if not {DIRECTION, PROTOCOL, DST_PORT, DEST_SRC, IP_RANGE, ACTION}.issubset(set(rule.keys())):
        return False

    if rule[DIRECTION] not in ('in', 'out'):
        return False

    if rule[ACTION] not in ('drop', 'acpt'):
        return False

    if rule[DEST_SRC] not in ('dst', 'src'):
        return False

    # Support port ranges in the form port1:portN
    dports = rule[DST_PORT].split(":")
    if len(dports) > 2:
        return False

    for dport in dports:
        # port is an int between 0 and 65535
        try:
            dst_port = int(dport)
            if dst_port < 0 or dst_port > 65535:
                return False
        except ValueError:
            return False

    # ip_range is a valid IP range in CIDR notation (IPv4 or IPv6)
    if not (iptools.ipv4.validate_cidr(rule[IP_RANGE]) or iptools.ipv6.validate_cidr(rule[IP_RANGE])):
        return False

    return True


def is_valid_policy(rule):
    if POLICY in rule.keys():
        if rule[POLICY] == "denyall":
            return True

    return False


def prepare_config():
    app.config["service_built"] = False
    app.config["service_building"] = False


if __name__ == "__main__":

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:")

    bind_address = "127.0.0.1"
    port = 9095
    for opt, arg in opts:
        if opt == "-a":
            bind_address = arg
        elif opt == "-p":
            port = int(arg)

    prepare_config()
    app.run(host=bind_address, port=port, debug=True)
