#!/bin/bash

######################################################################
# Author: Alexei Ledenev
# https://github.com/alexei-led/swarm-mac/blob/master/init_swarm.sh
#####################################################################
set -e

# vars
[ -z "$NUM_WORKERS" ] && NUM_WORKERS=3

# init swarm (need for service command); if not created
echo "Creating Docker Swarm master ..."
echo "$(tput setaf 3) docker swarm init $(tput sgr 0)"
docker swarm init
printf "\ndone, press key to continue ...\n"
#read -rn1

# get join token
echo "Get Swarm token"
echo "$(tput setaf 3) docker swarm join-token -q worker $(tput sgr 0)"
SWARM_TOKEN=$(docker swarm join-token -q worker)
echo "SWARM_TOKEN=${SWARM_TOKEN}"
printf "\ndone, press key to continue ...\n"
#read -rn1

# get Swarm master IP (Docker for Mac xhyve VM IP)
echo "Get Swarm master IP"
echo "$(tput setaf 3) docker info --format \"{{.Swarm.NodeAddr}}\") $(tput sgr 0)"
SWARM_MASTER=$(docker info --format "{{.Swarm.NodeAddr}}")
echo "Swarm master IP: ${SWARM_MASTER}"
echo "SWARM_MASTER=${SWARM_MASTER}"
printf "\ndone, press key to continue ...\n"
#read -rn1

# start Docker registry mirror
echo "Starting local Docker Registry mirror ..."
echo "$(tput setaf 3) docker run -d --restart=always -p 4000:5000 --name v2_mirror \
  -v $PWD/rdata:/var/lib/registry \
  -e REGISTRY_PROXY_REMOTEURL=https://registry-1.docker.io \
  registry:2.5 $(tput sgr 0)"
docker run -d --restart=always -p 4000:5000 --name v2_mirror \
  -v "$PWD"/rdata:/var/lib/registry \
  -e REGISTRY_PROXY_REMOTEURL=https://registry-1.docker.io \
  registry:2.5
printf "\ndone, press key to continue ...\n"
#read -rn1

# run NUM_WORKERS workers with SWARM_TOKEN
for i in $(seq "${NUM_WORKERS}"); do
  # run new worker container
  echo "Starting Docker swarm worker #${i} ..."
  echo "$(tput setaf 3) docker run -d --privileged --name worker-${i} --hostname=worker-${i} \
    -p ${i}2375:2375 \
    -p ${i}5000:5000 \
    -p ${i}5001:5001 \
    -p ${i}5601:5601 \
    docker:17.03.0-ce-dind \
      --storage-driver=bridge \
      --registry-mirror http://${SWARM_MASTER}:4000
  $(tput sgr 0)"
  docker run -d --privileged --name "worker-${i}" --hostname="worker-${i}" \
    -p ${i}2375:2375 \
    -p ${i}5000:5000 \
    -p ${i}5001:5001 \
    -p ${i}5601:5601 \
    docker:17.03.0-ce-dind \
      --storage-driver=overlay2 \
      --registry-mirror "http://${SWARM_MASTER}:4000"
  printf "\ndone, press key to continue ...\n"
  #read -rn1
  # add worker container to the cluster
  printf "\nJoin swarm worker #%s to swarm\n" "${i}"
  echo "$(tput setaf 3) docker --host=localhost:${i}2375 swarm join --token ${SWARM_TOKEN} ${SWARM_MASTER}:2377 $(tput sgr 0)"
  docker --host="localhost:${i}2375" swarm join --token "${SWARM_TOKEN}" "${SWARM_MASTER}:2377"
  printf "\ndone, press key to continue ...\n"
  #read -rn1
done

# show swarm cluster
printf "\nLocal Swarm Cluster\n===================\n"
echo "$(tput setaf 3) docker node ls $(tput sgr 0)"
docker node ls

printf "\npress key to continue ...\n"
#read -rn1

# echo swarm visualizer
printf "\nLocal Swarm Visualizer\n===================\n"
echo "$(tput setaf 3) docker run -it -d --name swarm_visualizer \
  -p 8080:8080 -e HOST=localhost \
  -v /var/run/docker.sock:/var/run/docker.sock \
  manomarks/visualizer
$(tput sgr 0)"
docker run -it -d --name swarm_visualizer \
  -p 8080:8080 -e HOST=localhost \
  -v /var/run/docker.sock:/var/run/docker.sock \
  dockersamples/visualizer

printf "\npress key to continue ...\n"
#read -rn1

# open Visualizer
#open "http://localhost:8080"
