#!/usr/bin/python3

import argparse
import grpc
import paho.mqtt.client as mqtt
import json
from pprint import pprint


import bgp_route_service_pb2
import bgp_route_service_pb2_grpc
import prpd_common_pb2
import prpd_common_pb2_grpc
import jnx_addr_pb2
import jnx_addr_pb2_grpc
import authentication_service_pb2
import authentication_service_pb2_grpc


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

def RouteInit(bgp):
    print('############## INVOKING BgpRouteInitialize API #############')
    strBgpReq = bgp_route_service_pb2.BgpRouteInitializeRequest()
    result = bgp.BgpRouteInitialize(strBgpReq, timeout=TIMEOUT)
    print('BgpRouteInitialize API return = %d' % result.status)
    if ((result.status != bgp_route_service_pb2.BgpRouteInitializeReply.SUCCESS) and
        (result.status != bgp_route_service_pb2.BgpRouteInitializeReply.SUCCESS_STATE_REBOUND)):
        print('Error on Initialize')


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



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', help="Juniper BGP instance", type=str, default="localhost")
    parser.add_argument('--port', help="Server GRPC port", type=int, default=50051)
    parser.add_argument('--username', help="Username", type=str, default="user1")
    parser.add_argument('--password', help="Password", type=str, default="passwd1")
    parser.add_argument('--client_id', help="Client_id", default="100")
    args = parser.parse_args()
    

    # Connect and Authenticate via TCP from on or off-box
    conn = grpc.insecure_channel('%s:%d' % (args.device, int(args.port)))
    a = Auth(conn, args.username, args.password)
    login = a.grpc_login(args.client_id)

    # Create the BGP service stub
    bgp = bgp_route_service_pb2_grpc.BgpRouteStub(conn)

    # Init and begin adding routes
    RouteInit(bgp)



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

