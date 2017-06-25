## Networks
There are two global networks with defined usages, `internal` and `proxy`, additional networks may be created as necessary.

### Creating an overlay network
Overlay networks automatically span the whole cluster and are expanded if a new host joins. To create a new overlay network:
    
    docker network create \
        --driver overlay \
        --subnet=192.168.0.0/16 \
        internal

### The `internal` network
The `internal` network is the fabric which all services use to communicate internally and generally every service should be connected to this network.

### The `proxy` network
Services connected to `proxy` will automatically be made available at `nps.uni-muenster.de`.

### HTTPS Proxy
Websites can be configured to be served on `https://service_name.nps.uni-muenster.de` using TLS through HAproxy. There is no need to configure certificates explicitly.