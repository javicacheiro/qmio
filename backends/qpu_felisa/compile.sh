#!/bin/bash
#SBATCH -J compile      # Job name
#SBATCH -o compile.o%j      # Name of stdout output file(%j expands to jobId)
#SBATCH -e compile.e%j      # Name of stderr output file(%j expands to jobId)
#SBATCH -p hpc        # partition
#SBATCH -N 1                # Number of nodes, not cores (24 cores/node)
#SBATCH -n 1                # Total number of MPI tasks (if omitted, n=N)
#SBATCH -c 1                # Cores per task
#SBATCH -t 01:00:00         # Run time (hh:mm:ss)

if [[ $# != 3 ]]; then
    echo $#
    echo "Usage: compile.sh <circuit.qasm> <circuit.p> <num_shots>"
    exit 1
fi

module load qat

python3.8 /mnt/Q_SWAP/qmio/backends/qpu_felisa/compile.py $*

#SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
#python3.8 $SCRIPTDIR/compile.py $*
