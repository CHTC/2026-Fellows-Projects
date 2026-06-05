import hashlib
import sys
import random

def main():
    # Argument Parsing
    if len(sys.argv) != 4:
        print("Usage: python mc_pi.py <S> <ProcID> <ClusterID>", file=sys.stderr)
        sys.exit(1)

    try:
        S = int(sys.argv[1])       # Number of samples
        proc_id = int(sys.argv[2]) # Job number / HTCondor ProcID
        cluster_id = int(sys.argv[3]) # Cluster number / HTCondor ClusterID
    except ValueError as e:
        print(f"Error: Arguments must be integers. {e}", file=sys.stderr)
        sys.exit(1)

    if S <= 0:
        print("Error: S must be a positive integer.", file=sys.stderr)
        sys.exit(1)

    if proc_id < 0 or cluster_id < 0:
        print("Error: proc_id and cluster_id must be non-negative integers.", file=sys.stderr)
        sys.exit(1)

    # combines ClusterID and ProcID into a single unique string,
    # hashes it with MD5, converts to integer, and maps to 32-bit range.
    # guarantees: no two (ClusterID, ProcID) pairs produce the same seed.
    hash_input = f"{cluster_id}_{proc_id}"
    seed = int(hashlib.md5(hash_input.encode()).hexdigest(), 16) % (2**32)

    rng = random.Random(seed)

    # Monte Carlo Sampling 
    M = 0  # Count of points inside the quarter-circle
    for _ in range(S):
        x = rng.random()   # Uniform in [0, 1)
        y = rng.random()   # Uniform in [0, 1)
        if x*x + y*y < 1.0:
            M += 1

    # Local π Estimate 
    pi_local = 4.0 * M / S

    # Write Output File 
    # Filename is unique per job using proc_id
    output_filename = f"output_{proc_id}.txt"
    with open(output_filename, "w") as f:
        f.write(f"job_id={proc_id}\n")
        f.write(f"cluster_id={cluster_id}\n")
        f.write(f"seed={seed}\n")
        f.write(f"samples={S}\n")
        f.write(f"hits={M}\n")
        f.write(f"pi_estimate={pi_local}\n")

    print(f"Job {proc_id}: cluster={cluster_id}, seed={seed}, S={S}, M={M}, pi_local={pi_local:.8f} → wrote {output_filename}")

if __name__ == "__main__":
    main()
