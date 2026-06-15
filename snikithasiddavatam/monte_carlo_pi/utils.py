import os

def get_run_folders(BASE_DIR = "mc_runs", with_results_csv = True):
    """
    Get the list of run folders in the BASE_DIR. If with_results_csv is True, only return those folders that contain a results.csv file.
    """
    return sorted([
        d for d in os.listdir(BASE_DIR)
        if os.path.isdir(os.path.join(BASE_DIR, d)) and d.startswith("run_")
        and (not with_results_csv or os.path.isfile(os.path.join(BASE_DIR, d, "results.csv")))
    ])