## System Architecture

1. Cluster: CoreOS Fleet
2. Swarm: Docker Swarm
3. Node: Docker host

A group of nodes forms a fleet, this may be bare metal devices or virtual machines. They boot CoreOS and load our globally shared `cloud-init`, which configures them to join the fleet. The rest of the configuration happens through Fleet. Note that we use capitalized Fleet for the software and lowercase fleet for the set of machines.

Within the fleet we create two swarms, one for continously running `services` and a second one for the image processing `jobs`. New machines will automatically join the jobs swarm until and must manually be added to the `services` swarm. Services are automatically scheduled by the Docker schedulder in the services swarm. Jobs use a FIFO queue build on Redis.