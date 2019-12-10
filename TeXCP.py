# Programmed by Garrett Decker for CSE534
# Garrett@decker5.com


# note: this script is currently broken.  See video/report for details

import socket
import sys
import pickle
import time
import random


# note: parts of this program can handle generalized topologies, and parts of it assume that paths have at most 2 branches

"""
arguments:
argv[1] - port associated with this process
argv[2] - possible paths (ingress format: port-port-port-port,port-port-port-port,...)  (for core/egress, this command line argument should just put "0")
argv[3] - output links (format: port,port)

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
weight - to prefer shorter paths

"""

# get program arguments
ownPort = int(sys.argv[1])
possiblePaths = sys.argv[2].split(,)
outputLinks = sys.argv[3].split(,)


# set some parameters

# set random seed so we get consistent results for debugging purposes
random.seed(0)

# controls how often the decision timer fires (in seconds)
decisionTimerInterval = 8
# controls the max and min decision timer interval in the random version
maxDecisionTimerInterval = 10
minDecisionTimerInterval = 5
randDecisionTimerInterval = random.randint(minDecisionTimerInterval, maxDecisionTimerInterval)  # this must be rerandomized every time the decision timer fires

# controls how often the probe timer fires (in seconds)
probeTimerInterval = 2


# create a udp socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# to avoid address already in use error
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# bind the socket to the port
serverAddr = ('localhost', ownPort)
print('starting up TeXCP Agent on {} port {}'.format(*serverAddr))
sock.bind(serverAddr)

# initialize some variables
drainingRate1 = 0   #rsp in paper, this should be incremented for each packet that the ingress router sends down first path*
drainingRate2 = 0   #rsp in paper, this should be incremented for each packet that the ingress router sends down second path*
# link utilization is the average amount of traffic sent down the link since the last probe timer firing or last probe packet passing by
packetsSinceLastProbe1 = 0  # used to compute the new linkUtil1 when the probe timer fires or a probe packet passes by*
packetsSinceLastProbe2 = 0  # used to compute the new linkUtil2 when the probe timer fires or a probe packet passes by*
# Due to the fact that the max link bandwidths all far exceed the bandwidth that is actually needed for this simulation, and that the differences in data
# packet sizes are negligible, link and network utilizations will be measured by number of packets per unit time instead of by percentage of bandwidth.
linkUtil1 = 0   #Ul in paper, for use in both ingress and core routers
linkUtil2 = 0   #Ul in paper, for use in both ingress and core routers
observedPathUtil1 = 0   #Usp in paper, only for use at ingress routers
observedPathUtil2 = 0   #Usp in paper, only for use at ingress routers
pathWeight1 = 0.5   #Xsp in paper, start with half and half
pathWeight2 = 0.5   #Xsp in paper, start with half and half


