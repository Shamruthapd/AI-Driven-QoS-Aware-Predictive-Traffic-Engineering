# Week 7: Queue Configuration & Verification Log
## OVS QoS Table
_uuid               : e622787c-60aa-4514-8285-4bc6c77f0c31
external_ids        : {}
other_config        : {max-rate="10000000"}
queues              : {0=97065ed3-3892-4299-a35b-1f4974ba224b, 1=b351534a-0213-4967-b078-338b8dfab9b1}
type                : linux-htb

_uuid               : 57ff2ede-2e34-49dd-8f46-db9a992e9ff7
external_ids        : {}
other_config        : {max-rate="10000000"}
queues              : {0=47d3b11b-04c7-4379-8346-4a0253c8fcb4, 1=c6f5b2a5-0a77-4d32-864d-2326b682b27b}
type                : linux-htb

## OVS Queue Table
_uuid               : c6f5b2a5-0a77-4d32-864d-2326b682b27b
dscp                : []
external_ids        : {}
other_config        : {max-rate="10000000", min-rate="8000000"}

_uuid               : b351534a-0213-4967-b078-338b8dfab9b1
dscp                : []
external_ids        : {}
other_config        : {max-rate="10000000", min-rate="8000000"}

_uuid               : 47d3b11b-04c7-4379-8346-4a0253c8fcb4
dscp                : []
external_ids        : {}
other_config        : {max-rate="4000000"}

_uuid               : 97065ed3-3892-4299-a35b-1f4974ba224b
dscp                : []
external_ids        : {}
other_config        : {max-rate="4000000"}

## Linux Traffic Control (tc) Qdisc Status
qdisc htb 1: root refcnt 13 r2q 10 default 0x1 direct_packets_stat 0 direct_qlen 1000
 Sent 70 bytes 1 pkt (dropped 0, overlimits 0 requeues 0) 
 backlog 0b 0p requeues 0
