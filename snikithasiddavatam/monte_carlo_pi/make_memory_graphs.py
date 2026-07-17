import os
import re
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

MEM_DIR   = "memory"
GRAPH_DIR = "graphs/memory"
PI_REF    = 3.14159265358979323846

os.makedirs(GRAPH_DIR, exist_ok=True)

def tier_to_mb(tier_label):
    """'500MB' -> 500, '4GB' -> 4096"""
    m = re.fullmatch(r"(\d+)(MB|GB)", tier_label)
    if not m:
        return None
    val, unit = int(m.group(1)), m.group(2)
    return val * 1024 if unit == "GB" else val

tier_dirs = {}
for d in sorted(os.listdir(MEM_DIR)):
    m = re.fullmatch(r"mc_runs_\d+_mem_(.+)", d)
    if m and os.path.isdir(os.path.join(MEM_DIR, d)):
        label = m.group(1)
        mb = tier_to_mb(label)
        if mb is None:
            print(f"  Skipping {d}: cannot parse memory label {label}")
            continue
        tier_dirs[label] = {"dir": os.path.join(MEM_DIR, d), "mb": mb}

if not tier_dirs:
    print(f"Error: no mc_runs_*_mem_* folders found in {MEM_DIR}/")
    sys.exit(1)

# sort tiers by memory size
tier_order = sorted(tier_dirs, key=lambda t: tier_dirs[t]["mb"])
print(f"Found {len(tier_order)} memory tiers: {', '.join(tier_order)}")

# aggregate each run into results.csv 

for tier in tier_order:
    base_dir = tier_dirs[tier]["dir"]
    for run_folder in get_run_folders(base_dir, with_results_csv=False):
        run_path   = os.path.join(base_dir, run_folder)
        logs_dir   = os.path.join(run_path, "logs")
        log_file   = os.path.join(logs_dir, "logs", "mc_pi.log")
        output_csv = os.path.join(run_path, "results.csv")

        if os.path.isfile(output_csv):
            print(f"  {tier}/{run_folder}: results.csv already exists — skipping aggregate.")
            continue

        print(f"\n--- Aggregating {tier}/{run_folder} ---")

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

        submit_times  = {}
        execute_times = {}
        term_times    = {}
        mem_usage     = {}
        try:
            jel = htcondor.JobEventLog(log_file)
            for event in jel.events(stop_after=0):
                if event.type == htcondor.JobEventType.SUBMIT:
                    submit_times[event.proc] = datetime.fromtimestamp(event.timestamp)
                elif event.type == htcondor.JobEventType.EXECUTE:
                    # keep the first execute per proc (restarts would overwrite)
                    execute_times.setdefault(event.proc, datetime.fromtimestamp(event.timestamp))
                elif event.type == htcondor.JobEventType.JOB_TERMINATED:
                    term_times[event.proc] = datetime.fromtimestamp(event.timestamp)
                    mem_usage[event.proc]  = event.get("MemoryUsage")
        except Exception as e:
            print(f"  Warning: Could not parse log file: {e} — skipping.")
            continue

        cluster_submit_time = min(submit_times.values()) if submit_times else None
        print(f"  Cluster submit time: {cluster_submit_time}")
        print(f"  Found {len(term_times)} termination entries.")

        valid_jobs = []
        for job_id, job_data in jobs.items():
            if job_id in term_times:
                job_data["timestamp"]    = term_times[job_id]
                job_data["submit_time"]  = submit_times.get(job_id)
                job_data["execute_time"] = execute_times.get(job_id)
                job_data["memory_usage_mb"] = mem_usage.get(job_id)
                job_data["turnaround_s"] = (
                    (term_times[job_id] - cluster_submit_time).total_seconds()
                    if cluster_submit_time else None
                )
                job_data["queue_wait_s"] = (
                    (execute_times[job_id] - cluster_submit_time).total_seconds()
                    if cluster_submit_time and job_id in execute_times else None
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
                "j":               j,
                "job_id":          job["job_id"],
                "submit_time":     job.get("submit_time"),
                "execute_time":    job.get("execute_time"),
                "timestamp":       job["timestamp"],
                "queue_wait_s":    job.get("queue_wait_s"),
                "turnaround_s":    job.get("turnaround_s"),
                "memory_usage_mb": job.get("memory_usage_mb"),
                "N":               S_total,
                "pi_est":          pi_est,
                "error":           abs(pi_est - PI_REF),
            })

        with open(output_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "j","job_id","submit_time","execute_time","timestamp",
                "queue_wait_s","turnaround_s","memory_usage_mb","N","pi_est","error"
            ])
            writer.writeheader()
            writer.writerows(results)

        print(f"  Saved {len(results)} rows → {output_csv}")

#  Load all results 

all_runs = {}   # (tier, cluster_id) -> df
for tier in tier_order:
    base_dir = tier_dirs[tier]["dir"]
    for run_folder in get_run_folders(base_dir, with_results_csv=True):
        cluster_id = run_folder[len("run_"):]
        df = pd.read_csv(os.path.join(base_dir, run_folder, "results.csv"),
                         parse_dates=["timestamp"])
        all_runs[(tier, cluster_id)] = df
        print(f"  Loaded {tier}/{run_folder}: {len(df)} jobs, "
              f"all jobs finished in {df['turnaround_s'].max():.0f}s")

if not all_runs:
    print("Error: No results.csv found after aggregation.")
    sys.exit(1)

