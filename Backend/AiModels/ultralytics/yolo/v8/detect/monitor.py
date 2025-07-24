import subprocess
import sys
import time
import psutil

def get_most_available_cpu():
    """Returns the CPU core with the lowest utilization."""
    time.sleep(1)
    cpu_usage = psutil.cpu_percent(percpu=True)
    return cpu_usage.index(min(cpu_usage)) 

def run_script():
    """Runs predict.py with the provided command-line arguments using the most available CPU."""
    while True:
        cpu_core = get_most_available_cpu()
        print(f"Assigning process to CPU core {cpu_core}")

        command = ["taskset", "-c", str(cpu_core), "python3", "predict.py"] + sys.argv[1:]  
        print(f"Running: {' '.join(command)}")

        process = subprocess.run(command)

        print(f"Script failed with exit code {process.returncode}. Restarting...")
        time.sleep(2)

if __name__ == "__main__":
    run_script()