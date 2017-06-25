# NPS Docker Services
NPS requires some tools like databases and DICOM servers to run at all times. These tools run as docker services on a swarm. Services are based on SwarmKit, so at least version 1.12 of docker is needed.

## Running a service

### Elasticsearch
Setting up an Elasticsearch cluster is pretty straightforward. Since the nodes of the cluster need to communicate with each other, they all join an overlay network called `elasticsearch_master`. Dockers built-in load-balancing will usually prohibit the nodes from forming a cluster because they all share a single IP address. This is mitigated by using DNS round-robin (DNS RR) instead of the load balancer (`--endpoint-mode dnsrr`). 

    docker service create \
    	--name elasticsearch-master \
    	--network internal \
    	--endpoint-mode dnsrr \
    	--user elasticsearch \
    	--replicas 3 \
    	--mount type=bind,source=/nps/applications/elasticsearch-master/config,target=/usr/share/elasticsearch/config \
    	--mount type=bind,source=/nps/applications/elasticsearch-master/data,target=/usr/share/elasticsearch/data \
    	elasticsearch:5

Elasticsearch should now be be available on port 9200 to all containers attached to the `internal` network. To make elasticsearch available to the outside world we add another service with elasticsearch client nodes. These nodes do not store data, they only forward search requests to the master-eligible nodes in `elasticsearch-master`. 

    docker service create \
    	--name elasticsearch-client \
    	--network internal \
    	--endpoint-mode dnsrr \
    	--user elasticsearch \
    	--replicas 1 \
    	--mount type=bind,source=/nps/applications/elasticsearch-client/config,target=/usr/share/elasticsearch/config \
    	elasticsearch

### NPS REST API

    docker service create \
        --network internal \
        --name nps-rest-api \
        -e ELASTICSEARCH_SERVER=elasticsearch-master \
        --mount type=bind,source=/nps/datasets,target=/nps/datasets \
        nps.uni-muenster.de:5000/nps/rest-api:v0.1-1-g94f3e49

Corresponding proxy server:

    docker service create \
        --name nps-rest-api-proxy \
        --network internal \
        -e SERVICE=nps-rest-api:80 \
        -p 3500:443 \
        --mount type=bind,source=/nps/applications/certs,target=/certs,readonly=true \
        janten/generic-proxy

### NPS Web Interface

    docker service create \
        --network internal \
        --name nps-web \
        -e ELASTICSEARCH_SERVER=elasticsearch-master \
        --mount type=bind,source=/nps/datasets,target=/nps/datasets,readonly=true \
        janten/nps-web

### NPS Indexer
This indexer writes more detailed information about DICOM datasets.

    docker service create \
        --name dataset-index-dicom-recent \
        --network internal \
        -e MAX_DAYS_AGO=5 \
        -e ELASTICSEARCH_SERVER=elasticsearch-master \
        --mount type=bind,source=/nps/datasets,target=/nps/datasets,readonly=true \
        neurology/dataset-index-dicom

### Kibana

    docker service create \
        --name kibana \
        --network internal \
        -e ELASTICSEARCH_URL=http://elasticsearch-master:9200 \
        kibana

### Kibana-Proxy

    docker service create \
        --name kibana-proxy \
        --network internal \
        -e SERVICE=kibana:5601 \
        -p 5601:443 \
        --mount type=bind,source=/nps/applications/certs,target=/certs,readonly=true \
        janten/generic-proxy

### Logstash

    docker service create \
        --name logstash \
        --network internal \
        -p 12201:12201/udp \
        -p 5140:5140/udp \
        --mount type=bind,source=/nps/applications/logstash/config,target=/config,readonly=true \
        logstash:2 -f /config/logstash.conf

### NPS Runner
These should eventually be scheduled to dedicated machines.

    docker service create \ 
    	--mode global \
    	--name nps-runner \
    	--mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
    	--mount type=bind,source=/nps/datasets,target=/nps/datasets \
    	janten/nps-cli \
    	receive -d /nps/datasets/ -r nps.uni-muenster.de

### GitLab

    docker service create \
    	--network internal \
    	--name gitlab \
    	-p 12000:12000 \
    	-p 12001:12001 \
    	--mount type=bind,source=/nps/applications/gitlab/config,target=/etc/gitlab \
    	--mount type=bind,source=/nps/applications/gitlab/logs,target=/var/log/gitlab \
    	--mount type=bind,source=/nps/applications/gitlab/data,target=/var/opt/gitlab \
    	--mount type=bind,source=/nps/applications/certs,target=/etc/gitlab/ssl,readonly=true \
    	gitlab/gitlab-ce:latest
   
### HAProxy

    docker service create \
        --network internal \
        --name proxy \
        -p 80:80 \
        -p 443:443 \
        --mount type=bind,source=/nps/applications/haproxy/haproxy.cfg,target=/usr/local/etc/haproxy/haproxy.cfg \
        --mount type=bind,source=/nps/applications/certs/nps-uni-muenster-de-crt-key.pem,target=/certs/nps-uni-muenster-de-crt-key.pem \
        haproxy:1.6

### DICOM Server
This DICOM server can only retrieve images.

    docker service create \
    	--name dicom-receiver \
    	-p 104:104 \
    	--replicas 2 \
    	--mount type=bind,source=/nps/datasets,target=/nps/datasets \
    	janten/nps-dicom-receiver:1.0

### Job Queue

    docker service create \
    --name nps-job-queue \
    --mount type=bind,source=/nps/applications/redis,target=/data \
    -p 6379:6379 \
    redis:alpine redis-server
