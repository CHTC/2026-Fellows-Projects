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


# combined scatter plot: all job sizes, colored by num_jobs 
job_sizes = sorted(df["num_jobs"].unique())
palette_combined = sns.color_palette("tab10", n_colors=len(job_sizes))
color_map = dict(zip(job_sizes, palette_combined))

fig, ax = plt.subplots(figsize=(10, 6))
fig.suptitle("Milestone Times — All Job Sizes", fontsize=13, fontweight="bold")

for num_jobs in job_sizes:
    group = df[df["num_jobs"] == num_jobs]
    xs, ys = [], []
    for _, row in group.iterrows():
        xs.extend(PERCENTILES)
        ys.extend(row[col] for col in pct_cols)
    ax.scatter(xs, ys, color=color_map[num_jobs], s=30, alpha=0.6,
               label=f"{num_jobs} jobs")

ax.set_xlabel("Jobs Completed (%)", fontsize=11)
ax.set_ylabel("Time from First Job Completion (s)", fontsize=11)
ax.set_yscale("log")
ax.set_xticks(PERCENTILES)
ax.set_xticklabels([f"{p}%" for p in PERCENTILES])
ax.legend(fontsize=9, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)

plt.tight_layout()
combined_path = os.path.join(GRAPH_DIR, "milestones_combined.png")
plt.savefig(combined_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved {combined_path}")

print("\nDone.")
