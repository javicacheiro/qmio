#!/bin/bash
#SBATCH -J qulacs_circuit      # Job name
#SBATCH -o qulacs_circuit.o%j      # Name of stdout output file(%j expands to jobId)
#SBATCH -e qulacs_circuit.e%j      # Name of stderr output file(%j expands to jobId)
#SBATCH -p qs        # partition
#SBATCH -N 1                # Number of nodes, not cores (48 cores/node)
#SBATCH -n 48                # Total number of MPI tasks (if omitted, n=N)
#SBATCH -c 1                # Cores per task
#SBATCH -t 00:10:00         # Run time (hh:mm:ss)

if [[ $# != 4 ]]; then
    echo $#
    echo "Usage: run.sh <qulacs_circuit.p> <results.json> <execution_metrics.json> <num_shots>"
    exit 1
fi

# Load qulacs module
module load qulacs-hpcx

# Run the circuit
python3.8 /mnt/Q_SWAP/qmio/backends/simulator_qulacs/run.py $*
