#!/usr/bin/env sh
#SBATCH -p ilk
#SBATCH --time=00:03:00
#SBATCH --mem=900G
#SBATCH -J Tunel
#SBATCH -o /dev/null
#SBATCH -e /dev/null

#############################################################
#   Bash script to spawn the tunner in by the Frontal node  #
#                                                           #
#   Arguments: Randomly generated ENDPONT_PORT.             #
#   Needs the posibility to execute iptables_create.exe     #
#############################################################

ENDPOINT_PORT=${1}

# Adds the route to the ZMQ_SERVER dev before iptables command
export ZMQ_SERVER="tcp://10.133.29.226:5556"

# Creates the tunnel tunnel
/opt/cesga/utils/qmio/iptables_create/iptables_create.exe $ENDPOINT_PORT

# Adjust sleep with timelimit
TIME_LIMIT=$(squeue -j $SLURM_JOB_ID -h --Format TimeLimit)
TIME_LIMIT_SECONDS=$(echo "${TIME_LIMIT}" | awk -F: '{ print ($1 * 3600) + ($2 * 60) + $3 }')

# Wait till time limit or execution ending
sleep ${TIME_LIMIT_SECONDS}s
