import os
import csv
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import htcondor2 as htcondor
from datetime import datetime
from utils import get_run_folders

BASE_DIR = "mc_runs_1000"
GRAPH_DIR = "graphs/1000_jobs"
PI_REF = 3.14159265358979323846

os.makedirs(GRAPH_DIR, exist_ok=True)


run_folders = get_run_folders(BASE_DIR, with_results_csv=False)
if not run_folders:
    print("Error: No run_* folders found.")
    sys.exit(1)

print(f"Found {len(run_folders)} run folder(s)")

for run_folder in run_folders:
    run_path   = os.path.join(BASE_DIR, run_folder)
    logs_dir   = os.path.join(run_path, "logs")
    log_file   = os.path.join(logs_dir, "logs", "mc_pi.log")
    output_csv = os.path.join(run_path, "results.csv")

    if os.path.isfile(output_csv):
        print(f"  {run_folder}: results.csv already exists — skipping aggregate.")
        continue

    print(f"\n--- Aggregating {run_folder} ---")

    if not os.path.isfile(log_file):
        print(f"  Warning: Log file not found at {log_file} — skipping.")
        continue

    jobs = {}
    for filename in os.listdir(logs_dir):
        if not (filename.startswith("output_") and filename.endswith(".txt")):
            continue
        filepath = os.path.join(logs_dir, filename)
        try:
            data = {}
            with open(filepath) as f:
                for line in f:
                    if "=" not in line:
                        continue
                    key, val = line.strip().split("=", 1)
                    data[key] = val
            required = ("job_id", "samples", "hits", "pi_estimate")
            missing = [k for k in required if k not in data]
            if missing:
                print(f"  Skipping {filename}: missing {missing}")
                continue
            job_id = int(data["job_id"])
            jobs[job_id] = {
                "job_id":      job_id,
                "samples":     int(data["samples"]),
                "hits":        int(data["hits"]),
                "pi_estimate": float(data["pi_estimate"]),
            }
        except (OSError, KeyError, ValueError) as e:
            print(f"  Skipping {filename}: {e}")

    print(f"  Found {len(jobs)} valid output files.")
    if not jobs:
        continue

    timestamps   = {}
    submit_times = {}
    try:
        jel = htcondor.JobEventLog(log_file)
        for event in jel.events(stop_after=0):
            if event.type == htcondor.JobEventType.SUBMIT:
                submit_times[event.proc] = datetime.fromtimestamp(event.timestamp)
            elif event.type == htcondor.JobEventType.JOB_TERMINATED:
                timestamps[event.proc] = datetime.fromtimestamp(event.timestamp)
    except Exception as e:
        print(f"  Warning: Could not parse log file: {e} — skipping.")
        continue

    cluster_submit_time = min(submit_times.values()) if submit_times else None
    print(f"  Cluster submit time: {cluster_submit_time}")
    print(f"  Found {len(timestamps)} termination entries.")

    valid_jobs = []
    for job_id, job_data in jobs.items():
        if job_id in timestamps:
            job_data["timestamp"]    = timestamps[job_id]
            job_data["submit_time"]  = submit_times.get(job_id)
            job_data["turnaround_s"] = (
                (timestamps[job_id] - cluster_submit_time).total_seconds()
                if cluster_submit_time else None
            )
            valid_jobs.append(job_data)

    print(f"  Valid jobs: {len(valid_jobs)}")
    if not valid_jobs:
        continue

    valid_jobs.sort(key=lambda x: x["timestamp"])

    S = valid_jobs[0]["samples"]
    M_total = 0
    results = []
    for j, job in enumerate(valid_jobs, start=1):
        M_total += job["hits"]
        S_total  = j * S
        pi_est   = 4.0 * M_total / S_total
        results.append({
            "j":            j,
            "job_id":       job["job_id"],
            "submit_time":  job.get("submit_time"),
            "timestamp":    job["timestamp"],
            "turnaround_s": job.get("turnaround_s"),
            "N":            S_total,
            "pi_est":       pi_est,
            "error":        abs(pi_est - PI_REF),
        })

    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["j","job_id","submit_time","timestamp","turnaround_s","N","pi_est","error"]
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"  Saved {len(results)} rows → {output_csv}")
    print(f"  Final π: {results[-1]['pi_est']:.8f}  error: {results[-1]['error']:.2e}")


