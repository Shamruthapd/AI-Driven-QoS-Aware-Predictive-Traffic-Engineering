import time
import os
import random
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.log import setLogLevel, info

def run_large_dataset_generation():
    setLogLevel('info')
    
    info('\n*** Starting High-Volume Telemetry Collector ***\n')
    net = Mininet(controller=RemoteController, switch=OVSKernelSwitch)
    
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')
    h3 = net.addHost('h3', ip='10.0.0.3/24')
    s1 = net.addSwitch('s1', protocols='OpenFlow13')

    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s1)

    net.build()
    c0.start()
    s1.start([c0])
    
    info('*** Network Ready. Initiating 15 Dynamic Traffic Waves...\n')
    
    h2.cmd('iperf3 -s -p 5201 > /dev/null 2>&1 &')
    h3.cmd('iperf3 -s -p 5202 > /dev/null 2>&1 &')
    time.sleep(2)

    rates = ['2M', '5M', '8M', '12M', '15M', '20M']
    
    for cycle in range(1, 16):
        tcp_rate = random.choice(rates)
        udp_rate = random.choice(rates)
        duration = random.randint(8, 12)

        info(f'Wave {cycle}/15 -> TCP: {tcp_rate}, UDP: {udp_rate}, Duration: {duration}s\n')

        h1.cmd(f'iperf3 -c 10.0.0.2 -p 5201 -b {tcp_rate} -t {duration} > /dev/null 2>&1 &')
        h1.cmd(f'iperf3 -c 10.0.0.3 -p 5202 -u -b {udp_rate} -t {duration} > /dev/null 2>&1 &')

        time.sleep(duration + 2)

    info('*** Collection complete. Cleaning up...\n')
    h2.cmd('pkill iperf3')
    h3.cmd('pkill iperf3')
    net.stop()

if __name__ == '__main__':
    run_large_dataset_generation()
