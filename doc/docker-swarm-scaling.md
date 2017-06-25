# Scaling the Docker Swarm
While you can run NPS on a single computer, it is normally scaled across a cluster of machines that do the heavy lifting. Since NPS is built on Docker Swarm, scaling up is easy. You will generally need at least one _manager_ and multiple _worker_ nodes. If you installed NPS through the provided install script, your computer will be set up as both a worker and a manager. In larger installations it is generally preferable to use dedicated managers that do not act as worker nodes (see [Docker docs](https://docs.docker.com/engine/swarm/) for more details). Follow the steps laid out in this chapter to create a NPS cluster.

## Configuring a dedicated manager
Before you add additional worker nodes to your swarm, configure a single dedicated manager node. This node needs to be reachable from all worker nodes since it also manages the overlay network. Put this node into swarm mode with `docker swarm init` or by running the NPS installer. The node should now be the swarm leader, as seen below.

```
$ docker node ls
ID                           HOSTNAME  STATUS  AVAILABILITY  MANAGER STATUS
zhd2zbgu32tj98jho68kkzjmj *  moby      Ready   Active        Leader
```

Make note of the node id (`zhd2zbgu32tj98jho68kkzjmj ` in the example). To switch this node into dedicated manager mode, run `docker node update --availability drain <node_id>`. The node will now stop executing Docker services and only schedule their execution on worker nodes. As these changes only affect the swarm mode, you can still use `docker run` to launch containers on this node.

```
$ docker node update --availability drain zhd2zbgu32tj98jho68kkzjmj
zhd2zbgu32tj98jho68kkzjmj

$ docker node ls
ID                           HOSTNAME  STATUS  AVAILABILITY  MANAGER STATUS
zhd2zbgu32tj98jho68kkzjmj *  moby      Ready   Drain         Leader
```
## Adding manager nodes
A Docker swarm can run with a single manager node but will be unavailable if this node fails or disconnects from the network. It is therefore advised to have at least three manager nodes in the swarm so that a quorum can be maintained even if one of them fails. To add manager nodes, fetch the manager join token from your initial node.

```
$ docker swarm join-token manager
To add a manager to this swarm, run the following command:

    docker swarm join \
    --token SWMTKN-1-262vhcjqlvdddggq5c3ik92p4ifbl2b6ovqdk7dkv77m6m4wt2-b6etdi7rxpckxqortfugyfqgp \
    192.168.65.2:2377
```

Simply run the printed command on any Docker node that you want to set up as a manager node. The new nodes should now be visible as part of the cluster.

```
$ docker node ls
ID                           HOSTNAME STATUS  AVAILABILITY  MANAGER STATUS
zhd2zbgu32tj98jho68kkzjmj    moby     Ready   Active        Reachable
9f5np3pwjebrrovn7iw71hss4    rudy     Ready   Active        Reachable
dr5eigq9pfo9k3ksgls8rprau *  judy     Ready   Active        Leader
```

To configure the new nodes as dedicated managers, run `docker node update --availability drain <node_id>` for each of the node ids.

## Adding worker nodes
The actual processing of jobs as well as metadata indexing and all Docker services take place on the worker nodes. To add a worker node to the swarm, fetch the worker join token from a manager node.

```
$ docker swarm join-token worker        
To add a worker to this swarm, run the following command:

    docker swarm join \
    --token SWMTKN-1-262vhcjqlvdddggq5c3ik92p4ifbl2b6ovqdk7dkv77m6m4wt2-et7io1o2vv08hst771lk1272v \
    192.168.65.2:2377
```

Run the indicated command on every node that you want to add to the swarm and you are done.