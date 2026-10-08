import time
import csv
import os
import subprocess
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.log import setLogLevel

def run_contention_bench(qos_status="OFF"):
    print(f"\n==========================================")
    print(f"   Starting Contention Test: QoS {qos_status}")
    print(f"==========================================")
    
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
    time.sleep(3)

    if qos_status == "ON":
        print("[+] Applying Data-Plane Queue Rules...")
        subprocess.run(["sudo", "./mininet/configure_queues.sh"], check=True)

    # Start iperf servers
    h2.cmd('iperf3 -s -p 5201 &')
    h3.cmd('iperf3 -s -p 5202 &')
    time.sleep(2)

    print("[+] Launching Contention Flows...")
    print("    - Flow 1 (Bulk TCP): 12 Mbps to h2 (Port 2)")
    print("    - Flow 2 (Priority UDP Video): 8 Mbps to h3 (Port 3)")

    # Run simultaneous flows for 15 seconds
    h2_cmd = f"iperf3 -c 10.0.0.2 -p 5201 -b 12M -t 15 --json > logs/h2_bulk_{qos_status.lower()}.json &"
    h3_cmd = f"iperf3 -c 10.0.0.3 -p 5202 -u -b 8M -t 15 --json > logs/h3_priority_{qos_status.lower()}.json &"

    h1.cmd(h2_cmd)
    h1.cmd(h3_cmd)

    time.sleep(18)

    h2.cmd('pkill iperf3')
    h3.cmd('pkill iperf3')
    net.stop()
    print(f"[+] Completed Test for QoS {qos_status}\n")

if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    setLogLevel('info')
    run_contention_bench(qos_status="OFF")
    time.sleep(3)
    run_contention_bench(qos_status="ON")
