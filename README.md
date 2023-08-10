# Using kea hooks and JET to send routed to cRPD


In this Proof of Concept (POC), we utilize the Kea DHCP server hooks feature to send assigned addresses to Juniper cRPD (container Routing Protocol Daemon) using the Juniper JETS (Juniper Extension Toolkit) API.


# Setup

- Start a bridge br2 with 10.10.10.1/24 subnet.


- Install MQTT broker
```
sudo apt update -y && sudo apt install mosquitto mosquitto-clients -y
```

- Install python MQTT client
```
sudo apt install python3-paho-mqtt
```

 - Config for our device
```
$ cat /etc/mosquitto/conf.d/bds_local.conf
allow_anonymous true
listener 1883 10.10.10.1
```
