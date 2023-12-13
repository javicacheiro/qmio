#!/bin/bash
#SBATCH -J compiled_circuit      # Job name
#SBATCH -o compiled_circuit.o%j      # Name of stdout output file(%j expands to jobId)
#SBATCH -e compiled_circuit.e%j      # Name of stderr output file(%j expands to jobId)
#SBATCH -p qpu        # partition
#SBATCH -N 1                # Number of nodes, not cores (24 cores/node)
#SBATCH -n 1                # Total number of MPI tasks (if omitted, n=N)
#SBATCH -c 1                # Cores per task
#SBATCH -t 00:10:00         # Run time (hh:mm:ss)

if [[ $# != 4 ]]; then
    echo $#
    echo "Usage: run.sh <compiled_circuit.p> <results.json> <execution_metrics.json> <num_shots>"
    exit 1
fi

# We have to modify the HOME of the user because it is not available in the lx7 control node
export HOME=/mnt/Q_SWAP/$USER

# If run from jupyter we must unset this options set by jupyter
unset MPLBACKEND

# Run the circuit
python3.8 /mnt/Q_SWAP/qmio/backends/qpu_felisa/run.py $*
