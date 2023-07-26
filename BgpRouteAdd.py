#!/usr/bin/env python3
#
# Copyright (c) 2016-2021 Juniper Networks, Inc.
# All rights reserved.
#
# BgpRouteAdd.py
#
# This application injects routes into BGP.
#
# Notes:
# - Currently, routes are added and removed in singlular, non-bulked
#   operations. It could be extended to add/remove in the bulk requests
#   based on the bulked monitor entries.
# - The configs below use the hidden 'clear-text' connection for
#   demo purposes only. The 'ssl' option is recommended for all other uses.
#
# Options:
# - '-H <SVR-ADDR>' or '--host <SVR-ADDR>': Specify router management address.
# - '-P <PORT>' or '--port <PORT>': Specify router GRPC port.
# - '-I True|False' or '--interactive True|False': Whether to get inputs
#                                                  interactively (default True)
#
# Necessary router configs:
#   set system services extension-service request-response grpc clear-text
#
# Additional necessary router configs for scripts running on-box:
#   set system scripts language python3
#   set system extensions extension-service application file BgpRouteAdd.py
#   (copy script to /var/run/scripts/jet/ and chown to root)
#
# To set optional script parameters:
#   set system extensions extension-service application file
#     BgpRouteAdd.py arguments "--host <SVR-ADDR> --port <SVR-PORT>"
#
# Run the script on the router with:
#   request extension-service start BgpRouteAdd.py
#

import time, sys, glob
import os, random
import optparse
import netaddr
import socket
import grpc

import sys
sys.path.append('./proto/proto1')

import bgp_route_service_pb2
import bgp_route_service_pb2_grpc
import prpd_common_pb2
import prpd_common_pb2_grpc
import jnx_addr_pb2
import jnx_addr_pb2_grpc
import authentication_service_pb2
import authentication_service_pb2_grpc

parser = optparse.OptionParser()
parser.add_option('-H', '--host', action="store", dest="HOST",
                  help="Server host address", default="localhost")
parser.add_option('-P', '--port', action="store", dest="PORT",
                  help="Server GRPC port", default="50051")
parser.add_option('-I', '--interactive', action="store", dest="interactive",
                  help="Interactive operation", default="True")
(options, args) = parser.parse_args()

CLIENT_ID = '100'
USER = 'user1'
PASSWORD = 'passwd1'
TIMEOUT = 10
SLEEP = 10

# Route parameters
num_routes = 1
base_ipv4_addr = '99.0.0.1'
prefix_len = 32
table = 'inet.0'
next_hop = '10.255.255.1'
local_pref = 200
route_pref = 10
commListStr = None
asPathStr = ''
originator = '10.255.255.1'
cluster = '10.255.255.7'
num_paths = 1
rt_type = 'int'
med = 0

if options.interactive == 'True':
    read_in = input('Number of routes (1):')
    if read_in != '':
        num_routes = int(read_in)
    read_in = input('Base IPv4 address (99.0.0.1):')
    if read_in != '':
        base_ipv4_addr = read_in
    read_in = input('Prefix length (32):')
    if read_in != '':
        prefix_len = int(read_in)
    read_in = input('Route table (inet.0):')
    if read_in != '':
        table = read_in
    read_in = input('Number of paths per prefix (1):')
    if read_in != '':
        num_paths = int(read_in)
    read_in = input('Route type: int|ext (int):')
    if read_in != '':
        rt_type = read_in
    read_in = input('Next-hop (10.255.255.1):')
    if read_in != '':
        next_hop = read_in
    read_in = input('Incoming AS Path (none):')
    if read_in != '':
        asPathStr = read_in
    read_in = input('MED (0):')
    if read_in != '':
        med = int(read_in)
    read_in = input('Communities, space separated (none):')
    if read_in != '':
        commListStr = read_in
    if (rt_type is 'int'):
        read_in = input('Originator or none (10.255.255.1):')
        if read_in != '':
            originator = read_in
        read_in = input('Cluster ID or none (10.255.255.7):')
        if read_in != '':
            cluster = read_in
    else:
        originator = 'none'
        cluster = 'none'

def RouteInit(bgp):
    print('############## INVOKING BgpRouteInitialize API #############')
    strBgpReq = bgp_route_service_pb2.BgpRouteInitializeRequest()
    result = bgp.BgpRouteInitialize(strBgpReq, timeout=TIMEOUT)
    print('BgpRouteInitialize API return = %d' % result.status)
    if ((result.status != bgp_route_service_pb2.BgpRouteInitializeReply.SUCCESS) and
        (result.status != bgp_route_service_pb2.BgpRouteInitializeReply.SUCCESS_STATE_REBOUND)):
        print('Error on Initialize')