run_folders = get_run_folders(BASE_DIR, with_results_csv=True)
if not run_folders:
    print("Error: No results.csv found after aggregation.")
    sys.exit(1)

all_runs = {}
for run_folder in run_folders:
    cluster_id = run_folder[len("run_"):]
    csv_path   = os.path.join(BASE_DIR, run_folder, "results.csv")
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    all_runs[cluster_id] = df
    print(f"  Loaded {run_folder}: {len(df)} jobs, final error={df['error'].iloc[-1]:.2e}")


sns.set_theme(style="darkgrid", palette="tab10", font_scale=1.1)
palette = sns.color_palette("tab10", n_colors=len(all_runs))

fig, axes = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle(
    f"Monte Carlo π Convergence — All Runs ({len(all_runs)} clusters, 1,000 jobs each)",
    fontsize=13, fontweight="bold", y=1.01,
)

ax1 = axes[0]
for i, (cluster_id, df) in enumerate(all_runs.items()):
    ax1.scatter(df["j"], df["pi_est"], color=palette[i], s=18, alpha=0.6,
                label=f"Run {cluster_id}")
ax1.axhline(y=PI_REF, color="red", linewidth=1.8, linestyle="--", label="True π", zorder=5)
ax1.set_xlabel("Cumulative Jobs Completed (j)", fontsize=11)
ax1.set_ylabel(r"Cumulative $\hat{\pi}$ Estimate", fontsize=11)
ax1.set_title("π Estimate vs. Cumulative Jobs", fontsize=11)
ax1.legend(fontsize=8, markerscale=1.5, loc="upper left",
           bbox_to_anchor=(1.01, 1), borderaxespad=0)
