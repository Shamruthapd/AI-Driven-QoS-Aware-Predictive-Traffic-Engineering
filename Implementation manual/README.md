# Implementation Manual Directory

This directory contains the complete technical documentation, step-by-step execution guides, and system diagrams for reproducing the academic project:

**"AI-Driven QoS-Aware Predictive Traffic Engineering and Self-Healing in SDN-Based Edge Networks"**

---

## Directory Contents

* **[`Implementation_Manual.md`](Implementation_Manual.md):** The comprehensive implementation manual covering:
  1. Project overview and system architecture.
  2. Hardware specifications and software requirements.
  3. Dependencies and installation instructions.
  4. Project folder structure and key files.
  5. Network topology and physical/logical port mappings.
  6. Controller implementation, OpenFlow 1.3 rules, Fast-Failover groups, HTB QoS queues, and AI telemetry.
  7. Configuration parameters (`config.yaml`, `S3_failure.yaml`).
  8. Step-by-step terminal execution commands.
  9. Preflight testing and verification procedures.
  10. Logs, CSV datasets, and empirical result comparisons.
  11. Troubleshooting guide and common error resolutions.
  12. Known limitations and reproducibility notes.

* **`diagrams/`:** Architecture, workflow, and network topology visual assets:
  * [`architecture-diagram.png`](diagrams/architecture-diagram.png) & [`architecture-diagram.drawio`](diagrams/architecture-diagram.drawio): System architecture diagram (editable and rendered).
  * [`flow-diagram.png`](diagrams/flow-diagram.png) & [`flow-diagram.drawio`](diagrams/flow-diagram.drawio): Control and data plane failover workflow diagram (editable and rendered).
  * [`topology-final.png`](diagrams/topology-final.png): 4-host, 3-switch edge mesh topology layout.

---

For top-level repository context and submission details, refer to the root [`../README.md`](../README.md).