def RouteCleanup(bgp):
    print('############## INVOKING BgpRouteCleanup API ################')
    strBgpReq = bgp_route_service_pb2.BgpRouteCleanupRequest()
    result = bgp.BgpRouteCleanup(strBgpReq, timeout=TIMEOUT)
    print('BgpRouteCleanup API return = %d' % result.status)
    if result.status != bgp_route_service_pb2.BgpRouteCleanupReply.SUCCESS:
        print('Error on Cleanup')

def RouteAdd(bgp):
    addr_int = int(netaddr.IPAddress(base_ipv4_addr))
    for i in range(num_routes):
        addr_str = str(netaddr.IPAddress(addr_int))
        addr_int += 1
        destPrefix = prpd_common_pb2.RoutePrefix(inet=jnx_addr_pb2.IpAddress(addr_string=addr_str))
        destTable = prpd_common_pb2.RouteTable(rtt_name=prpd_common_pb2.RouteTableName(name=table))
        if rt_type == "ext":
            routeType = bgp_route_service_pb2.BGP_EXTERNAL
        else:
            routeType = bgp_route_service_pb2.BGP_INTERNAL
        if med != 0:
            med_met = bgp_route_service_pb2.BgpAttrib32(value=med)
        else:
            med_met = None
        nh_addr_int = int(netaddr.IPAddress(next_hop))
        for p in range(num_paths):
            nh_addr_str = str(netaddr.IPAddress(nh_addr_int))
            nh_addr_int += 2
            nextHopIp = jnx_addr_pb2.IpAddress(addr_string=nh_addr_str)
            routeParams = bgp_route_service_pb2.BgpRouteEntry(
                dest_prefix = destPrefix, dest_prefix_len = 32,
                table = destTable,
                protocol_nexthops = [nextHopIp],
                path_cookie = p + 1,
                route_type = routeType,
                local_preference = bgp_route_service_pb2.BgpAttrib32(value=local_pref),
                route_preference = bgp_route_service_pb2.BgpAttrib32(value=route_pref),
                med = med_met,
                protocol = bgp_route_service_pb2.PROTO_BGP_STATIC,
                aspath = bgp_route_service_pb2.AsPath(aspath_string=asPathStr))
            if originator != 'none':
                routeParams.originator_id.value = socket.htonl(
                        int(netaddr.IPAddress(originator)))
            if cluster != 'none':
                routeParams.cluster_id.value = socket.htonl(
                        int(netaddr.IPAddress(cluster)))

            if commListStr:
                for comm in commListStr.split():
                    routeParams.communities.com_list.add().community_string = comm

            print('--------------------------------------------------')
            print('Add Route: %s/32 Path %d' % (addr_str, (p + 1)))
            routeUpdReq = bgp_route_service_pb2.BgpRouteUpdateRequest(bgp_routes=[routeParams])
            result = bgp.BgpRouteAdd(routeUpdReq, TIMEOUT)
            print('BgpRouteAdd API return = %d' % result.status)
            if result.status > bgp_route_service_pb2.BgpRouteOperReply.SUCCESS:
                print('Error on Add')

class Auth(object):
    def __init__(self, conn, user, password):
        self.conn = conn
        self.user = user
        self.password = password
        self.timeout = 60
        
    def grpc_login(self, client_id):
        auth_stub = authentication_service_pb2_grpc.LoginStub(self.conn)
        login_response = auth_stub.LoginCheck(
            authentication_service_pb2.LoginRequest(
            user_name=self.user,
            password=self.password,
            client_id=client_id), self.timeout)
        return login_response.result
                                                                
def Main():

    # Connect and Authenticate via TCP from on or off-box
    conn = grpc.insecure_channel('%s:%d' % (options.HOST,
                                            int(options.PORT)))
    a = Auth(conn, USER, PASSWORD)
    login = a.grpc_login(CLIENT_ID)

    # Create the BGP service stub
    bgp = bgp_route_service_pb2_grpc.BgpRouteStub(conn)

    # Init and begin adding routes
    if options.interactive == 'True':
        input('Enter to add BGP routes')
    RouteInit(bgp)
    RouteAdd(bgp)
    print('\nRoutes added, verify state on router.')

    if options.interactive == 'True':
        input('Enter to remove BGP routes')
    elif SLEEP != 0:
        print('Sleeping for %d seconds prior to removing BGP routes...' % SLEEP)
        time.sleep(SLEEP)

    # Cleanup
    RouteCleanup(bgp)

if __name__ == '__main__':
    Main()
