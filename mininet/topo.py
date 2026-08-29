from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink

class FatTreeEdgeTopo(Topo):
    def build(self):
        # 1. Add Switches
        # STP is enabled on every bridge: the redundant s1-s2 backup link
        # creates a physical L2 loop, and STP keeps the tree loop-free so the
        # controller's broadcast/flood learning converges (Week 2 fix).
        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, stp=True) # Edge Switch 1
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch, stp=True) # Edge Switch 2
        s3 = self.addSwitch('s3', cls=OVSKernelSwitch, stp=True) # Core Switch

        # 2. Add Hosts (2 per Edge Switch)
        h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', ip='10.0.0.4/24', mac='00:00:00:00:00:04')

        # 3. Connect Hosts to Edge Switches (10 Mbps links)
        self.addLink(h1, s1, bw=10)
        self.addLink(h2, s1, bw=10)
        self.addLink(h3, s2, bw=10)
        self.addLink(h4, s2, bw=10)

        # 4. Connect Edge Switches to Core Switch (100 Mbps links)
        self.addLink(s1, s3, bw=100)
        self.addLink(s2, s3, bw=100)

        # 5. REDUNDANT BACKUP LINK (Edge-to-Edge path for Week 9 Fast-Failover)
        self.addLink(s1, s2, bw=100)

topos = { 'fattreeedge': ( lambda: FatTreeEdgeTopo() ) }

if __name__ == '__main__':
    setLogLevel('info')
    topo = FatTreeEdgeTopo()
    
    # PRODUCTION MODE: Connects to Member 1's OS-Ken controller.
    # Port 6633 matches scripts/run_controller.py, traffic/run_iperf3_experiment.py
    # and docs/week2/week3 (OS-Ken ofp_handler default OpenFlow listen port).
    net = Mininet(topo=topo, controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633), switch=OVSKernelSwitch, link=TCLink)

    net.start()
    print("*** Running CLI for verification")
    CLI(net)
    net.stop()
