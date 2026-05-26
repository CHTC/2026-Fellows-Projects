## Understanding Throughput using a standardized workflow

This experiment uses Monte Carlo numerical integration to estimate π and profiles how the estimation error decreases as the total number of samples grows.

How it works: Random points (x, y) are drawn uniformly from [0,1)×[0,1). A point is "inside" if x² + y² < 1. The fraction of inside points converges to π/4, so multiplying by 4 gives an estimate of π.
Structure: J independent jobs are submitted, each generating S random samples and writing results to an output file. Jobs are sorted by completion time, and a running cumulative π estimate is computed across jobs in that order. The absolute error ε = |π_estimated − π_ref| is tracked against total samples N = j × S.

Expected behaviour: Error decreases at roughly 1/√N, consistent with standard Monte Carlo convergence. Deviations may indicate seed collisions, RNG quality issues, or outlier jobs.
Output: A log-log plot of absolute error vs. total samples, overlaid with a 1/√N reference curve, annotated with the number of valid jobs and samples per job.
