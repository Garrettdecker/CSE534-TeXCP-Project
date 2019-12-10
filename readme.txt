
FULL DISCLOSURE:

This implementation is currently broken.  I made major changes to it in the final week of the project, involving changing many important design decisions (I have no doubt that the majority of the lines of code have been altered in the last week).  The inherent nondetermistic and distributed nature of this program also was a time sink.  By the final couple days, I realized I had bit off more than I could chew by trying to change too much too fast.  Honestly, it probably would have been easier to redesign the structure of the program than to continue to try to hack the existing version back together.



I still need to do a demo though, so I figure I will make the best of a bad situation.  This is how it is *supposed* to work:




The TeXCP agents are passed information about the topology of the network via arguments on the command line.

Instructions to use project:

1. Open N+M terminals, where N is the number of nodes in the topology and M is the number of ingress nodes.

2. Make sure all terminals are in the directory where the project scripts are stored.

3. The arguments required to start the TeXCP.py and traffic_generator.py scripts are given at the top of their respective source files.

3. I will give an example command to start one of each type of nodes (ingress, core, egress) from the topology depicted in the final report:

seattle ingress node (first argument: seattle node's port, second argument: list of available paths, where hops in a single path are delimited by "-", and separate paths are delimited by ",", third argument: seattle's output links (ports of neighboring nodes) along the previously given paths):
$ python3 TeXCP.py 10000 10000-10001-10002-10003,10000-10004-10005-10003 10001,10004
core node B (10005) (first argument: core node B's port, second argument: core/egress nodes always put 0 here, third argument: core node B's output links (ports of neighboring nodes further along the path):
$ python3 TeXCP.py 10005 0 10003,10009
New York egress node (first argument: New York node's port, second argument: core/egress nodes always put 0 here, third argument: 0 (unused))
$ python3 TeXCP.py 10009 0 0

Note that the second argument for core and egress nodes should always be 0.

N terminals should be running the TeXCP.py script with command line arguments tailored to the desired topology.


4. Additionally, the ingress nodes need to be provided traffic before they can make any routing decisions.  The traffic_generator.py script generates UDP packets to act as traffic for the ingress nodes (and it even fluctuates over larger time scales).  Here is an example of starting a process that generates traffic for the seattle ingress node:

(first argument: port to send traffic to, second argument: final destination port)
$ python3 traffic_generator.py 10000 10003

M terminals should be running the traffic_generator.py script.


5. For the topology given in the report, there should be 10 terminals running the TeXCP.py script and 2 terminals running the traffic_generator.py script.

6. For data collection purposes, the terminals running the ingress nodes are important to look at because they print out the max utilizations of the different paths at a high frequency.

7. In order to use the TeXCP version with randomized decision timers, ctrl-F "UNCOMMENT" to locate the code block that should be uncommented and swapped with the adjacent one.  I decided to combine the two versions in a single script whose behavior could easily be changed because the idea was suggested in a comment after I gave my presentation.  There was little reason not to, and there was also the benefit of not having the two versions differ more than they needed to (that would be harder to maintain).
