import os


def get_run_folders(BASE_DIR = "mc_runs", with_results_csv = True):
    return sorted([
        d for d in os.listdir(BASE_DIR)
        if os.path.isdir(os.path.join(BASE_DIR, d)) and d.startswith("run_")
        and (not with_results_csv or os.path.isfile(os.path.join(BASE_DIR, d, "results.csv")))
    ])