#!/usr/bin/python3

"""
POC using DHCP hooks to send messages over MQTT.

MQTT Guides:
   http://www.steves-internet-guide.com/mqtt-python-beginners-course/
   https://mosquitto.org/
   https://www.hivemq.com/mqtt-essentials/

"""

#import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import argparse
import logging
import sys
import os
import json
from pprint import pprint


def process_command ():
    data = dict()

    if args.hook_command == "leases4_committed":
        print ("received leases4_committed")
        address = os.environ.get('LEASES4_AT0_ADDRESS')
        print ("address =", address)

        data["LEASES4_AT0_ADDRESS"] = address
        data["next_hop"] = "1.1.1.1"

        print ("publish to MQTT")
        #publish.single("paho/test/single", "payload", hostname="mqtt.eclipseprojects.io")
        publish.single(args.mq, json.dumps(data), hostname="localhost")




if __name__ == "__main__":

    parser = argparse.ArgumentParser(
                    description='Kea DHCP server hook script ',
                    epilog='Just a POC')

    parser.add_argument('hook_command', help='the dhcp server hook command')     
    parser.add_argument('-mq', default='dhcp_server', help='the MQTT queue to send to')     
    parser.add_argument('-d', '--debug', action='store_true')

    args = parser.parse_args()
    if (args.debug):
        print("Debug on",args.debug)
        pprint(sys.argv)
        pprint(os.environ)

    print("hook command:",args.hook_command)
    print("sending to queue:",args.mq)

    process_command()
