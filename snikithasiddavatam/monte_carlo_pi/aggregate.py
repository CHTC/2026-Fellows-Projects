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

