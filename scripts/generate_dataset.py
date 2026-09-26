import time
import os
import random
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.log import setLogLevel, info

def run_dataset_generation(runs=5):
    setLogLevel('info')
    os.makedirs('logs', exist_ok=True)

    for i in range(1, runs + 1):
        info(f'\n--- Starting Traffic Generation Run {i}/{runs} ---\n')
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
        time.sleep(2)

        # Vary bitrates dynamically per run
        tcp_bw = random.choice(['5M', '8M', '12M', '15M'])
        udp_bw = random.choice(['3M', '5M', '8M', '10M'])
        duration = random.choice([15, 20, 25])

        info(f'Run {i}: TCP Target={tcp_bw}, UDP Target={udp_bw}, Duration={duration}s\n')

        h2.cmd(f'iperf3 -s -p 5201 > /dev/null 2>&1 &')
        h3.cmd(f'iperf3 -s -p 5202 > /dev/null 2>&1 &')
        time.sleep(1)

        # Launch concurrent TCP and UDP streams
        h1.cmd(f'iperf3 -c 10.0.0.2 -p 5201 -b {tcp_bw} -t {duration} > /dev/null 2>&1 &')
        h1.cmd(f'iperf3 -c 10.0.0.3 -p 5202 -u -b {udp_bw} -t {duration} > /dev/null 2>&1 &')

        time.sleep(duration + 3)

        h2.cmd('pkill iperf3')
        h3.cmd('pkill iperf3')
        net.stop()
        time.sleep(2)

if __name__ == '__main__':
    run_dataset_generation(runs=5)
