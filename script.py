#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.node import Controller
import time
import math
import re
import sys

class DoubleSwitchTopo(Topo) :
    "2 switches each connected to n hosts."
    def build(self, n=2):
        s1 = self.addSwitch('S1')
        s2 = self.addSwitch('S2')
        self.addLink(s1, s2, bw=10, delay='5ms', max_queue_size=10, loss=0, use_htb=True)
        createHost(s1, self, 'VH2')
        createHost(s1, self, 'VH4')
        createHost(s2, self, 'VH1')
        createHost(s2, self, 'VH3')
        
def runIperf(net, iteration) :
    print('----- Starting Iperf tests -----')
    vh1 = net.get('VH1')
    vh2 = net.get('VH2')
    vh3 = net.get('VH3')
    vh4 = net.get('VH4')
    tcpPacketLength = 1448
    if iteration == 1:
        udp_throughput = 1
    else:
        udp_throughput = calculateUDPthroughput(tcpPacketLength)/1000000
    logUDPThroughput(iteration, udp_throughput)
    #vh2_command = 'iperf -u -c {} -b {}M -l {} -i 1 > udp_client.txt &'.format(vh1.IP(), udp_throughput, tcpPacketLength)
    vh2_command = 'iperf -u -c {} -b 2.31M -l {} -t 300 -i 1 > udp_client.txt &'.format(vh1.IP(), tcpPacketLength)
    print(vh2_command)
    vh1.cmd('iperf -u -s -t 300 -i 1 > udp_server.txt &')
    vh3.cmd('iperf -s -w 1M -Z cubic -t 300 -i 1 > tcp_server.txt &')
    print('Starting servers')
    time.sleep(2)
    print('tcpdump')
    vh2.cmd('sudo tcpdump -c 30 udp > tcpdump_udp.txt &')
    vh3.cmd('sudo tcpdump -c 30 tcp > tcpdump.txt &')
    #get RTT to estimate one-way delay (divide by 2)
    vh2.cmd('ping {} > RTT_udp.txt &'.format(vh1.IP()))
    vh4.cmd('ping {} > RTT_tcp.txt &'.format(vh3.IP()))
    print('Starting clients')
    #1448 is the packet size of tcp packets on my machine (observed with tcpdump)
    vh2.cmd(vh2_command) #Update UDP throughput considering previous loss values
    vh4.cmd('iperf -c {} -w 1M -Z cubic -t 300 -i 1 > tcp_client.txt &'.format(vh3.IP()))
    time.sleep(300)
    print ('------ Ending Iperf tests -----')

def createHost(switch, topo, hostID) :
    host = topo.addHost('%s' % (hostID))
    #1Gbps, 1ms delay
    topo.addLink(host, switch, bw=1000, delay ='1ms')

def simpleTest(iteration) :
    "Create and test a simple network"
    topo = DoubleSwitchTopo()
    net = Mininet(topo, controller=Controller, link=TCLink)
    net.start()
    print("Dumping host connections")
    dumpNodeConnections(net.hosts)
    print("Testing networkd connectivity")
    net.pingAll()
    runIperf(net, iteration)
    #CLI(net)
    net.stop()

def calculateUDPthroughput(tcpPacketLength):
    b = 2
    rtt = 14/1000
    p = readPreviousLossRate()
    t0 = 500/1000
    if p==0: #if loss rate = 0
        packetsPerSecond = 10000 #High value to represent infinity 
    else :
        packetsPerSecond = 1/(rtt*math.sqrt(2*b*p/3)+t0*min(1,3*math.sqrt(3*b*p/8)*p*(1+32*(p*p))))
    rounded_value = round(packetsPerSecond * tcpPacketLength*8, 2)
    print("ROUNDED VALUE")
    print(rounded_value)
    return rounded_value

def logUDPThroughput(iteration, udp_throughput):
    log_file= "udp_throughput_log.txt"
    if iteration == 1 :
        with open(log_file, "w") as file:
            file.write('iteration udp_throughput\n')
            file.write('{} {}\n'.format(iteration, udp_throughput))
    else :
        with open(log_file, "a") as file:
            file.write('{} {}\n'.format(iteration, udp_throughput))
    file.close()

def readPreviousLossRate():
    with open("udp_server.txt", "r") as file:
        lines = file.readlines()
        last_line = lines[-1]

    if re.search(r'\(-nan%\)', last_line) :
        print("0% loss rate")
        return 0
    if re.search(r'\(1e\+02%\)', last_line):
        print("100% loss rate")
        return 1
    match = re.search(r"\(([\d.]+)%\)", last_line)   
    if match :
        loss_percentage = float(match.group(1))
        loss_rate = loss_percentage/100
        print(f"Packet Loss Rate: {loss_rate:.4f}")
        file.close()
        return loss_rate
    else :
        print("Packet loss value not found!")
        sys.exit()
        file.close()
        return 0

if __name__ == '__main__' :
    #Tell mininet to print useful information
    setLogLevel('info')
    for iteration in range(1):
        simpleTest(iteration)

