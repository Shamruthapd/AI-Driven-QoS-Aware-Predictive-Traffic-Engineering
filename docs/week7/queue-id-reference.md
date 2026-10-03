# Member 2 to Member 1 Handshake: Queue ID Reference Map

| Queue ID | Priority Level | Rate Limits | Intended Traffic Class |
| :--- | :--- | :--- | :--- |
| **Queue 0** | Low / Best Effort | Max: 4.0 Mbps | Bulk Data (TCP streams) |
| **Queue 1** | High / Guaranteed | Min: 8.0 Mbps, Max: 10.0 Mbps | Priority Streams (Video / IoT UDP) |

### OpenFlow Enforcement Action Reference
When Member 1's controller detects predicted congestion ($>10\text{ Mbps}$):
- Direct Bulk Traffic to `Queue 0` (`OFPActionSetQueue(queue_id=0)`)
- Direct Priority Traffic to `Queue 1` (`OFPActionSetQueue(queue_id=1)`)
