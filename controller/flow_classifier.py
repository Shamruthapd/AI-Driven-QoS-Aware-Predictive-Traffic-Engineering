"""
Week 7 - QoS Flow Classification

Classifies project traffic into:
    PRIORITY
    BEST_EFFORT

Current project traffic:
    Scapy IoT:
        10.0.0.3 -> 10.0.0.4
        UDP destination port 5202

    iPerf3:
        10.0.0.1 -> 10.0.0.2
        TCP/UDP destination port 5201

The classifier also accepts DSCP information when available.
"""

from dataclasses import dataclass
from typing import Optional


PRIORITY = "PRIORITY"
BEST_EFFORT = "BEST_EFFORT"


# Project-specific traffic identifiers
IOT_SRC_IP = "10.0.0.3"
IOT_DST_IP = "10.0.0.4"
IOT_DST_PORT = 5202

IPERF_SRC_IP = "10.0.0.1"
IPERF_DST_IP = "10.0.0.2"
IPERF_DST_PORT = 5201


@dataclass
class FlowClassification:
    """
    Result returned by the classifier.
    """

    traffic_class: str
    reason: str
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    ip_proto: Optional[int] = None
    dst_port: Optional[int] = None
    dscp: Optional[int] = None


def classify_flow(
    src_ip=None,
    dst_ip=None,
    ip_proto=None,
    dst_port=None,
    dscp=None,
):
    """
    Classify an IP flow as PRIORITY or BEST_EFFORT.

    Priority:
        Scapy IoT traffic: 10.0.0.3 -> 10.0.0.4, UDP, port 5202

    Best-effort:
        iPerf3 traffic: 10.0.0.1 -> 10.0.0.2, TCP/UDP, port 5201

    DSCP:
        A non-zero DSCP value is recorded for classification context,
        but project traffic is classified using the actual IP/protocol/
        port definitions above because the current traffic generators
        do not explicitly set DSCP.
    """

    # Scapy IoT traffic
    if (
        src_ip == IOT_SRC_IP
        and dst_ip == IOT_DST_IP
        and ip_proto == 17
        and dst_port == IOT_DST_PORT
    ):
        return FlowClassification(
            traffic_class=PRIORITY,
            reason="Scapy IoT UDP flow",
            src_ip=src_ip,
            dst_ip=dst_ip,
            ip_proto=ip_proto,
            dst_port=dst_port,
            dscp=dscp,
        )

    # iPerf3 TCP/UDP traffic
    if (
        src_ip == IPERF_SRC_IP
        and dst_ip == IPERF_DST_IP
        and ip_proto in (6, 17)
        and dst_port == IPERF_DST_PORT
    ):
        return FlowClassification(
            traffic_class=BEST_EFFORT,
            reason="iPerf3 bulk traffic",
            src_ip=src_ip,
            dst_ip=dst_ip,
            ip_proto=ip_proto,
            dst_port=dst_port,
            dscp=dscp,
        )

    # Default policy
    return FlowClassification(
        traffic_class=BEST_EFFORT,
        reason="Default best-effort policy",
        src_ip=src_ip,
        dst_ip=dst_ip,
        ip_proto=ip_proto,
        dst_port=dst_port,
        dscp=dscp,
    )