ax1.annotate(f"{len(all_runs)} runs", xy=(0.03, 0.05), xycoords="axes fraction",
             fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

ax2 = axes[1]
for i, (cluster_id, df) in enumerate(all_runs.items()):
    ax2.scatter(df["N"], df["error"], color=palette[i], s=18, alpha=0.6,
                label=f"Run {cluster_id}")

first_errors = [df["error"].iloc[0] for df in all_runs.values()]
first_N      = list(all_runs.values())[0]["N"].iloc[0]
scale        = np.median(first_errors) * np.sqrt(first_N)
N_ref = np.logspace(
    np.log10(min(df["N"].min() for df in all_runs.values())),
    np.log10(max(df["N"].max() for df in all_runs.values())),
    300,
)
ax2.plot(N_ref, scale / np.sqrt(N_ref), color="red", linewidth=1.8,
         linestyle="--", label=r"$1/\sqrt{N}$ reference", zorder=5)
ax2.set_xscale("log")
ax2.set_yscale("log")
ax2.set_xlabel("Total Samples N", fontsize=11)
ax2.set_ylabel(r"Absolute Error $|\hat{\pi} - \pi_{ref}|$", fontsize=11)
ax2.set_title("Log-Log Convergence — All Runs", fontsize=11)
ax2.legend(fontsize=8, markerscale=1.5, loc="upper left",
           bbox_to_anchor=(1.01, 1), borderaxespad=0)

plt.tight_layout()
scatter_path = os.path.join(GRAPH_DIR, "mc_runs_1000_scatter.png")
plt.savefig(scatter_path, dpi=150, bbox_inches="tight")
print(f"\nScatter plot saved to {scatter_path}")
plt.close()


fig2, ax3 = plt.subplots(figsize=(10, 6))
fig2.suptitle(
    f"Runtime vs. Number of Samples — 1,000 samples/job ({len(all_runs)} cluster(s))",
    fontsize=13, fontweight="bold",
)
for i, (cluster_id, df) in enumerate(all_runs.items()):
    t0 = df["timestamp"].iloc[0]
    df = df.copy()
    df["runtime_s"] = (df["timestamp"] - t0).dt.total_seconds()
    ax3.plot(df["runtime_s"], df["N"], color=palette[i], linewidth=1.8,
             alpha=0.85, label=f"Run {cluster_id}")

ax3.set_xlabel("Wall-clock Runtime (seconds)", fontsize=11)
ax3.set_ylabel("Total Samples N", fontsize=11)
ax3.set_title("Cumulative Samples vs. Elapsed Time", fontsize=11)
ax3.legend(fontsize=9, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
plt.tight_layout()
runtime_path = os.path.join(GRAPH_DIR, "mc_runs_1000_runtime.png")
plt.savefig(runtime_path, dpi=150, bbox_inches="tight")
print(f"Runtime plot saved to {runtime_path}")
plt.close()


fig4, ax5 = plt.subplots(figsize=(10, 6))
fig4.suptitle(
    f"Runtime vs. Number of Jobs — 1,000 jobs ({len(all_runs)} cluster(s))",
    fontsize=13, fontweight="bold",
)
for i, (cluster_id, df) in enumerate(all_runs.items()):
    t0 = df["timestamp"].iloc[0]
    df = df.copy()
    df["runtime_s"] = (df["timestamp"] - t0).dt.total_seconds()
    ax5.plot(df["runtime_s"], df["j"], color=palette[i], linewidth=1.8,
             alpha=0.85, label=f"Run {cluster_id}")

ax5.set_xlabel("Time from First Job Completion (s)", fontsize=11)
ax5.set_ylabel("Total Jobs Completed", fontsize=11)
ax5.set_title("Cumulative Jobs vs. Elapsed Time", fontsize=11)
ax5.legend(fontsize=9, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
plt.tight_layout()
runtime_jobs_path = os.path.join(GRAPH_DIR, "mc_runs_1000_runtime_jobs.png")
plt.savefig(runtime_jobs_path, dpi=150, bbox_inches="tight")
print(f"Runtime jobs plot saved to {runtime_jobs_path}")
plt.close()


turnaround_data = {}
for run_folder in get_run_folders(BASE_DIR, with_results_csv=True):
    cluster_id = run_folder[len("run_"):]
    df = all_runs[cluster_id]
    if "turnaround_s" not in df.columns or df["turnaround_s"].isna().all():
        print(f"  Skipping {run_folder}: no turnaround_s")
        continue
    turnaround_data[cluster_id] = df[["job_id", "turnaround_s"]].dropna().copy()

if turnaround_data:
    palette2 = sns.color_palette("tab10", n_colors=len(turnaround_data))
    fig3, ax4 = plt.subplots(figsize=(10, 6))
    fig3.suptitle(
        f"Job Turnaround Time — Termination minus Cluster Submit ({len(turnaround_data)} cluster(s))",
        fontsize=13, fontweight="bold",
    )
    for i, (cluster_id, df_ta) in enumerate(turnaround_data.items()):
        ax4.scatter(df_ta["turnaround_s"], df_ta["job_id"],
                    color=palette2[i], s=20, alpha=0.7, label=f"Run {cluster_id}")
    ax4.set_xlabel("Turnaround Time (seconds)", fontsize=11)
    ax4.set_ylabel("Job ID (proc_id)", fontsize=11)
    ax4.set_title("Time from Cluster Submit to Job Termination", fontsize=11)
    ax4.legend(fontsize=9, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
    plt.tight_layout()
    turnaround_path = os.path.join(GRAPH_DIR, "mc_runs_1000_turnaround.png")
    plt.savefig(turnaround_path, dpi=150, bbox_inches="tight")
    print(f"Turnaround plot saved to {turnaround_path}")
    plt.close()
else:
    print("No turnaround data — skipping turnaround plot.")

print("\nDone.")
