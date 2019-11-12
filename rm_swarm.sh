#!/bin/bash
######################################################################
# Author: Alexei Ledenev
# https://github.com/alexei-led/swarm-mac/blob/master/rm_swarm.sh
#####################################################################

# vars
[ -z "$NUM_WORKERS" ] && NUM_WORKERS=3

# remove nodes
# run NUM_WORKERS workers with SWARM_TOKEN
printf "Removing worker nodes ...\n"
for i in $(seq "${NUM_WORKERS}"); do
  docker --host "localhost:${i}2375" swarm leave 
  docker rm --force "worker-${i}" 
done
printf "\ndone, press key to continue ...\n"
#read -rn1

# remove swarm cluster master
printf "Removing master ...\n"
docker swarm leave --force 
printf "\ndone, press key to continue ...\n"
#read -rn1

# remove docker mirror
printf "Removing Docker registry mirror ...\n"
docker rm --force v2_mirror 
printf "\ndone, press key to continue ...\n"
#read -rn1

# remove swarm visuzalizer
printf "Removing Swarm Visualizer ...\n"
docker rm --force swarm_visualizer 
echo "done, press key to continue ..."

echo "Running system prune"
docker system prune --force
echo "done"
