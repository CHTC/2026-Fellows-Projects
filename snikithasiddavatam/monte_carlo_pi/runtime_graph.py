import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import get_run_folders

BASE_DIR = "mc_runs"

run_folders = get_run_folders(BASE_DIR, with_results_csv=True)

if not run_folders:
    print("Error: No run_*/results.csv files found. Run aggregate.py first.")
    raise SystemExit(1)

print(f"Found {len(run_folders)} run(s): {run_folders}")

all_runs = {}
for run_folder in run_folders:
    cluster_id = run_folder[len("run_"):]
    csv_path = os.path.join(BASE_DIR, run_folder, "results.csv")
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    t0 = df["timestamp"].iloc[0]
    df["runtime_s"] = (df["timestamp"] - t0).dt.total_seconds()
    all_runs[cluster_id] = df
    print(f"  Loaded {run_folder}: {len(df)} jobs, "
          f"total runtime={df['runtime_s'].iloc[-1]:.1f}s")

sns.set_theme(style="darkgrid", palette="tab10", font_scale=1.1)
palette = sns.color_palette("tab10", n_colors=len(all_runs))

fig, ax = plt.subplots(figsize=(10, 6))
fig.suptitle(
    f"Runtime vs. Number of Samples — 10,000 samples/job ({len(all_runs)} cluster(s))",
    fontsize=13, fontweight="bold"
)

for i, (cluster_id, df) in enumerate(all_runs.items()):
    ax.plot(df["runtime_s"], df["N"],
            color=palette[i], linewidth=1.8, alpha=0.85,
            label=f"Run {cluster_id}")

ax.set_xlabel("Wall-clock Runtime (seconds)", fontsize=11)
ax.set_ylabel("Total Samples N", fontsize=11)
ax.set_title("Cumulative Samples vs. Elapsed Time", fontsize=11)
ax.legend(fontsize=9, loc="upper left")

plt.tight_layout()
output_path = f"{BASE_DIR}_runtime.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"\nPlot saved to {output_path}")
plt.show()

# --- Turnaround time graph: job termination time - cluster submit time ---
# turnaround_s is written by aggregate.py into each results.csv

turnaround_data = {}
for run_folder, df in zip(run_folders, all_runs.values()):
    cluster_id = run_folder[len("run_"):]
    if "turnaround_s" not in df.columns or df["turnaround_s"].isna().all():
        print(f"  Skipping {run_folder}: no turnaround_s in results.csv (re-run aggregate.py)")
        continue
    df_ta = df[["job_id", "turnaround_s"]].dropna().copy()
    turnaround_data[cluster_id] = df_ta
    print(f"  {run_folder}: {len(df_ta)} jobs, "
          f"turnaround min={df_ta['turnaround_s'].min():.1f}s "
          f"max={df_ta['turnaround_s'].max():.1f}s")

if turnaround_data:
    palette2 = sns.color_palette("tab10", n_colors=len(turnaround_data))
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    fig2.suptitle(
        f"Job Turnaround Time - Termination minus Cluster Submit ({len(turnaround_data)} cluster(s))",
        fontsize=13, fontweight="bold"
    )

    for i, (cluster_id, df_ta) in enumerate(turnaround_data.items()):
        ax2.scatter(df_ta["turnaround_s"], df_ta["job_id"],
                    color=palette2[i], s=20, alpha=0.7, label=f"Run {cluster_id}")

    ax2.set_xlabel("Turnaround Time (seconds)", fontsize=11)
    ax2.set_ylabel("Job ID (proc_id)", fontsize=11)
    ax2.set_title("Time from Cluster Submit to Job Termination", fontsize=11)
    ax2.legend(fontsize=9, loc="upper left")

    plt.tight_layout()
    turnaround_path = f"{BASE_DIR}_turnaround.png"
    plt.savefig(turnaround_path, dpi=150, bbox_inches="tight")
    print(f"\nTurnaround plot saved to {turnaround_path}")
    plt.show()
else:
    print("No turnaround data found — skipping turnaround plot.")
