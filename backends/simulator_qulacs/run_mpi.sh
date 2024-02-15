#!/bin/bash
#SBATCH -J qulacs_circuit      # Job name
#SBATCH -o qulacs_circuit.o%j      # Name of stdout output file(%j expands to jobId)
#SBATCH -e qulacs_circuit.e%j      # Name of stderr output file(%j expands to jobId)
#SBATCH -p qs        # partition
#SBATCH -N 1                # Number of nodes, not cores (48 cores/node)
#SBATCH -n 48                # Total number of MPI tasks (if omitted, n=N)
#SBATCH -c 1                # Cores per task
#SBATCH -t 00:10:00         # Run time (hh:mm:ss)

#set -x

if [[ $# != 4 ]]; then
    echo $#
    echo "Usage: run.sh <qulacs_circuit.p> <results.json> <execution_metrics.json> <num_shots>"
    exit 1
fi

calcular_potencia() {
    local nodos=$SLURM_NNODES
    local resultado=$((nodos * 48))
    local potencia=1

    while [ $((potencia * 2)) -le $resultado ]; do
        potencia=$((potencia * 2))
    done
    export SIZE=$potencia
}
# Función para sacar de manera automática el número de tareas.
calcular_potencia
# Load qulacs module
module load qulacs-hpcx
# Run the circuit

OMP_NUM_THREADS=12
QULACS_NUM_THREADS=12

mpirun -npernode 4 numactl -N 0-3 -m 0-3 python3.8 /home/cesga/acaride/Trainning_Qulacs/run.py $*
