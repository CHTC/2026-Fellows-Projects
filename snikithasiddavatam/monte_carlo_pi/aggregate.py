# script that takes all individual job output files and combines them into a single dataset for analysis.
import os
import csv
import htcondor2 as htcondor
from datetime import datetime

from utils import get_run_folders

# Configuration
BASE_DIR = "mc_runs_1000"  # Directory containing run_XXXXXXX folders
PI_REF   = 3.14159265358979323846

# auto-detect all run_* folders 
run_folders = get_run_folders(BASE_DIR, with_results_csv=False)

if not run_folders:
    print("Error: No run_* folders found in current directory.")
    raise SystemExit(1)

print(f"Found {len(run_folders)} run folder(s): {run_folders}")

# process each run folder 
for run_folder in run_folders:
    cluster_id = run_folder[len("run_"):]
    run_path   = os.path.join(BASE_DIR, run_folder)
    logs_dir   = os.path.join(run_path, "logs")        # run_XXXXXXX/logs/
    log_file   = os.path.join(logs_dir, "logs", "mc_pi.log")  # run_XXXXXXX/logs/logs/mc_pi.log
    output_csv = os.path.join(run_path, "results.csv")

    print(f"\n--- Processing {run_folder} ---")

    # Check log file exists
    if not os.path.isfile(log_file):
        print(f"  Warning: Log file not found at {log_file} — skipping.")
        continue

    # --- Parse all output files from run_XXXXXXX/logs/ ---
    jobs = {}
    for filename in os.listdir(logs_dir):
        if filename.startswith("output_") and filename.endswith(".txt"):
            filepath   = os.path.join(logs_dir, filename)
            job_number = filename[len("output_"):-len(".txt")]
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
                    print(f"  Skipping {filename}: missing keys {missing}")
                    continue
                job_id = int(data["job_id"])
                jobs[job_id] = {
                    "job_id":      job_id,
                    "samples":     int(data["samples"]),
                    "hits":        int(data["hits"]),
                    "pi_estimate": float(data["pi_estimate"])
                }
            except OSError:
                print(f"  Skipping job {job_number}: Could not open file {filename}")
            except KeyError as e:
                print(f"  Skipping job {job_number}: Missing key {e} in {filename}")
            except ValueError as e:
                print(f"  Skipping job {job_number}: Bad value in {filename}: {e}")

    print(f"  Found {len(jobs)} valid output files.")

    if not jobs:
        print(f"  No valid jobs found — skipping.")
        continue

    #parse log file for submit and "Job terminated" timestamps using htcondor2 ---
    timestamps = {}
    submit_times = {}
    print(f"  Parsing HTCondor log file: {log_file}")
    try:
        jel = htcondor.JobEventLog(log_file)
        for event in jel.events(stop_after=0):
            if event.type == htcondor.JobEventType.SUBMIT:
                submit_times[event.proc] = datetime.fromtimestamp(event.timestamp)
            elif event.type == htcondor.JobEventType.JOB_TERMINATED:
                timestamps[event.proc] = datetime.fromtimestamp(event.timestamp)
    except Exception as e:
        print(f"  Warning: Could not parse log file with htcondor2: {e} — skipping.")
        continue

    cluster_submit_time = min(submit_times.values()) if submit_times else None
    print(f"  Cluster submit time: {cluster_submit_time}")

    print(f"  Found {len(timestamps)} 'Job terminated' entries in log.")

    #keep only valid jobs (output file AND log entry) ---
    valid_jobs = []
    for job_id, job_data in jobs.items():
        if job_id in timestamps:
            job_data["timestamp"] = timestamps[job_id]
            job_data["submit_time"] = submit_times.get(job_id)
            if cluster_submit_time is not None:
                job_data["turnaround_s"] = (timestamps[job_id] - cluster_submit_time).total_seconds()
            else:
                job_data["turnaround_s"] = None
            valid_jobs.append(job_data)
        else:
            print(f"  Warning: Job {job_id} has output file but no log entry — skipping.")

    print(f"  Valid jobs (both file + log entry): {len(valid_jobs)}")

    if not valid_jobs:
        print(f"  No valid jobs after cross-checking — skipping.")
        continue

    #sort by timestamp 
    valid_jobs.sort(key=lambda x: x["timestamp"])

    #compute cumulative pi estimate and error 
    # j         - cumulative job index (1-based, ordered by termination time)
    # job_id    - HTCondor process ID for the job
    # timestamp - datetime when the job terminated (from the HTCondor log)
    # N         - total samples accumulated across all jobs up to and including this one
    # pi_est    - running Monte Carlo estimate of pi (4 * cumulative_hits / N)
    # error     - absolute error |pi_est - pi|
    S       = valid_jobs[0]["samples"]
    M_total = 0
    results = []

    for j, job in enumerate(valid_jobs, start=1):
        M_total += job["hits"]
        S_total  = j * S
        pi_est   = 4.0 * M_total / S_total
        error    = abs(pi_est - PI_REF)
        results.append({
            "j":            j,
            "job_id":       job["job_id"],
            "submit_time":  job.get("submit_time"),
            "timestamp":    job["timestamp"],
            "turnaround_s": job.get("turnaround_s"),
            "N":            S_total,
            "pi_est":       pi_est,
            "error":        error
        })

    # save to CSV inside run folder 
    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["j","job_id","submit_time","timestamp","turnaround_s","N","pi_est","error"])
        writer.writeheader()
        writer.writerows(results)

    print(f"  Saved {len(results)} rows to {output_csv}")
    print(f"  Final pi estimate : {results[-1]['pi_est']:.10f}")
    print(f"  Final error       : {results[-1]['error']:.2e}")

print("\nall runs processed.")