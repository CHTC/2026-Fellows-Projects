import os
import math
import csv
import pandas as pd
from utils import get_run_folders

BASE_DIRS = [
    ("mc_runs_10",     10),
    ("mc_runs_100",    100),
    ("mc_runs_1000",   1000),
    ("mc_runs_10000",  10000),
    ("mc_runs_100000", 100000),
]

PERCENTILES = list(range(10, 110, 10))  # 10, 20, ..., 100

rows = []

for base_dir, num_jobs in BASE_DIRS:
    run_folders = get_run_folders(base_dir, with_results_csv=True)
    if not run_folders:
        print(f"No results.csv found in {base_dir} — skipping.")
        continue

    for run_folder in run_folders:
        cluster_id = run_folder[len("run_"):]
        csv_path = os.path.join(base_dir, run_folder, "results.csv")

        df = pd.read_csv(csv_path, parse_dates=["timestamp"])
        t0 = df["timestamp"].iloc[0]
        df["runtime_s"] = (df["timestamp"] - t0).dt.total_seconds()

        total = len(df)
        row = {"num_jobs": num_jobs, "run_id": cluster_id}

        for pct in PERCENTILES:
            target_j = math.ceil(total * pct / 100)
            target_j = min(target_j, total)
            # find the row where j == target_j (j is 1-based)
            match = df[df["j"] == target_j]
            row[f"pct_{pct}"] = match["runtime_s"].iloc[0] if not match.empty else None

        rows.append(row)
        print(f"  {base_dir}/{run_folder}: {total} jobs processed")

output_path = "milestone_times.csv"
fieldnames = ["num_jobs", "run_id"] + [f"pct_{p}" for p in PERCENTILES]

with open(output_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nSaved {len(rows)} rows to {output_path}")
