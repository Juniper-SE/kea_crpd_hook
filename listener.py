#!/usr/bin/python3

import sys
sys.path.append('./proto/proto2')


import argparse
import grpc
import paho.mqtt.client as mqtt
import json
from pprint import pprint


#import authentication_service_pb2
#import bgp_route_service_pb2
#import prpd_common_pb2
#import jnx_addr_pb2

import jnx_authentication_service_pb2
import jnx_routing_bgp_service_pb2
import 


#import bgp_route_service_pb2
#import bgp_route_service_pb2_grpc
#import prpd_common_pb2
#import prpd_common_pb2_grpc
#import jnx_addr_pb2
#import jnx_addr_pb2_grpc
#import authentication_service_pb2
#import authentication_service_pb2_grpc


TIMEOUT = 10


def send_to_crpd(msg):
    print ("payload =",msg.payload)
    #data = json.loads(json_msg.decode('UTF-8'))
    json_string = msg.payload.decode('UTF-8')
    data = json.loads(json_string)
    pprint (data)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("dhcp_server")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

    send_to_crpd(msg)


### JET ###




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', help="Juniper BGP instance", type=str, default="localhost")
    parser.add_argument('--port', help="Server GRPC port", type=int, default=50051)
    parser.add_argument('--username', help="Username", type=str, default="user1")
    parser.add_argument('--password', help="Password", type=str, default="passwd1")
    parser.add_argument('--client_id', help="Client_id", default="100")
    args = parser.parse_args()
    

    try:
        # open gRPC channel
        print("")
        print(__file__)
        print("Trying to Login to", args.device, "port",
              args.port, "as user", args.username, "... ", end='')
        channel = grpc.insecure_channel('%s:%d' % (args.device, args.port))
        auth_stub = authentication_service_pb2.LoginStub(channel)
        login_response = auth_stub.LoginCheck(
            authentication_service_pb2.LoginRequest(
                user_name=args.username,
                password=args.password,
                client_id=clientid), _JET_TIMEOUT)

        if login_response.result == 1:
            print("Login successful")
        else:
            print("Login failed")
            sys.exit(1)

    except Exception as tx:
        print(tx)


#    # Create the BGP service stub
#    bgp = bgp_route_service_pb2.BgpRouteStub(channel)
#    strBgpReq = bgp_route_service_pb2.BgpRouteInitializeRequest()
#    result = bgp.BgpRouteInitialize(strBgpReq, timeout=_JET_TIMEOUT)
#    if ((result.status != bgp_route_service_pb2.BgpRouteInitializeReply.SUCCESS) and
#        (result.status != bgp_route_service_pb2.BgpRouteInitializeReply.SUCCESS_STATE_REBOUND)):
#        print("Error on Initialize")
#    print("Successfully connected to BGP Route Service")



    exit()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("localhost", 1883, 60)

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    client.loop_forever()


if __name__ == '__main__':
    main()

