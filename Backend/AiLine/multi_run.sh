#!/bin/bash

if [ $# -lt 1 ]; then
    echo "Usage: $0 <num_cpus> [num_gpus]"
    exit 1
fi

NUM_CPUS=$1
NUM_GPUS=${2:-1}
echo "Using $NUM_CPUS CPUs and $NUM_GPUS GPUs."
PIDS=()

# Function to clean up on exit
cleanup() {
    echo "Stopping all processes..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null
    done
    wait
    echo "All processes stopped."
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup SIGINT

# Start processes
for (( i=0; i<NUM_CPUS; i++ )); do
    GPU=$((i % NUM_GPUS)) # Alternate between GPU 0 and GPU 1
    CUDA_VISIBLE_DEVICES=$GPU python3 predict.py \
        --line="[330,0,330,710]" &

    PIDS+=($!) # Store process ID
done

echo "Running... Press Ctrl+C to stop."

# Keep script running
wait