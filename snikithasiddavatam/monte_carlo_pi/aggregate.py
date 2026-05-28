#!/usr/bin/env python3
#script that takes all individual job output files and combines them into a single dataset for analysis
import os
import re
from datetime import datetime

OUTPUT_DIR = "logs"        # Where output_*.txt files are
LOG_FILE   = "logs/logs/mc_pi.log"
PI_REF     = 3.14159265358979323846

# parse all output files    
jobs = {}
for filename in os.listdir(OUTPUT_DIR):
    if filename.startswith("output_") and filename.endswith(".txt"):
        filepath = os.path.join(OUTPUT_DIR, filename)
        try:
            data = {}
            with open(filepath) as f:
                for line in f:
                    if "=" not in line:
                        continue
                    key, val = line.strip().split("=", 1)
                    data[key] = val
            required_keys = ("job_id", "samples", "hits", "pi_estimate")
            missing = [k for k in required_keys if k not in data]
            if missing:
                print(f"Skipping {filename}: missing keys {missing}")
                continue
            job_id = int(data["job_id"])
            jobs[job_id] = {
                "job_id":      job_id,
                "samples":     int(data["samples"]),
                "hits":        int(data["hits"]),
                "pi_estimate": float(data["pi_estimate"])
            }
        except (OSError, ValueError) as e:
            print(f"Skipping {filename}: {e}")

print(f"Found {len(jobs)} valid output files.")

# parse log files for "job terminated" timestamps
timestamps = {}
with open(LOG_FILE) as f:
    content = f.read()

# Each event block looks like:
# 005 (5203008.000.000) 05/27 13:54:49 Job terminated.
pattern = r"005 \(\d+\.(\d+)\.\d+\) (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) Job terminated\."
for match in re.finditer(pattern, content):
    proc_id   = int(match.group(1))
    timestamp = datetime.strptime(match.group(2), "%Y-%m-%d %H:%M:%S")
    timestamps[proc_id] = timestamp

#Keep only valid jobs (output file and log entry) 
valid_jobs = []
for job_id, job_data in jobs.items():
    if job_id in timestamps:
        job_data["timestamp"] = timestamps[job_id]
        valid_jobs.append(job_data)
    else:
        print(f"Warning: Job {job_id} has output file but no log entry — skipping.")

print(f"Valid jobs (both file + log entry): {len(valid_jobs)}")

# Sort by timestamp
valid_jobs.sort(key=lambda x: x["timestamp"])

S = valid_jobs[0]["samples"]
M_total = 0
results = []

for j, job in enumerate(valid_jobs, start=1):
    M_total += job["hits"]
    S_total  = j * S
    pi_est   = 4.0 * M_total / S_total
    error    = abs(pi_est - PI_REF)
    results.append({
        "j": j,
        "job_id": job["job_id"],
        "timestamp": job["timestamp"],
        "N": S_total,
        "pi_est": pi_est,
        "error": error
    })

# saving to csv
import csv
with open("results.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["j","job_id","timestamp","N","pi_est","error"])
    writer.writeheader()
    writer.writerows(results)

print(f"Saved {len(results)} rows to results.csv")
print(f"Final pi estimate: {results[-1]['pi_est']:.10f}")
print(f"Final error: {results[-1]['error']:.2e}")

