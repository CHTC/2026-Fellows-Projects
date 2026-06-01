import sys
import random

def main():
    # Argument Parsing
    if len(sys.argv) != 3:
        print("Usage: python mc_pi.py <S> <ProcID>", file=sys.stderr)
        sys.exit(1)

    try:
        S = int(sys.argv[1])       # Number of samples
        proc_id = int(sys.argv[2]) # Job number / HTCondor ProcID
    except ValueError as e:
        print(f"Error: Arguments must be integers. {e}", file=sys.stderr)
        sys.exit(1)

    if S <= 0:
        print("Error: S must be a positive integer.", file=sys.stderr)
        sys.exit(1)

    # Seeded RNG 
    # Using proc_id as seed ensures each job is independent and reproducible
    rng = random.Random(proc_id)

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

    # Write only if no errors 
    with open(output_filename, "w") as f:
        f.write(f"job_id={proc_id}\n")
        f.write(f"samples={S}\n")
        f.write(f"hits={M}\n")
        f.write(f"pi_estimate={pi_local}\n")

    print(f"Job {proc_id}: S={S}, M={M}, pi_local={pi_local:.8f} → wrote {output_filename}")

if __name__ == "__main__":
    main()
