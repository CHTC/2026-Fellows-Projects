import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("milestone_times.csv")

PERCENTILES = list(range(10, 110, 10))
pct_cols = [f"pct_{p}" for p in PERCENTILES]

GRAPH_DIR = "graphs/milestones"
os.makedirs(GRAPH_DIR, exist_ok=True)

sns.set_theme(style="darkgrid", font_scale=1.1)

for num_jobs, group in df.groupby("num_jobs"):
    palette = sns.color_palette("tab10", n_colors=len(group))

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.suptitle(
        f"Milestone Times — {num_jobs} jobs ({len(group)} runs)",
        fontsize=13, fontweight="bold",
    )

    for i, (_, row) in enumerate(group.iterrows()):
        times = [row[col] for col in pct_cols]
        ax.scatter(PERCENTILES, times, color=palette[i], s=40, alpha=0.7,
                   label=f"Run {row['run_id']}")

    ax.set_xlabel("Jobs Completed (%)", fontsize=11)
    ax.set_ylabel("Time from First Job Completion (s)", fontsize=11)
    ax.set_xticks(PERCENTILES)
    ax.set_xticklabels([f"{p}%" for p in PERCENTILES])
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)

    plt.tight_layout()
    out_path = os.path.join(GRAPH_DIR, f"milestones_{num_jobs}_jobs.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {out_path}")

print("\nDone.")
