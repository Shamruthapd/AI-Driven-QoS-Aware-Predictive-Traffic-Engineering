#!/usr/bin/env python3
"""
Generates the publication-quality Runtime Decision Loop Flow Diagram
for the final report and presentation slides.
Outputs: docs/final/flow-diagram.png
"""

from pathlib import Path

OUT_FILE = Path("docs/final/flow-diagram.png")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    fig, ax = plt.subplots(figsize=(12, 14), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 140)
    ax.axis("off")

    # Global Background
    ax.add_patch(patches.Rectangle((0, 0), 100, 140, facecolor="#f8fafc"))

    # Header Banner
    ax.text(50, 136, "Operational Workflow: Runtime Closed-Loop Decision Cycle",
            ha="center", va="center", fontsize=15, fontweight="bold", color="#0f172a")
    ax.text(50, 133, "Continuous AI-Driven Telemetry, Congestion Forecasting & Switch-Local Self-Healing",
            ha="center", va="center", fontsize=10.5, color="#475569")

    # 1. Start Node
    start_box = patches.FancyBboxPatch((35, 122), 30, 6.5, boxstyle="round,pad=0.5,rounding_size=3.25",
                                       facecolor="#10b981", edgecolor="#047857", linewidth=1.5)
    ax.add_patch(start_box)
    ax.text(50, 125.2, "START MONITORING (T = 5.0s)", ha="center", va="center", fontsize=10, fontweight="bold", color="#ffffff")

    # 2. Step 1: Collect Telemetry
    step1_box = patches.FancyBboxPatch((20, 107), 60, 10, boxstyle="round,pad=0.8,rounding_size=1.5",
                                       facecolor="#ffffff", edgecolor="#0284c7", linewidth=1.8)
    ax.add_patch(step1_box)
    ax.text(50, 114.5, "Step 1: Collect Data-Plane Telemetry (controller/app.py)", ha="center", fontsize=10, fontweight="bold", color="#0369a1")
    ax.text(50, 110, "• Controller polls switches via OFPPortStatsRequest every 5s\n• Extracts Tx/Rx byte counters, packet delta, and port status",
            ha="center", fontsize=8.5, color="#334155")

    # 3. Step 2: Feed LSTM
    step2_box = patches.FancyBboxPatch((20, 92), 60, 10, boxstyle="round,pad=0.8,rounding_size=1.5",
                                       facecolor="#ffffff", edgecolor="#8b5cf6", linewidth=1.8)
    ax.add_patch(step2_box)
    ax.text(50, 99.5, "Step 2: AI Forecasting & Anomaly Detection (ai-model/ai_loop.py)", ha="center", fontsize=10, fontweight="bold", color="#6d28d9")
    ax.text(50, 95, "• Sliding window buffer (W = 12 steps = 60s) fed into PyTorch LSTM (14.8 ms latency)\n• Forecasts link bandwidth demand 15–30s ahead; computes MSE residuals",
            ha="center", fontsize=8.5, color="#334155")

    # 4. Decision Diamond 1: Hard Link Failure?
    dia1 = patches.Polygon([[50, 87], [68, 80], [50, 73], [32, 80]], closed=True,
                           facecolor="#fef2f2", edgecolor="#ef4444", linewidth=1.8)
    ax.add_patch(dia1)
    ax.text(50, 80.5, "Hard Physical Link\nDown / Carrier Loss?", ha="center", va="center", fontsize=9.5, fontweight="bold", color="#b91c1c")

    # 5. Layer 1 Action: Switch-Local Fast Failover (Right branch)
    ff_box = patches.FancyBboxPatch((72, 73), 25, 14, boxstyle="round,pad=0.8,rounding_size=1.5",
                                    facecolor="#fee2e2", edgecolor="#b91c1c", linewidth=1.8)
    ax.add_patch(ff_box)
    ax.text(84.5, 84.5, "Layer 1: Switch-Local FF\n(controller/ff_groups.py)", ha="center", fontsize=9, fontweight="bold", color="#991b1b")
    ax.text(84.5, 77.5, "• Hardware loss flips to Bucket 1\n• Direct path (s1-eth4 <=> s2-eth4)\n• set_queue(1) preserved\n• Sub-second: 41.0 ms recovery!",
            ha="center", fontsize=7.5, color="#7f1d1d")

    # 6. Decision Diamond 2: Congestion Predicted?
    dia2 = patches.Polygon([[50, 68], [68, 61], [50, 54], [32, 61]], closed=True,
                           facecolor="#fffbeb", edgecolor="#f59e0b", linewidth=1.8)
    ax.add_patch(dia2)
    ax.text(50, 61.5, "LSTM Forecast:\nPredicted Util > 85%?", ha="center", va="center", fontsize=9.5, fontweight="bold", color="#b45309")

    # 7. Decision Diamond 3: Cooldown Active? (Left branch)
    dia3 = patches.Polygon([[18, 68], [30, 61], [18, 54], [6, 61]], closed=True,
                           facecolor="#fef3c7", edgecolor="#d97706", linewidth=1.5)
    ax.add_patch(dia3)
    ax.text(18, 61.2, "15s Cooldown\nTimer Active?", ha="center", va="center", fontsize=8, fontweight="bold", color="#92400e")

    # 8. Layer 2 Action: Proactive QoS Rerouting
    qos_box = patches.FancyBboxPatch((4, 37), 30, 13, boxstyle="round,pad=0.8,rounding_size=1.5",
                                     facecolor="#fef9c3", edgecolor="#ca8a04", linewidth=1.8)
    ax.add_patch(qos_box)
    ax.text(19, 47, "Layer 2: AI Proactive Reroute\n(self_healing_module.py)", ha="center", fontsize=9, fontweight="bold", color="#854d0e")
    ax.text(19, 41, "• Offload bulk TCP to backup Port 4\n• Priority VoIP/Video pinned to Q1\n• Rate-limit bulk to 4M ceiling (Q0)\n• 84% latency drop (7.6 ms)!",
            ha="center", fontsize=7.5, color="#713f12")

    # 9. Nominal Forwarding State
    norm_box = patches.FancyBboxPatch((38, 38), 34, 11, boxstyle="round,pad=0.8,rounding_size=1.5",
                                      facecolor="#f0fdf4", edgecolor="#16a34a", linewidth=1.8)
    ax.add_patch(norm_box)
    ax.text(55, 46.5, "Nominal Transmission State", ha="center", fontsize=9.5, fontweight="bold", color="#15803d")
    ax.text(55, 41.5, "• Primary path active (s1-s3-s2, 100 Mbps)\n• Queue 1 reserves 8-10M for VoIP/Video\n• Queue 0 transmits background bulk data",
            ha="center", fontsize=8, color="#166534")

    # 10. Step 5: Logging & Sync
    step5_box = patches.FancyBboxPatch((18, 16), 64, 13, boxstyle="round,pad=0.8,rounding_size=1.5",
                                       facecolor="#f8fafc", edgecolor="#475569", linewidth=1.8)
    ax.add_patch(step5_box)
    ax.text(50, 26, "Step 5: Telemetry Logging & Closed-Loop Synchronization", ha="center", fontsize=10, fontweight="bold", color="#1e293b")
    ax.text(50, 20.5, "• Synchronize logs to unified_event_log.csv and week11_summary_tables.csv\n• Measure recovery delay, latency (7.6 ms), jitter (1.2 ms), drops (0.12%), and goodput (9.4 Mbps)\n• Awaits next 5-second polling tick",
            ha="center", fontsize=8, color="#334155")

    # -----------------------------------------------------------
    # ARROWS & TRANSITIONS
    # -----------------------------------------------------------
    arrow_kw = dict(arrowstyle="->", color="#0f172a", lw=1.8, mutation_scale=12)

    # Start -> Step 1
    ax.annotate("", xy=(50, 117), xytext=(50, 122), arrowprops=arrow_kw)
    # Step 1 -> Step 2
    ax.annotate("", xy=(50, 102), xytext=(50, 107), arrowprops=arrow_kw)
    # Step 2 -> Dia 1
    ax.annotate("", xy=(50, 87), xytext=(50, 92), arrowprops=arrow_kw)

    # Dia 1 (YES) -> Fast Failover
    ax.annotate("", xy=(72, 80), xytext=(68, 80), arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2, mutation_scale=12))
    ax.text(70, 81.5, "YES", ha="center", fontsize=8.5, fontweight="bold", color="#dc2626")

    # Dia 1 (NO) -> Dia 2
    ax.annotate("", xy=(50, 68), xytext=(50, 73), arrowprops=dict(arrowstyle="->", color="#059669", lw=2, mutation_scale=12))
    ax.text(53, 70.5, "NO", ha="left", fontsize=8.5, fontweight="bold", color="#059669")

    # Dia 2 (YES) -> Dia 3
    ax.annotate("", xy=(30, 61), xytext=(32, 61), arrowprops=dict(arrowstyle="->", color="#d97706", lw=2, mutation_scale=12))
    ax.text(31, 62.5, "YES", ha="center", fontsize=8.5, fontweight="bold", color="#d97706")

    # Dia 2 (NO) -> Nominal
    ax.annotate("", xy=(55, 49), xytext=(50, 54), arrowprops=dict(arrowstyle="->", color="#059669", lw=2, mutation_scale=12))
    ax.text(55, 52, "NO", ha="center", fontsize=8.5, fontweight="bold", color="#059669")

    # Dia 3 (EXPIRED) -> QoS Reroute
    ax.annotate("", xy=(19, 50), xytext=(18, 54), arrowprops=dict(arrowstyle="->", color="#d97706", lw=2, mutation_scale=12))
    ax.text(23, 52, "EXPIRED (>15s)", ha="center", fontsize=7.5, fontweight="bold", color="#d97706")

    # Dia 3 (ACTIVE) -> Nominal
    ax.annotate("", xy=(38, 44), xytext=(30, 58), arrowprops=dict(arrowstyle="->", color="#64748b", lw=1.5, ls="--", mutation_scale=10))
    ax.text(34, 52, "ACTIVE", ha="center", fontsize=7, color="#64748b")

    # Actions to Step 5
    ax.annotate("", xy=(65, 29), xytext=(84.5, 73), arrowprops=dict(arrowstyle="->", color="#b91c1c", lw=1.5, mutation_scale=12))
    ax.annotate("", xy=(30, 29), xytext=(19, 37), arrowprops=dict(arrowstyle="->", color="#ca8a04", lw=1.5, mutation_scale=12))
    ax.annotate("", xy=(50, 29), xytext=(55, 38), arrowprops=dict(arrowstyle="->", color="#16a34a", lw=1.5, mutation_scale=12))

    # Loop Back Arrow from Step 5 to Step 1
    ax.plot([18, 8, 8, 20], [22, 22, 112, 112], color="#4f46e5", lw=2.2, ls="--")
    ax.annotate("", xy=(20, 112), xytext=(19.5, 112), arrowprops=dict(arrowstyle="->", color="#4f46e5", lw=2.2, mutation_scale=14))
    ax.text(7, 65, "Continuous 5-Second Closed Decision Loop", rotation=90, ha="center", va="center", fontsize=9, fontweight="bold", color="#4f46e5")

    plt.tight_layout()
    plt.savefig(OUT_FILE, format="png", bbox_inches="tight")
    plt.close()
    print(f"Successfully generated flow diagram at: {OUT_FILE.resolve()}")

except Exception as e:
    print(f"Error generating flow diagram: {e}")
