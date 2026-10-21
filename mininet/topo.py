
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink
import argparse


class FatTreeEdgeTopo(Topo):

    def build(self):

        # 1. Add switches
        # Use a tree topology for stable initial connectivity.
        s1 = self.addSwitch(
            's1',
            cls=OVSKernelSwitch,
            protocols='OpenFlow13'
        )

        s2 = self.addSwitch(
            's2',
            cls=OVSKernelSwitch,
            protocols='OpenFlow13'
        )

        s3 = self.addSwitch(
            's3',
            cls=OVSKernelSwitch,
            protocols='OpenFlow13'
        )

        # 2. Add hosts
        h1 = self.addHost(
            'h1',
            ip='10.0.0.1/24',
            mac='00:00:00:00:00:01'
        )

        h2 = self.addHost(
            'h2',
            ip='10.0.0.2/24',
            mac='00:00:00:00:00:02'
        )

        h3 = self.addHost(
            'h3',
            ip='10.0.0.3/24',
            mac='00:00:00:00:00:03'
        )

        h4 = self.addHost(
            'h4',
            ip='10.0.0.4/24',
            mac='00:00:00:00:00:04'
        )

        # 3. Host-to-switch links (10 Mbps)
        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h2, s1, cls=TCLink, bw=10)
        self.addLink(h3, s2, cls=TCLink, bw=10)
        self.addLink(h4, s2, cls=TCLink, bw=10)

        # 4. Switch-to-switch links (100 Mbps)
        self.addLink(s1, s3, cls=TCLink, bw=100)
        self.addLink(s2, s3, cls=TCLink, bw=100)

        # The redundant s1-s2 link is temporarily removed
        # to avoid a Layer-2 loop during connectivity testing.


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--controller-ip',
        default='127.0.0.1',
        help='IP address of the remote OS-Ken controller'
    )

    parser.add_argument(
        '--controller-port',
        type=int,
        required=True,
        help='OpenFlow controller port'
    )

    args = parser.parse_args()

    setLogLevel('info')

    topo = FatTreeEdgeTopo()

    net = Mininet(
        topo=topo,
        controller=None,
        switch=OVSKernelSwitch,
        link=TCLink,
        autoSetMacs=False
    )

    controller = RemoteController(
        'c0',
        ip=args.controller_ip,
        port=args.controller_port
    )

    net.addController(controller)

    try:
        net.start()
        print("*** Running CLI for verification")
        CLI(net)
    finally:
        net.stop()
