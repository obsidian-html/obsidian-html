# Install ETCD   
   
``` bash
# Create a temporary dir 
mkdir /tmp/etcd && cd /tmp/etcd

# Download the tarball
curl -s https://api.github.com/repos/etcd-io/etcd/releases/latest \
  | grep browser_download_url \
  | grep linux-amd64 \
  | cut -d '"' -f 4 \
  | wget -qi -

# Unpack and enter folder
tar xvf etcd-v*.tar.gz
cd etcd-*/

# Move etcd and etcdcdl binaries to path
sudo mv etcd* /usr/local/bin/

# Clean up
cd ~
rm -rf /tmp/etcd

# Test etcd and etcdctl
etcd --verion
etcdctl version
```   
   
# Start ETCD   
```bash
etcd &
```   
This starts the service. You can `Ctrl+C` to quit the output and the service should continue to run.    
   
# Related:   
[Basic Usage ETCD](Basic%20Usage%20ETCD.md)