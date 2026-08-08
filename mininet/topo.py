from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

class EdgeNetworkTopo(Topo):
    def build(self):
        # Add 2 Edge Switches and 1 Core Switch
        s1 = self.addSwitch('s1', cls=OVSKernelSwitch) # Edge Switch 1
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch) # Edge Switch 2
        s3 = self.addSwitch('s3', cls=OVSKernelSwitch) # Core Switch

        # Add Host A and Host B
        h1 = self.addHost('h1', ip='10.0.0.1/24') # Host A (Video/Voice)
        h2 = self.addHost('h2', ip='10.0.0.2/24') # Host B (Bulk Data)

        # Add Links (defining bandwidths for QoS testing)
        self.addLink(h1, s1, bw=10)
        self.addLink(h2, s2, bw=10)
        self.addLink(s1, s3, bw=100)
        self.addLink(s2, s3, bw=100)

topos = { 'edgenetwork': ( lambda: EdgeNetworkTopo() ) }

if __name__ == '__main__':
    setLogLevel('info')
    topo = EdgeNetworkTopo()
    # Connected to RemoteController for Member 1's Ryu integration
    net = Mininet(topo=topo, controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6653), switch=OVSKernelSwitch)
    net.start()
    print("*** Running CLI for verification")
    CLI(net)
    net.stop()
