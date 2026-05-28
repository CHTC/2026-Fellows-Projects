#!/usr/bin/env python3
#script that takes all individual job output files and combines them into a single dataset for analysis
import os
import re
from datetime import datetime

OUTPUT_DIR = "."           # Where output_*.txt files are
LOG_FILE   = "logs/mc_pi.log"
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
                    key, val = line.strip().split("=")
                    data[key] = val
            job_id = int(data["job_id"])
            jobs[job_id] = {
                "job_id":      job_id,
                "samples":     int(data["samples"]),
                "hits":        int(data["hits"]),
                "pi_estimate": float(data["pi_estimate"])
            }
        except Exception as e:
            print(f"Skipping {filename}: {e}")

print(f"Found {len(jobs)} valid output files.")

# parse log files for "job terminated" timestamps
timestamps = {}
with open(LOG_FILE) as f:
    content = f.read()

# Each event block looks like:
# 005 (5203008.000.000) 05/27 13:54:49 Job terminated.
pattern = r"005 \(\d+\.(\d+)\.\d+\) (\d{2}/\d{2} \d{2}:\d{2}:\d{2}) Job terminated\."
for match in re.finditer(pattern, content):
    proc_id   = int(match.group(1))
    timestamp = datetime.strptime(f"2026/{match.group(2)}", "%Y/%m/%d %H:%M:%S")
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

