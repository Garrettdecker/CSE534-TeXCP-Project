# Programmed by Garrett Decker for CSE534
# Garrett@decker5.com


# example way to call this script from command line:
# python3 traffic_generator.py 10000 10003


# sends traffic to the ingress router

import socket
import sys
import pickle
import time
import random

# must forward packets based on the topology

"""
arguments:
argv[1] - port to send traffic to
argv[2] - final destination port

"""


"""
packet structure:

path - path packet is on (format: port-port-port-port...)
pktType - probe packet or data packet?
content - this only contains user data (which we dont care about)
------ the below fields are used for probe packets ------
pathUtil - max utilization of any link on the path
posFeed - additive positive feedback
negFeed - multiplicative negative feedback
weight - used to prefer shorter paths

"""

# set some parameters (in seconds)

# this controls how often packets are sent
currentTimeBetweenPackets = 1

# timeBetweenFluctuations controls how often currentTimeBetweenPackets is randomized (between minTimeBetweenPackets and maxTimeBetweenPackets)
timeBetweenFluctuations = 30
minTimeBetweenPackets = 0.4
maxTimeBetweenPackets = 1


# set random seed so we get consistent results for debugging purposes
random.seed(0)


# get program arguments
sendToPort = int(sys.argv[1])
finalDestPort = int(sys.argv[2])    # this should be relevant in more complex topologies


# create a udp socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# to avoid address already in use error
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# bind the socket to the port
serverAddr = ('localhost', sendToPort)

try:
    # start traffic fluctuation timer
    fluctuationStart = time.time()

    # make counter that counts sent packets
    counter = 0

    while(True):

        # increment packet counter
        counter += 1

        # enforce time between sending packets
        # must use sleep so we are not busy waiting
        time.sleep(currentTimeBetweenPackets)

        # check how many seconds have elapsed since the last traffic fluctuation
        elapsed = time.time() - fluctuationStart
        if elapsed > timeBetweenFluctuations:
            # randomize currentTimeBetweenPackets
            currentTimeBetweenPackets = random.randrange(1000*minTimeBetweenPackets, 1000*maxTimeBetweenPackets, 1) / 1000
            # reset traffic fluctuation timer
            fluctuationStart = time.time()

        # create the traffic packet
        data = {'path':"0", 'pktType':"data", 'content':"blah"*20+str(counter), 'pathUtil':"", 'posFeed':"", 'negFeed':"", 'weight':""}
        path, pktType, content, pathUtil, posFeed, negFeed, weight = data['path'], data['pktType'], data['content'], data['pathUtil'], data['posFeed'], data['negFeed'], data['weight']
        print('packet fields:')
        print('path: {}, pktType: {}, content: {}, pathUtil: {}, posFeed: {}, negFeed: {}, weight: {}'.format(path, pktType, content, pathUtil, posFeed, negFeed, weight))
        #convert to binary
        pkt = pickle.dumps(data)


        # send packet
        print('sending {!r}'.format(pkt))
        sent = sock.sendto(pkt, serverAddr)


finally:
    print('closing socket')
    sock.close()
