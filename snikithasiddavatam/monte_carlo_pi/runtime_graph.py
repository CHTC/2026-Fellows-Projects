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
    ax.plot(df["N"], df["runtime_s"],
            color=palette[i], linewidth=1.8, alpha=0.85,
            label=f"Run {cluster_id}")

ax.set_xlabel("Total Samples N", fontsize=11)
ax.set_ylabel("Cumulative Runtime (seconds)", fontsize=11)
ax.set_title("Elapsed Time vs. Cumulative Samples", fontsize=11)
ax.legend(fontsize=9, loc="upper left")

plt.tight_layout()
output_path = f"{BASE_DIR}_runtime.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"\nPlot saved to {output_path}")
plt.show()
