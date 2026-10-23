#!/usr/bin/env python3
"""
Generates the publication-quality 3-Tier System Architecture Diagram
for the project report, slides, and documentation.
Outputs: docs/final/architecture-diagram.png
"""

from pathlib import Path

OUT_FILE = Path("docs/final/architecture-diagram.png")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    fig, ax = plt.subplots(figsize=(14, 10.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Global Background
    ax.add_patch(patches.Rectangle((0, 0), 100, 100, facecolor="#f8fafc"))

    # Title & Subtitle Header
    ax.text(50, 97.2, "AI-Driven QoS-Aware Predictive Traffic Engineering & Self-Healing",
            ha="center", va="center", fontsize=15, fontweight="bold", color="#0f172a")
    ax.text(50, 94.6, "System Architecture: Three-Tier Closed-Loop SDN Framework",
            ha="center", va="center", fontsize=11, fontweight="medium", color="#475569")

    # -------------------------------------------------------------
    # 1. APPLICATION & AI PLANE (Top Tier)
    # -------------------------------------------------------------
    ai_box = patches.FancyBboxPatch((4, 71), 92, 20.5, boxstyle="round,pad=1.2,rounding_size=2",
                                    linewidth=1.8, edgecolor="#8b5cf6", facecolor="#f5f3ff", zorder=1)
    ax.add_patch(ai_box)
    ax.text(7, 89.2, "APPLICATION & AI PLANE (PyTorch Runtime)", fontsize=11, fontweight="bold", color="#6d28d9")

    # Module 1.1: Telemetry Ingestion
    ax.add_patch(patches.FancyBboxPatch((6, 73.5), 26, 13.5, boxstyle="round,pad=0.8,rounding_size=1",
                                        facecolor="#ffffff", edgecolor="#c4b5fd", linewidth=1.2, zorder=2))
    ax.text(19, 84.5, "Telemetry Preprocessor", ha="center", fontsize=9.5, fontweight="bold", color="#4c1d95")
    ax.text(19, 78.5, "- Sliding Window (W=12)\n- 5-sec Polling Window\n- MinMax Scaling & Delta\n- Feature Normalization",
            ha="center", fontsize=8, color="#334155")

    # Module 1.2: LSTM Predictor
    ax.add_patch(patches.FancyBboxPatch((37, 73.5), 26, 13.5, boxstyle="round,pad=0.8,rounding_size=1",
                                        facecolor="#ffffff", edgecolor="#c4b5fd", linewidth=1.2, zorder=2))
    ax.text(50, 84.5, "PyTorch LSTM Forecaster", ha="center", fontsize=9.5, fontweight="bold", color="#4c1d95")
    ax.text(50, 78.5, "- 2-Layer LSTM Network\n- Inference Latency: 14.8 ms\n- Multi-Step Horizon (15-30s)\n- Low RMSE Traffic Estimator",
            ha="center", fontsize=8, color="#334155")

    # Module 1.3: Self-Healing Decision Engine
    ax.add_patch(patches.FancyBboxPatch((68, 73.5), 26, 13.5, boxstyle="round,pad=0.8,rounding_size=1",
                                        facecolor="#ffffff", edgecolor="#c4b5fd", linewidth=1.2, zorder=2))
    ax.text(81, 84.5, "Self-Healing Decision Engine", ha="center", fontsize=9.5, fontweight="bold", color="#4c1d95")
    ax.text(81, 78.5, "- Congestion Threshold (>85%)\n- 15s Cooldown & Hysteresis\n- Anti-Route Oscillation\n- Bulk Offload Decisions",
            ha="center", fontsize=8, color="#334155")

    # -------------------------------------------------------------
    # 2. CONTROL PLANE (Middle Tier)
    # -------------------------------------------------------------
    ctrl_box = patches.FancyBboxPatch((4, 38.5), 92, 24.5, boxstyle="round,pad=1.2,rounding_size=2",
                                      linewidth=1.8, edgecolor="#0284c7", facecolor="#f0f9ff", zorder=1)
    ax.add_patch(ctrl_box)
    ax.text(7, 60.5, "CONTROL PLANE (OS-Ken / Ryu SDN Controller - OpenFlow 1.3)", fontsize=11, fontweight="bold", color="#0369a1")

    # Module 2.1: REST Bridge
    ax.add_patch(patches.FancyBboxPatch((6, 41), 20.5, 17, boxstyle="round,pad=0.8,rounding_size=1",
                                        facecolor="#ffffff", edgecolor="#7dd3fc", linewidth=1.2, zorder=2))
    ax.text(16.25, 55.5, "AI-SDN REST Bridge\n(controller/ai_sdn_bridge.py)", ha="center", fontsize=8.5, fontweight="bold", color="#075985")
    ax.text(16.25, 47.5, "- JSON Stats Exporter\n- Asynchronous IPC\n- Operational Mode\n  Switch (3 Modes)\n- Event Timeline Logger",
            ha="center", fontsize=7.5, color="#334155")

    # Module 2.2: Flow Classifier
    ax.add_patch(patches.FancyBboxPatch((29.5, 41), 20.5, 17, boxstyle="round,pad=0.8,rounding_size=1",
                                        facecolor="#ffffff", edgecolor="#7dd3fc", linewidth=1.2, zorder=2))
    ax.text(39.75, 55.5, "QoS Flow Classifier\n(controller/flow_classifier.py)", ha="center", fontsize=8.5, fontweight="bold", color="#075985")
    ax.text(39.75, 47.5, "- DSCP Marking (EF / CS0)\n- L4 Port Demux (UDP/TCP)\n- Metadata Tagging\n- Priority Flow Pinning\n- Queue Id Assignment",
            ha="center", fontsize=7.5, color="#334155")

    # Module 2.3: Fast-Failover Manager
    ax.add_patch(patches.FancyBboxPatch((53, 41), 20.5, 17, boxstyle="round,pad=0.8,rounding_size=1",
                                        facecolor="#ffffff", edgecolor="#7dd3fc", linewidth=1.2, zorder=2))
    ax.text(63.25, 55.5, "Fast-Failover Manager\n(controller/ff_groups.py)", ha="center", fontsize=8.5, fontweight="bold", color="#075985")
    ax.text(63.25, 47.5, "- Group 100/200 Install\n- Bucket 0: Primary (Port 3)\n- Bucket 1: Backup (Port 4)\n- `set_queue` in BOTH buckets\n- OFP_GROUP_MOD",
            ha="center", fontsize=7.5, color="#334155")

    # Module 2.4: Port Status & Telemetry
    ax.add_patch(patches.FancyBboxPatch((76.5, 41), 17.5, 17, boxstyle="round,pad=0.8,rounding_size=1",
                                        facecolor="#ffffff", edgecolor="#7dd3fc", linewidth=1.2, zorder=2))
    ax.text(85.25, 55.5, "Telemetry Collector\n(controller/app.py)", ha="center", fontsize=8.5, fontweight="bold", color="#075985")
    ax.text(85.25, 47.5, "- OFPPortStatsRequest\n- Tx/Rx Delta Tracker\n- OFPPortStatus Handler\n- Unified Event CSV\n  Synchronization",
            ha="center", fontsize=7.5, color="#334155")

    # -------------------------------------------------------------
    # 3. DATA PLANE (Bottom Tier)
    # -------------------------------------------------------------
    data_box = patches.FancyBboxPatch((4, 3), 92, 28, boxstyle="round,pad=1.2,rounding_size=2",
                                      linewidth=1.8, edgecolor="#16a34a", facecolor="#f0fdf4", zorder=1)
    ax.add_patch(data_box)
    ax.text(7, 28.5, "DATA PLANE (Mininet & Open vSwitch 2.17+ with Linux HTB Queuing)", fontsize=11, fontweight="bold", color="#15803d")

    # Edge Switch s1
    ax.add_patch(patches.FancyBboxPatch((6, 7.5), 25, 18.5, boxstyle="round,pad=0.6,rounding_size=1",
                                        facecolor="#ffffff", edgecolor="#86efac", linewidth=1.2, zorder=2))
    ax.text(18.5, 23.5, "Edge Switch (s1)", ha="center", fontsize=9.5, fontweight="bold", color="#166534")
    ax.text(18.5, 15.5, "- FF Group 100 (Primary/Backup)\n- Port 3: Primary (s1->s3)\n- Port 4: Backup (s1->s2)\n- HTB Q0 (Bulk <= 4M)\n- HTB Q1 (Priority 8-10M)\n- Switch-Local Recovery (41 ms)",
            ha="center", fontsize=7.5, color="#334155")

    # Core Switch s3
    ax.add_patch(patches.FancyBboxPatch((38, 12), 24, 14, boxstyle="round,pad=0.6,rounding_size=1",
                                        facecolor="#ffffff", edgecolor="#86efac", linewidth=1.2, zorder=2))
    ax.text(50, 23.5, "Core Switch (s3)", ha="center", fontsize=9.5, fontweight="bold", color="#166534")
    ax.text(50, 16.5, "- Transit Backbone Switch\n- High-Speed 100 Mbps Trunk\n- Connects s1-eth3 & s2-eth3\n- Normal L2/L3 Forwarding",
            ha="center", fontsize=7.5, color="#334155")

    # Edge Switch s2
    ax.add_patch(patches.FancyBboxPatch((69, 7.5), 25, 18.5, boxstyle="round,pad=0.6,rounding_size=1",
                                        facecolor="#ffffff", edgecolor="#86efac", linewidth=1.2, zorder=2))
    ax.text(81.5, 23.5, "Edge Switch (s2)", ha="center", fontsize=9.5, fontweight="bold", color="#166534")
    ax.text(81.5, 15.5, "- FF Group 200 (Primary/Backup)\n- Port 3: Primary (s2->s3)\n- Port 4: Backup (s2->s1)\n- HTB Q0 (Bulk <= 4M)\n- HTB Q1 (Priority 8-10M)\n- Switch-Local Recovery (41 ms)",
            ha="center", fontsize=7.5, color="#334155")

    # Hosts under switches
    ax.text(18.5, 4.8, "Hosts: h1 (10.0.0.1 - VoIP/Video) | h2 (10.0.0.2 - Bulk TCP)",
            ha="center", fontsize=7.8, fontweight="bold", color="#0f766e")
    ax.text(81.5, 4.8, "Hosts: h3 (10.0.0.3 - VoIP/Video) | h4 (10.0.0.4 - Bulk TCP)",
            ha="center", fontsize=7.8, fontweight="bold", color="#0f766e")

    # -------------------------------------------------------------
    # INTER-PLANE COMMUNICATION ARROWS & LABELS
    # -------------------------------------------------------------
    # AI <-> Control Arrow
    ax.annotate("", xy=(30, 63), xytext=(30, 71),
                arrowprops=dict(arrowstyle="<->", color="#9333ea", lw=2, mutation_scale=15))
    ax.text(28.5, 67, "Northbound REST / JSON IPC\n(Tx/Rx Telemetry Streams)", 
            ha="right", va="center", fontsize=8, fontweight="bold", color="#7e22ce")

    ax.annotate("", xy=(70, 63), xytext=(70, 71),
                arrowprops=dict(arrowstyle="<->", color="#9333ea", lw=2, mutation_scale=15))
    ax.text(71.5, 67, "AI Control Directives\n(Proactive Reroute / Rate Limit)", 
            ha="left", va="center", fontsize=8, fontweight="bold", color="#7e22ce")

    # Control <-> Data Plane Arrow
    ax.annotate("", xy=(25, 31), xytext=(25, 38.5),
                arrowprops=dict(arrowstyle="<->", color="#0284c7", lw=2, mutation_scale=15))
    ax.text(23.5, 34.8, "OpenFlow 1.3 (TCP 6633)\nFlowMod / GroupMod / PacketIn", 
            ha="right", va="center", fontsize=8, fontweight="bold", color="#0369a1")

    ax.annotate("", xy=(75, 31), xytext=(75, 38.5),
                arrowprops=dict(arrowstyle="<->", color="#0284c7", lw=2, mutation_scale=15))
    ax.text(76.5, 34.8, "OpenFlow 1.3 Telemetry\nPortStats / PortStatus Asynchronous Events", 
            ha="left", va="center", fontsize=8, fontweight="bold", color="#0369a1")

    # Inter-switch links inside Data Plane
    ax.plot([31, 38], [18, 18], color="#0284c7", lw=2.5) # s1 to s3
    ax.plot([62, 69], [18, 18], color="#0284c7", lw=2.5) # s3 to s2
    ax.plot([31, 69], [9.5, 9.5], color="#ea580c", lw=2, linestyle="--") # s1 to s2 direct
    ax.text(50, 8.2, "Redundant Path (s1-s2: 100 Mbps) [Fast-Failover & AI Bulk Offload]",
            ha="center", fontsize=7.2, fontweight="bold", color="#c2410c")

    plt.tight_layout()
    plt.savefig(OUT_FILE, format="png", bbox_inches="tight")
    plt.close()
    print(f"Successfully generated architecture diagram at: {OUT_FILE.resolve()}")

except Exception as e:
    print(f"Error generating diagram: {e}")
