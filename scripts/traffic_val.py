import time
import os
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.log import setLogLevel, info

def run_traffic_validation():
    setLogLevel('info')

    # Connect to local controller on port 6653
    net = Mininet(controller=RemoteController, switch=OVSKernelSwitch)

    info('*** Adding controller\n')
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)

    info('*** Adding hosts\n')
    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')
    h3 = net.addHost('h3', ip='10.0.0.3/24')

    info('*** Adding switch\n')
    s1 = net.addSwitch('s1', protocols='OpenFlow13')

    info('*** Creating links\n')
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s1)

    info('*** Starting network\n')
    net.build()
    c0.start()
    s1.start([c0])

    info('*** Verifying initial connectivity\n')
    net.pingAll()

    # Create logs output directory
    os.makedirs('logs', exist_ok=True)

    info('*** Running TCP Bulk traffic test (h1 -> h2)\n')
    h2.cmd('iperf3 -s -p 5201 > logs/iperf_tcp_server.log 2>&1 &')
    time.sleep(1)
    h1.cmd('iperf3 -c 10.0.0.2 -p 5201 -b 8M -t 10 > logs/iperf_tcp_client.log 2>&1')

    info('*** Running UDP Video traffic test (h1 -> h3)\n')
    h3.cmd('iperf3 -s -p 5202 > logs/iperf_udp_server.log 2>&1 &')
    time.sleep(1)
    h1.cmd('iperf3 -c 10.0.0.3 -p 5202 -u -b 5M -t 10 > logs/iperf_udp_client.log 2>&1')

    info('*** Traffic validation complete. Cleaning up...\n')
    h2.cmd('pkill iperf3')
    h3.cmd('pkill iperf3')
    net.stop()

if __name__ == '__main__':
    run_traffic_validation()
