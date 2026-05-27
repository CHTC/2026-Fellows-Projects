def parse_output_file(filepath):
    data = {}
    with open(filepath) as f:
        for line in f:
            key, val = line.strip().split("=")
            data[key] = val
    return {
        "job_id": int(data["job_id"]),
        "samples": int(data["samples"]),
        "hits": int(data["hits"]),
        "pi_estimate": float(data["pi_estimate"])
    }

result = parse_output_file("output_0.txt")
print(result)