try:

    # start decision timer
    decisionTimerStart = time.time()

    # start probe timer
    probeTimerStart = time.time()

    while True:

        # since we will have multiple instances of TeXCP running this loop, it may be expensive to have them all busy waiting for incoming packets.  This could exasperate stability problems.
        # if this causes issues, we will have to find a work around (maybe sleep for very short intervals when there are no packets to be handled? but sleep() is inconsistent for very short time scales...)
        # nevermind... I forgot recvfrom() can be blocking, so we do not busy wait

        pkt, address = sock.recvfrom(8192)
        print('received {} bytes from {}'.format(len(pkt), address))

        """
        # a note on the nondeterminism of this program:
        # even with a fixed seed for the random number generator, this program still exhibits nondeterministic behavior due to
        # the variable execution time of the different processes.  A slight variance in execution time can lead to packets being sent
        # in different orders.  Because the behavior of each process is dependent on what order they receive packets from the other 
        # processes, overall execution of the algorithm can drastically diverge from previous runs once a single packet is reordered.
        # Once one packet is reordered, the randomized decision timer may be reset to a different random value than in previous runs,
        # which I suspect has the most impact on the behavior divergence.
        """

        # print the current values of the observed path utilizations (these come directly from the max path utilization field of the probe packets that return to the ingress routers)
        # the code here is executed every time the current node receives a packet (so even more frequently than the rate of probe timer fires)
        # we should only collect data from the terminals that are running the ingress router processes, as those have the meaningful values for observedPathUtil1 and observedPathUtil2
        print('IMPORTANT NETWORK UTILIZATION DATA:')
        print('observedPathUtil1: {}, observedPathUtil2: {}'.format(observedPathUtil1, observedPathUtil2))


        # regardless of what type of packet we just received, since we are now unblocked, let us take this opportunity to check whether the decision timer should fire yet
        # check how many seconds have elapsed since the last decision timer firing
        elapsed = time.time() - probeTimerStart

       
        """
        # UNCOMMENT and swap with the below code in order to use the randomized decision timer version
        if elapsed > randDecisionTimerInterval:
            # decision timer is firing
            # rerandomize the next decision timer and reset decision timer
            randDecisionTimerInterval = random.randint(minDecisionTimerInterval, maxDecisionTimerInterval)
            decisionTimerStart = time.time()

            # continue as in the non-randomized version below

        """
        if elapsed > decisionTimerInterval:
            # decision timer is firing
            decisionTimerStart = time.time()
            
            # recompute path weights (Xsp) based on observed path utilizations (Usp)
            # these equations are still not topology agnostic (example: allow for more than 2 paths from ingress to egress),
            # but at this point, we just need this to be runnable
            # see equations in TeXCP paper

            # eq 6
            # compute average utilization normalized by the drain rates
            avgUtilNormedByDrainRates = (drainingRate1 * observedPathUtil1 + drainingRate2 * observedPathUtil2) / (drainingRate1 + drainingRate2)

            # eq 5
            # have overutilized paths to decrease rate and underutilized paths to increase rate
            # also force change in path's traffic proportional to its current traffic share
            if observedPathUtil1 > observedPathUtil2:            
                deltaPathWeight1 = (drainingRate1 / (drainingRate1 + drainingRate2) * (avgUtilNormedByDrainRates - observedPathUtil1)
                deltaPathWeight2 = (drainingRate2 / (drainingRate1 + drainingRate2) * (avgUtilNormedByDrainRates - observedPathUtil2) + 0.001
            else:
                deltaPathWeight1 = (drainingRate1 / (drainingRate1 + drainingRate2) * (avgUtilNormedByDrainRates - observedPathUtil1) + 0.001
                deltaPathWeight2 = (drainingRate2 / (drainingRate1 + drainingRate2) * (avgUtilNormedByDrainRates - observedPathUtil2)

            # eq 7
            # ensure traffic fractions are positive
            pathWeight1 = max(0, pathWeight1 + deltaPathWeight1)
            pathWeight2 = max(0, pathWeight2 + deltaPathWeight2)
            
            # eq 8
            # ensure traffic fractions sum to 1
            pathWeight1 = pathWeight1 / (pathWeight1 + pathWeight2)
            pathWeight2 = pathWeight2 / (pathWeight1 + pathWeight2)
             


        # if pkt exists
        if pkt:
            # get the fields of the packet
            data = pickle.loads(pkt)
            path, pktType, content, pathUtil, posFeed, negFeed, weight = data['path'], data['pktType'], data['content'], data['pathUtil'], data['posFeed'], data['negFeed'], data['weight']
            print('packet fields:')
            print('path: {}, pktType: {}, content: {}, pathUtil: {}, posFeed: {}, negFeed: {}, weight: {}'.format(path, pktType, content, pathUtil, posFeed, negFeed, weight))


            # now we will handle the packet
            
            # check whether the packet is a probe or data packet
            if pktType == 'data':
                # if data packet, then just forward packet to another router
                
                if path == '0':
                    # if the path in the packet is '0', this means the packet came from the traffic generator
                    # in such a case, we must be at an ingress router, so a path should be chosen to forward this packet along
                    
                    # probabilistically choose which path to send the packet on based on the computed path weights
                    randNum = random.randint(0, 10000, 1) / 10000


                    # However, there may be some stability issues due to the following:
                    # Basically, if we choose which path to send the packet on using a binomial distribution,
                    # then we might get very unlucky balancing.  For example, 0.5 probability for each path could send
                    # significantly more packets on one of the paths.  Granted, the probability of this happening becomes
                    # negligible as the number of packets sent grows.  Since the rate of packets being sent in this simulation
                    # is relatively low (compared to an actual ISP), the probability of this bad luck happening is not negligible.
                    # Upon realizing this issue, I concocted the following algorithm to attempt to solve it:
                    # Suppose the path weight ratio was 0.6 to 0.4:
                    # 4+4-6+4-6+4+4-6+4-6   <---repeatedly add on the lower of the ratios in a running total until it exceeds
                    #                           the higher ratio, then subtract the higher ratio.
                    # 4 8 2 6 0 4 8 2 6 0   <---the running total is shown here
                    # 1 1 2 1 2 1 1 2 1 2   <---if the previous operation was addition, send along the first path
                    #                           if the previous operation was subtraction, send along the second path
                    # as you can see, this results in 60% 1's and 40% 2's in a repeating cycle of length 5.
                    # I thought this was a bit clever until I realized it unfortunately has an issue of being biased towards
                    # the higher ratio (suppose we stop after the fourth packet, which would yield a 0.75 to 0.25 ratio in favor of the first path).
                    # Due to both methods having flaws, I will stick with what is currently implemented.
                    
                    if randNum < pathWeight1:
                        # send on first path
                        # but first we must modify the packet to send
                        data.update({'path':possiblePaths[0]})
                        newpkt = pickle.dumps(data)

                        # determine which router to forward packet to
                        portList = possiblePaths[0].split('-')
                        nextPort = int(portList[1])
                        nextAddr = ('localhost', nextPort)
                        
                        # forward packet to next router
                        sent = sock.sendto(newpkt, nextAddr)
                        print('sent {} bytes to {}'.format(sent, nextAddr))

                        # we are sending on the first link, so increment packetsSinceLastProbe1
                        packetsSinceLastProbe1 += 1

                    else:
                        # send on second path
                        # but first we must modify the packet to send
                        data.update({'path':possiblePaths[1]})
                        newpkt = pickle.dumps(data)

                        # determine which router to forward packet to
                        portList = possiblePaths[1].split('-')
                        nextPort = int(portList[1])
                        nextAddr = ('localhost', nextPort)
                        
                        # forward packet to next router
                        sent = sock.sendto(newpkt, nextAddr)
                        print('sent {} bytes to {}'.format(sent, nextAddr))

                        # we are sending on the second link, so increment packetsSinceLastProbe2
                        packetsSinceLastProbe2 += 1


                    # check how many seconds have elapsed since the last probe timer firing
                    elapsed = time.time() - probeTimerStart
                    if elapsed > probeTimerInterval:
                        # NOTE: WE ARE AT AN INGRESS ROUTER
                        # fire the probe timer
                        
                        # linkUtils need to be computed (how many packets have been sent since last probe timer firing)

                        # send probe packets along all possible paths

                        # send a probe packet along first possible path
                        # construct the first probe packet (since we are at ingress router)
                        
                        data1 = {'path':possiblePaths[0], 'pktType':"probe", 'content':"", 'pathUtil':observedPathUtil1, 'posFeed':0, 'negFeed':1, 'weight':""}
                        # a consequence of having a link capacity >> traffic demand is that the aggregate feedback becomes largely irrelevant because the 
                        # bounds are laughably wide and thus are never reached.
                        # this allows for implementation simplifications.
                        # weight is blank since all path lengths are equal, so there is no shorter path.

                        # convert to binary
                        pkt = pickle.dumps(data1)

                        #path, pktType, content, pathUtil, posFeed, negFeed, weight = data['path'], data['pktType'], data['content'], data['pathUtil'], data['posFeed'], data['negFeed'], data['weight']
                        #print('packet fields:')
                        #print('path: {}, pktType: {}, content: {}, pathUtil: {}, posFeed: {}, negFeed: {}, weight: {}'.format(path, pktType, content, pathUtil, posFeed, negFeed, weight))

                        # determine which router to forward packet to
                        portList = possiblePaths[0].split('-')
                        nextPort = int(portList[1])
                        nextAddr = ('localhost', nextPort)
                        
                        # forward packet to next router
                        sent = sock.sendto(pkt, nextAddr)
                        print('sent probe packet containing {} bytes to {}'.format(sent, nextAddr))


                        # send a probe packet along second possible path
                        # construct the second probe packet (since we are at ingress router)
                        
                        data2 = {'path':possiblePaths[1], 'pktType':"probe", 'content':"", 'pathUtil':observedPathUtil2, 'posFeed':0, 'negFeed':1, 'weight':""}
                        # a consequence of having a link capacity >> traffic demand is that the aggregate feedback becomes largely irrelevant because the 
                        # bounds are extremely wide and thus are never reached.
                        # this allows for implementation simplifications.
                        # weight is unused since all path lengths are equal, so there is no shorter path.

                        # convert to binary
                        pkt = pickle.dumps(data2)

                        #path, pktType, content, pathUtil, posFeed, negFeed, weight = data['path'], data['pktType'], data['content'], data['pathUtil'], data['posFeed'], data['negFeed'], data['weight']
                        #print('packet fields:')
                        #print('path: {}, pktType: {}, content: {}, pathUtil: {}, posFeed: {}, negFeed: {}, weight: {}'.format(path, pktType, content, pathUtil, posFeed, negFeed, weight))

                        # determine which router to forward packet to
                        portList = possiblePaths[1].split('-')
                        nextPort = int(portList[1])
                        nextAddr = ('localhost', nextPort)
                        
                        # forward packet to next router
                        sent = sock.sendto(pkt, nextAddr)
                        print('sent probe packet containing {} bytes to {}'.format(sent, nextAddr))

                        # reset probe timer
                        probeTimerStart = time.time()
                        # also update link utilizations based on packets sent since last probe timer
                        linkUtil1 = packetsSinceLastProbe1
                        linkUtil2 = packetsSinceLastProbe2
                        # also reset packet count since last probe timer
                        packetsSinceLastProbe1 = 0
                        packetsSinceLastProbe2 = 0
                        
                    

                else:
                    # packet path field is set normally
                    # NOTE: WE ARE NOT AT AN INGRESS ROUTER
                    # we must forward data packet to next router
                    
                    # determine which router to forward packet to
                    
                    # parse the packet path field
                    portList = path.split('-')
                    # get the path length
                    pathLength = len(portList)
                    # find which router we are currently at on the path
                    currentIndex = portList.index(str(ownPort))
                    
                    
                    if currentIndex + 1 < pathLength:
                        # if we have not yet reached the final destination
                        # get next router (port) on path
                        nextPort = int(portList[currentIndex + 1])
                        nextAddr = ('localhost', nextPort)

                        # forward packet to next router in portList
                        sent = sock.sendto(pkt, nextAddr)
                        print('sent {} bytes to {}'.format(sent, nextAddr))

                        # determine which link we just sent to, so we know which packetsSinceLastProbe to increment

                        # check whether there is only one outputLink
                        if len(outputLinks) == 1:
                            # we sent on the first (and only) link, so increment packetsSinceLastProbe1
                            packetsSinceLastProbe1 += 1
                        
                        else:
                            # we have two available output links, so determine which one we sent on
                            if nextPort == int(outputLinks[0]):
                                # we sent on the first link
                                # increment packetsSinceLastProbe1
                                packetsSinceLastProbe1 += 1
                            elif nextPort == int(outputLinks[1]):
                                # we sent on the second link
                                # increment packetsSinceLastProbe2
                                packetsSinceLastProbe2 += 1


                    else:
                        # otherwise, we are at the final destination, so we do not need to forward this packet anymore
                        print('data packet reached final destination.  Dropping it.')


            elif pktType == 'probe':
                # now we must handle a probe packet

                # Aside: a consequence of having a link capacity >> traffic demand (which is certainly true on our hardware setup) is that the aggregate feedback becomes 
                # largely irrelevant because the upper bounds on delta Xsp (how much the path weights change) are extremely wide and thus are never reached.
                # this allows for implementation simplifications.
                
                # check whether we are an ingress or core/egress router (our behavior will be drastically different)
                # core/egress routers always have possiblePaths[0] argument set as "0", whereas ingress routers never have this set as "0"
                if possiblePaths[0] == "0":
                    # this is a core/egress router

                    # update pathUtil in pkt if necessary
                    data.update({'pathUtil':max(packetsSinceLastProbe, pathUtil)})
                    newpkt = pickle.dumps(data)

                    # NOTE: THE BELOW SECTION NEEDS FIXING

                    # parse the packet path field
                    portList = path.split('-')
                    # get the path length
                    pathLength = len(portList)
                    # find which router we are currently at on the path
                    currentIndex = portList.index(str(ownPort))

                    # check if arrived at final destination (egress router)
                    if currentIndex + 1 > pathLength:

                        # probe is at a core router

                        # update pathUtil if necessary
                        data.update({'pathUtil':max(packetsSinceLastProbe, pathUtil)})
                        newpkt = pickle.dumps(data)


                        # forward probe packet to the next router on its path

                    else:
                        # probe arrived at egress router

                        # unicast back to ingress router

                    # FIX UNTIL HERE

                else:
                    # this is an ingress router
                    
                    # check which path this probe packet traversed (it should still be stored in path, so we can compare with our output links)
                    if path[1] == outputLink[0]:
                        # this probe traversed the first possible path
                        # so update observedPathUtil1
                        observedPathUtil1 = pathUtil

                    elif path[1] == outputLink[1]:
                        # this probe traversed the second possible path
                        # so update observedPathUtil2
                        observedPathUtil2 = pathUtil

                    else:
                        print('error: this should be impossible to reach.  Check this.')
                        break

                
            else:
                # if pktType is neither 'data' nor 'probe', then something is very wrong
                print('error: pktType was neither "data" nor "probe"... terminating while loop.)
                break
        else:
            # apparently, pkt does not exist
            print('warning: pkt does not exist.  Please investigate what caused this.  Terminating.')
            break
       

finally:
    print('closing socket')
    sock.close()
