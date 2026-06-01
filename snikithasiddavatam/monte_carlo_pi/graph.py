import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
RESULTS_CSV = "results.csv"   # output from aggregate.py
PI_REF = 3.14159265358979323846

df = pd.read_csv(RESULTS_CSV)
S  = df["N"].iloc[0]          # samples per job (N at j=1)
J_valid = len(df)

print(f"Loaded {J_valid} valid jobs, S={int(S)} samples per job")
print(f"Final pi estimate : {df['pi_est'].iloc[-1]:.10f}")
print(f"Final error : {df['error'].iloc[-1]:.2e}")

sns.set_theme(style="darkgrid", palette="muted", font_scale=1.1)
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle(
    f"Monte Carlo π Convergence  |  S={int(S):,} samples/job  |  J_valid={J_valid} jobs",
    fontsize=13, fontweight="bold", y=1.01
)

# plot 1: log-log convergence of absolute error vs total samples N
ax1 = axes[0]

# scatter points
ax1.scatter(df["N"], df["error"],
            color=sns.color_palette("muted")[0],
            s=25, alpha=0.7, zorder=3, label="Absolute error per job")

# 1/√N reference line scaled to first data point
N_ref   = np.logspace(np.log10(df["N"].min()), np.log10(df["N"].max()), 300)
scale   = df["error"].iloc[0] * np.sqrt(df["N"].iloc[0])
ref_line = scale / np.sqrt(N_ref)
ax1.plot(N_ref, ref_line,
         color="tomato", linewidth=1.8, linestyle="--",
         label=r"$1/\sqrt{N}$ reference")

ax1.set_xscale("log")
ax1.set_yscale("log")
ax1.set_xlabel("Total Samples N", fontsize=11)
ax1.set_ylabel(r"Absolute Error $|\hat{\pi} - \pi_{ref}|$", fontsize=11)
ax1.set_title("Convergence Plot", fontsize=11)
ax1.legend(fontsize=9)
ax1.annotate(f"J_valid = {J_valid}\nS = {int(S):,}",
             xy=(0.97, 0.97), xycoords="axes fraction",
             ha="right", va="top", fontsize=9,
             bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

# plot 2: pi estimate convergence
ax2 = axes[1]

ax2.plot(df["N"], df["pi_est"],
         color=sns.color_palette("muted")[1],
         linewidth=1.5, alpha=0.85, label=r"Cumulative $\hat{\pi}$")

ax2.axhline(y=PI_REF, color="tomato", linewidth=1.5,
            linestyle="--", label=f"π_ref = {PI_REF:.6f}...")

# shaded error band
ax2.fill_between(df["N"],
                 PI_REF - df["error"],
                 PI_REF + df["error"],
                 alpha=0.15, color=sns.color_palette("muted")[1])

ax2.set_xlabel("Total Samples N", fontsize=11)
ax2.set_ylabel(r"$\hat{\pi}$ Estimate", fontsize=11)
ax2.set_title(r"Cumulative $\hat{\pi}$ Estimate vs. Samples", fontsize=11)
ax2.legend(fontsize=9)
ax2.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax2.annotate(f"Final estimate:\n{df['pi_est'].iloc[-1]:.8f}",
             xy=(0.97, 0.05), xycoords="axes fraction",
             ha="right", va="bottom", fontsize=9,
             bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

plt.tight_layout()
output_path = "convergence_plot.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"\nPlot saved to {output_path}")
plt.show()