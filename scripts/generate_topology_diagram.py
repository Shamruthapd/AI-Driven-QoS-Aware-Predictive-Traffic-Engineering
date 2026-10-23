#!/usr/bin/env python3
"""
Generates the official finalized network topology diagram for the final report.
Outputs: docs/final/topology-final.png
"""

from pathlib import Path

OUT_FILE = Path("docs/final/topology-final.png")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Background
    ax.add_patch(patches.Rectangle((0, 0), 100, 100, facecolor="#f8f9fa"))

    # Title
    ax.text(50, 94, "Final Network Topology: Edge Fat-Tree with Fast-Failover & QoS",
            ha="center", va="center", fontsize=14, fontweight="bold", color="#1a252f")
    ax.text(50, 90, "AI-Driven QoS-Aware Predictive Traffic Engineering & Self-Healing",
            ha="center", va="center", fontsize=10, color="#7f8c8d")

    # Node positions
    # Core Switch
    s3_pos = (50, 68)
    # Edge Switches
    s1_pos = (28, 42)
    s2_pos = (72, 42)
    # Hosts
    h1_pos = (15, 18)
    h2_pos = (35, 18)
    h3_pos = (65, 18)
    h4_pos = (85, 18)

    # Links
    # s1 - s3 (Primary 100 Mbps)
    ax.plot([s1_pos[0], s3_pos[0]], [s1_pos[1], s3_pos[1]], color="#2980b9", linewidth=3.5, zorder=1)
    ax.text(36, 57, "s1-eth3 <-> s3-eth1\n100 Mbps (Primary Path)\nQoS Queues: Q0, Q1", 
            ha="center", va="center", fontsize=8.5, color="#2980b9", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#ebf5fb", edgecolor="#2980b9", alpha=0.9))

    # s2 - s3 (Primary 100 Mbps)
    ax.plot([s2_pos[0], s3_pos[0]], [s2_pos[1], s3_pos[1]], color="#2980b9", linewidth=3.5, zorder=1)
    ax.text(64, 57, "s2-eth3 <-> s3-eth2\n100 Mbps (Primary Path)\nQoS Queues: Q0, Q1", 
            ha="center", va="center", fontsize=8.5, color="#2980b9", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#ebf5fb", edgecolor="#2980b9", alpha=0.9))

    # s1 - s2 (Redundant direct link 100 Mbps)
    ax.plot([s1_pos[0], s2_pos[0]], [s1_pos[1], s2_pos[1]], color="#e67e22", linewidth=3.5, linestyle="--", zorder=1)
    ax.text(50, 37, "s1-eth4 <-> s2-eth4 (Redundant Backup Link: 100 Mbps)\nFast-Failover Alternate Bucket & AI Bulk Offload Path\nQoS Queues: Q0 (Bulk), Q1 (Priority)", 
            ha="center", va="center", fontsize=8.5, color="#d35400", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#fef5e7", edgecolor="#e67e22", alpha=0.9))

    # Host access links (10 Mbps)
    host_links = [
        (h1_pos, s1_pos, "s1-eth1 (10M)"),
        (h2_pos, s1_pos, "s1-eth2 (10M, Q0/Q1)"),
        (h3_pos, s2_pos, "s2-eth1 (10M)"),
        (h4_pos, s2_pos, "s2-eth2 (10M, Q0/Q1)")
    ]
    for h_pos, s_pos, lbl in host_links:
        ax.plot([h_pos[0], s_pos[0]], [h_pos[1], s_pos[1]], color="#7f8c8d", linewidth=2, zorder=1)
        ax.text((h_pos[0] + s_pos[0])/2, (h_pos[1] + s_pos[1])/2, lbl,
                ha="center", va="center", fontsize=7.5, color="#34495e",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="#bdc3c7", alpha=0.8))

    # Draw Switches (Rectangles)
    def draw_switch(pos, name, dpid, role):
        w, h = 18, 9
        rect = patches.FancyBboxPatch((pos[0]-w/2, pos[1]-h/2), w, h, boxstyle="round,pad=0.3",
                                      facecolor="#34495e", edgecolor="#1a252f", linewidth=1.5, zorder=3)
        ax.add_patch(rect)
        ax.text(pos[0], pos[1]+1.8, name, ha="center", va="center", fontsize=11, fontweight="bold", color="white", zorder=4)
        ax.text(pos[0], pos[1]-0.2, f"DPID={dpid} | OF 1.3", ha="center", va="center", fontsize=8, color="#ecf0f1", zorder=4)
        ax.text(pos[0], pos[1]-2.2, role, ha="center", va="center", fontsize=7.5, color="#f1c40f", zorder=4)

    draw_switch(s3_pos, "Core Switch s3", "3", "Backbone Transit")
    draw_switch(s1_pos, "Edge Switch s1", "1", "Ingress / FF Group 100")
    draw_switch(s2_pos, "Edge Switch s2", "2", "Egress / FF Group 200")

    # Draw Hosts (Circles)
    def draw_host(pos, name, ip, mac, role):
        circ = patches.Circle(pos, radius=4.5, facecolor="#27ae60", edgecolor="#1e8449", linewidth=1.5, zorder=3)
        ax.add_patch(circ)
        ax.text(pos[0], pos[1]+1.2, name, ha="center", va="center", fontsize=9.5, fontweight="bold", color="white", zorder=4)
        ax.text(pos[0], pos[1]-0.6, ip, ha="center", va="center", fontsize=7.5, color="white", zorder=4)
        ax.text(pos[0], pos[1]-2.0, role, ha="center", va="center", fontsize=6.5, color="#f9e79f", zorder=4)

    draw_host(h1_pos, "Host h1", "10.0.0.1", "00:00:00:00:00:01", "Priority Sender")
    draw_host(h2_pos, "Host h2", "10.0.0.2", "00:00:00:00:00:02", "Bulk Sender / IoT")
    draw_host(h3_pos, "Host h3", "10.0.0.3", "00:00:00:00:00:03", "Priority Recv")
    draw_host(h4_pos, "Host h4", "10.0.0.4", "00:00:00:00:00:04", "Bulk Recv")

    # Legend / Info Box
    legend_box = patches.FancyBboxPatch((4, 4), 92, 7, boxstyle="round,pad=0.2",
                                        facecolor="#eaeded", edgecolor="#bdc3c7", linewidth=1, zorder=2)
    ax.add_patch(legend_box)
    legend_text = (
        "Queue 0 (Best-Effort): max-rate=4 Mbps (Capped)  |  "
        "Queue 1 (Priority): min-rate=8 Mbps, max-rate=10 Mbps (Guaranteed)\n"
        "Fast-Failover: Primary Bucket watch=Port 3 (s3), Backup Bucket watch=Port 4 (s2)  |  "
        "set_queue actions embedded in both buckets"
    )
    ax.text(50, 7.5, legend_text, ha="center", va="center", fontsize=8, color="#2c3e50", fontweight="semibold")

    plt.tight_layout()
    plt.savefig(OUT_FILE, dpi=300)
    plt.close()
    print(f"[+] Saved final topology diagram: {OUT_FILE}")
except Exception as e:
    print(f"Error creating diagram: {e}")
