from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink
import argparse


class FatTreeEdgeTopo(Topo):

    def build(self):

        # ---------------------------------------------------------------
        # 1. Add switches
        # STP prevents Layer-2 loops caused by the redundant s1-s2 link.
        # ---------------------------------------------------------------
        s1 = self.addSwitch(
            's1',
            cls=OVSKernelSwitch,
            stp=True
        )

        s2 = self.addSwitch(
            's2',
            cls=OVSKernelSwitch,
            stp=True
        )

        s3 = self.addSwitch(
            's3',
            cls=OVSKernelSwitch,
            stp=True
        )

        # ---------------------------------------------------------------
        # 2. Add hosts
        # ---------------------------------------------------------------
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

        # ---------------------------------------------------------------
        # 3. Host-to-switch links
        # 10 Mbps edge links
        # ---------------------------------------------------------------
        self.addLink(h1, s1, bw=10)
        self.addLink(h2, s1, bw=10)
        self.addLink(h3, s2, bw=10)
        self.addLink(h4, s2, bw=10)

        # ---------------------------------------------------------------
        # 4. Switch-to-switch links
        # 100 Mbps backbone links
        # ---------------------------------------------------------------
        self.addLink(s1, s3, bw=100)
        self.addLink(s2, s3, bw=100)

        # ---------------------------------------------------------------
        # 5. Redundant backup link
        # Used for redundancy and future fast-failover experiments.
        # STP prevents a permanent L2 loop during normal operation.
        # ---------------------------------------------------------------
        self.addLink(s1, s2, bw=100)


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

    # ---------------------------------------------------------------
    # Create Mininet without a default controller.
    # The controller is added explicitly below.
    # ---------------------------------------------------------------
    net = Mininet(
        topo=topo,
        controller=None,
        switch=OVSKernelSwitch,
        link=TCLink
    )

    # ---------------------------------------------------------------
    # Connect to the remote OS-Ken controller.
    # ---------------------------------------------------------------
    controller = RemoteController(
        'c0',
        ip=args.controller_ip,
        port=args.controller_port
    )

    net.addController(controller)

    # ---------------------------------------------------------------
    # Start network
    # ---------------------------------------------------------------
    net.start()

    print("*** Running CLI for verification")

    CLI(net)

    net.stop()