# color per tier: sequential (viridis) since tiers are ordered by size
sns.set_theme(style="darkgrid", font_scale=1.1)
tier_colors = dict(zip(tier_order, sns.color_palette("viridis", n_colors=len(tier_order))))

# cumulative jobs vs. time since submit 

fig, ax = plt.subplots(figsize=(11, 6.5))
fig.suptitle("Job Completion Throughput by Memory Request",
             fontsize=13, fontweight="bold")
seen = set()
for (tier, cluster_id), df in all_runs.items():
    label = tier if tier not in seen else None
    seen.add(tier)
    ax.plot(df["turnaround_s"], df["j"], color=tier_colors[tier],
            linewidth=1.8, alpha=0.85, label=label)
ax.set_xlabel("Time Since Cluster Submit (s)", fontsize=11)
ax.set_ylabel("Cumulative Jobs Completed", fontsize=11)
ax.set_title("10,000 jobs per run, 3 runs per memory request", fontsize=11)
handles, labels = ax.get_legend_handles_labels()
order = [labels.index(t) for t in tier_order if t in labels]
ax.legend([handles[i] for i in order], [labels[i] for i in order],
          title="request_memory", fontsize=9, loc="upper left",
          bbox_to_anchor=(1.01, 1), borderaxespad=0)
plt.tight_layout()
path = os.path.join(GRAPH_DIR, "memory_cumulative_jobs.png")
plt.savefig(path, dpi=150, bbox_inches="tight")
print(f"\nCumulative jobs plot saved to {path}")
plt.close()

# turnaround & queue-wait distributions per tier 

rows = []
for (tier, cluster_id), df in all_runs.items():
    sub = df[["turnaround_s", "queue_wait_s"]].copy()
    sub["tier"] = tier
    sub["run"] = cluster_id
    rows.append(sub)
dist_df = pd.concat(rows, ignore_index=True)
dist_df["tier"] = pd.Categorical(dist_df["tier"], categories=tier_order, ordered=True)

fig, axes = plt.subplots(1, 2, figsize=(15, 6), sharey=False)
fig.suptitle("Per-Job Latency by Memory Request (all runs combined)",
             fontsize=13, fontweight="bold", y=1.01)

sns.boxplot(data=dist_df, x="tier", y="turnaround_s", hue="tier",
            palette=tier_colors, legend=False, ax=axes[0],
            showfliers=False, order=tier_order)
axes[0].set_xlabel("request_memory", fontsize=11)
axes[0].set_ylabel("Turnaround Time (s)", fontsize=11)
axes[0].set_title("Submit → Termination", fontsize=11)

sns.boxplot(data=dist_df, x="tier", y="queue_wait_s", hue="tier",
            palette=tier_colors, legend=False, ax=axes[1],
            showfliers=False, order=tier_order)
axes[1].set_xlabel("request_memory", fontsize=11)
axes[1].set_ylabel("Queue Wait Time (s)", fontsize=11)
axes[1].set_title("Submit → First Execution", fontsize=11)

plt.tight_layout()
path = os.path.join(GRAPH_DIR, "memory_latency_box.png")
plt.savefig(path, dpi=150, bbox_inches="tight")
print(f"Latency boxplots saved to {path}")
plt.close()

#  total completion time vs. requested memory 

mk_rows = []
for (tier, cluster_id), df in all_runs.items():
    mk_rows.append({
        "tier":         tier,
        "mb":           tier_dirs[tier]["mb"],
        "run":          cluster_id,
        "total_time_s": df["turnaround_s"].max(),
        "median_turnaround_s": df["turnaround_s"].median(),
    })
mk_df = pd.DataFrame(mk_rows).sort_values("mb")

fig, ax = plt.subplots(figsize=(10, 6))
fig.suptitle("Total Completion Time vs. Requested Memory",
             fontsize=13, fontweight="bold")
for tier in tier_order:
    sub = mk_df[mk_df["tier"] == tier]
    ax.scatter(sub["mb"], sub["total_time_s"], color=tier_colors[tier],
               s=70, alpha=0.85, zorder=3, label=tier)
med = mk_df.groupby("mb")["total_time_s"].median()
ax.plot(med.index, med.values, color="gray", linewidth=1.5, linestyle="--",
        zorder=2, label="median")
ax.set_xscale("log", base=2)
ax.set_xticks(mk_df["mb"].unique())
ax.set_xticklabels(tier_order, rotation=0)
ax.set_xlabel("request_memory", fontsize=11)
ax.set_ylabel("Time for All 10,000 Jobs to Finish (s)", fontsize=11)
ax.set_title("One point per run (3 runs per memory request)", fontsize=11)
ax.legend(fontsize=9, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
plt.tight_layout()
path = os.path.join(GRAPH_DIR, "memory_total_completion.png")
plt.savefig(path, dpi=150, bbox_inches="tight")
print(f"Total completion time plot saved to {path}")
plt.close()

# summary table 

summary = (
    dist_df.groupby("tier", observed=True)
    .agg(median_turnaround_s=("turnaround_s", "median"),
         p90_turnaround_s=("turnaround_s", lambda s: s.quantile(0.9)),
         median_queue_wait_s=("queue_wait_s", "median"))
    .join(mk_df.groupby("tier")["total_time_s"].median().rename("median_total_time_s"))
)
summary_path = os.path.join(GRAPH_DIR, "memory_summary.csv")
summary.to_csv(summary_path)
print(f"\nSummary saved to {summary_path}")
print(summary.round(1).to_string())

print("\nDone.")
