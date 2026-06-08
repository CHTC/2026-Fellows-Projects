import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
from utils import get_run_folders
BASE_DIR = "mc_runs"
PI_REF   = 3.14159265358979323846
run_folders = get_run_folders(BASE_DIR, with_results_csv=True)

if not run_folders:
    print("Error: No run_*/results.csv files found. Run aggregate.py first.")
    raise SystemExit(1)

print(f"Found {len(run_folders)} run(s): {run_folders}")

# load all runs 
all_runs = {}
for run_folder in run_folders:
    cluster_id = run_folder[len("run_"):]
    csv_path   = os.path.join(BASE_DIR, run_folder, "results.csv")
    df         = pd.read_csv(csv_path)
    all_runs[cluster_id] = df
    print(f"  Loaded {run_folder}: {len(df)} jobs, final error={df['error'].iloc[-1]:.2e}")

#plot Setup 
sns.set_theme(style="darkgrid", palette="tab10", font_scale=1.1)
palette   = sns.color_palette("tab10", n_colors=len(all_runs))
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle(
    f"Monte Carlo π Convergence - All Runs ({len(all_runs)} clusters)",
    fontsize=13, fontweight="bold", y=1.01
)

#plot 1: Scatter — π Estimate vs Cumulative Jobs 
ax1 = axes[0]

for i, (cluster_id, df) in enumerate(all_runs.items()):
    ax1.scatter(df["j"], df["pi_est"],
                color=palette[i], s=18, alpha=0.6,
                label=f"Run {cluster_id}")

ax1.axhline(y=PI_REF, color="red", linewidth=1.8,
            linestyle="--", label=f"True π", zorder=5)

ax1.set_xlabel("Cumulative Jobs Completed (j)", fontsize=11)
ax1.set_ylabel(r"Cumulative $\hat{\pi}$ Estimate", fontsize=11)
ax1.set_title("π Estimate vs. Cumulative Jobs - All Runs", fontsize=11)
ax1.legend(fontsize=8, markerscale=1.5, loc="upper left",
           bbox_to_anchor=(1.01, 1), borderaxespad=0)
ax1.annotate(f"{len(all_runs)} runs",
             xy=(0.03, 0.05), xycoords="axes fraction",
             fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

#plot 2: Scatter — Absolute Error vs Total Samples (log-log) 
ax2 = axes[1]

for i, (cluster_id, df) in enumerate(all_runs.items()):
    ax2.scatter(df["N"], df["error"],
                color=palette[i], s=18, alpha=0.6,
                label=f"Run {cluster_id}")

# 1/√N reference line scaled to median of first-point errors
first_errors = [df["error"].iloc[0] for df in all_runs.values()]
first_N      = list(all_runs.values())[0]["N"].iloc[0]
scale        = np.median(first_errors) * np.sqrt(first_N)
N_ref        = np.logspace(
                   np.log10(min(df["N"].min() for df in all_runs.values())),
                   np.log10(max(df["N"].max() for df in all_runs.values())),
                   300)
ax2.plot(N_ref, scale / np.sqrt(N_ref),
         color="red", linewidth=1.8, linestyle="--",
         label=r"$1/\sqrt{N}$ reference", zorder=5)

ax2.set_xscale("log")
ax2.set_yscale("log")
ax2.set_xlabel("Total Samples N", fontsize=11)
ax2.set_ylabel(r"Absolute Error $|\hat{\pi} - \pi_{ref}|$", fontsize=11)
ax2.set_title("Log-Log Convergence - All Runs", fontsize=11)
ax2.legend(fontsize=8, markerscale=1.5, loc="upper left",
           bbox_to_anchor=(1.01, 1), borderaxespad=0)

plt.tight_layout()
output_path = "all_runs_scatter.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"\nPlot saved to {output_path}")
plt.show()