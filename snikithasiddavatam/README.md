## Understanding Throughput using a standardized workflow

### Objective
Profile the error of Monte Carlo numerical integration as an estimator of π as a function of the total number of samples N. By submitting J independent jobs, each producing a fixed number of samples, and accumulating results in chronological order of job completion, we can observe how the absolute estimation error decreases as N grows.

### Background
The Monte Carlo method estimates π by exploiting the ratio of the area of a unit circle to its enclosing unit square. For a point (x, y) drawn uniformly from [0,1) × [0,1), the point falls inside the quarter-circle if: x² + y² < 1

The fraction of points satisfying this condition converges to π/4 as the number of samples grows. Multiplying by 4 gives the estimate of π. The expected error decreases proportionally to 1/N (the standard Monte Carlo convergence rate).
