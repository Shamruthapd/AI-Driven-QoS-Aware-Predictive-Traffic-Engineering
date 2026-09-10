# Week 3 — Traffic Generation and Baseline Experiments

## 1. Objective

Week 3 focuses on generating reproducible network traffic using iPerf3 over the Mininet/Open vSwitch topology established in Week 2.

The experiments provide real baseline measurements for the later QoS analysis and dataset-generation stages.

## 2. Traffic Generation Environment

- Mininet 2.3.0
- Open vSwitch 3.3.4
- OpenFlow 1.3
- OS-Ken 4.2.1
- iPerf3 3.16
- Python 3.12.3

Topology:

h1 ---- s1 ---- h2

The controller endpoint is:

127.0.0.1:6633
## 3. Repeatable Experiment Script

The traffic-generation module is:

traffic/run_iperf3_experiment.py

The script supports:

- TCP traffic
- UDP traffic
- configurable experiment duration
- configurable UDP bitrate
- automatic iPerf3 server startup
- automatic result logging
- automatic Mininet cleanup

Results are stored under:

results/week3/
## 4. TCP Baseline Experiment

Configuration:

Parameter	Value
Protocol	TCP
Duration	10 seconds
Destination	h2
iPerf3 port	5201

Measured result:

Metric	Result
Transfer	74.3 GBytes
Sender bitrate	63.8 Gbit/s
Receiver bitrate	63.8 Gbit/s
Retransmissions	5

Log:

results/week3/tcp_20260809_142223.log

Evidence:

screenshots/week3-tcp-iperf3.jpg
## 5. UDP Baseline Experiment

Configuration:

Parameter	Value
Protocol	UDP
Duration	10 seconds
Target bitrate	10 Mbit/s
Destination	h2
iPerf3 port	5201

Measured result:

Metric	Result
Transfer	11.9 MBytes
Sender bitrate	10.0 Mbit/s
Receiver bitrate	10.0 Mbit/s
Receiver jitter	0.009 ms
Packet loss	0%
Lost datagrams	0/8632

Log:

results/week3/udp_20260809_142310.log

Evidence:

screenshots/week3-udp-iperf3.jpg
## 6. Reproducibility

TCP experiment:

sudo "$(which python3)" traffic/run_iperf3_experiment.py \
  --protocol tcp \
  --duration 10

UDP experiment:

sudo "$(which python3)" traffic/run_iperf3_experiment.py \
  --protocol udp \
  --duration 10 \
  --bitrate 10M

Each execution automatically creates a timestamped log file.

## 7. Baseline Findings

The TCP experiment successfully generated sustained bulk traffic through the SDN-controlled topology.

The measured receiver throughput was 63.8 Gbit/s with 5 TCP retransmissions during the 10-second experiment.

The UDP experiment successfully generated the configured 10 Mbit/s traffic rate with 0% packet loss and 0.009 ms receiver-side jitter.

These measurements are treated as observed experimental results rather than fabricated or assumed QoS values.

## 8. Week 3 Outcome

Week 3 successfully establishes a repeatable traffic-generation framework.

The project now has:

- TCP traffic generation
- UDP traffic generation
- controlled experiment duration
- configurable UDP bitrate
- timestamped experiment logs
- baseline throughput measurements
- experiment screenshots

The generated traffic will be used with the telemetry collection pipeline for subsequent QoS feature extraction and dataset generation.

## 9. Next Step

Week 4 will focus on validating and processing the collected OpenFlow telemetry, handling counter resets, extracting QoS-related features, and generating the processed dataset.
