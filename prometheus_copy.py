"""
This module helps to install prometheus and collect prometheus metrics data
It contains: prometheus installation on server, node_exporter installation on hosts
             archive prometheus data by calling snapshot and transfer file to local machine
API:
  install_prometheus()
  save_prometheus_data(prometheus_server_host, local_dir)
  start_prometheus_server(prometheus_server_host)
  cleanup_shutdown(prometheus_server_host)
"""
from subprocess import check_call
import os
import logging
import fabric.api as fabric
import json

from textwrap import dedent


LIB_DIR = os.path.abspath(os.path.dirname(__file__))

LOG = logging.getLogger(__name__)

PROMETHEUS_VERSION="2.14.0"
NODE_EXPORTER_VERSION="0.18.1"
FABRIC_MAX_POOL_SIZE=10
PROMETHEUS_SERVICE=dedent("""
    [Unit]
    Description=Prometheus Server
    Documentation=https://prometheus.io/docs/introduction/overview/
    After=network-online.target
    [Service]
    User=prometheus
    Restart=on-failure
    ExecStart=/opt/prometheus/prometheus-{0}.linux-amd64/prometheus \
    --config.file=/opt/prometheus/prometheus.yml \
    --storage.tsdb.path=/opt/prometheus/data \
    --web.enable-admin-api
    [Install]
    WantedBy=multi-user.target
""".format(PROMETHEUS_VERSION))

NODE_EXPORTER_SERVICE=dedent("""
    [Unit]
    Description=Node Exporter
    [Service]
    User=prometheus
    ExecStart=/opt/prometheus/node_exporter-{0}.linux-amd64/node_exporter
    [Install]
    WantedBy=multi-user.target
""".format(NODE_EXPORTER_VERSION))

def install_node_exporter():
  return fabric.run(dedent("""
    useradd --no-create-home --shell /bin/false prometheus
    # Node Exporter
    mkdir -p /opt/prometheus
    chown -R prometheus:prometheus /opt/prometheus
    cd /opt/prometheus
    wget --quiet https://github.com/prometheus/prometheus/release/node_exporter-{NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
    tar -xzvf node_exporter-{NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
    rm node_exporter-{NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
    cat > /etc/systemd/system/node_exporter.service<<EOF{NODE_EXPORTER_SERVICE}EOF
    systemctl daemon-reload
    systemctl start node_exporter
  """).format(S3_BUILD_URL=S3_BUILD_URL,
              PROMETHEUS_GBN=PROMETHEUS_GBN,
              NODE_EXPORTER_SERVICE=NODE_EXPORTER_SERVICE,
              NODE_EXPORTER_VERSION=NODE_EXPORTER_VERSION))

@fabric.task
def install_prometheus_server():
  #prometheus_yml=get_prometheus_yml(local_host_target, remote_hosts_target)
  return fabric.run(dedent("""
    useradd --no-create-home --shell /bin/false prometheus
    # prometheus_server
    mkdir -p ~/SoftwareTest/data
    chown -R prometheus:prometheus /opt/prometheus/data
    cd ~/SoftwareTest
    wget --quiet https://github.com/prometheus/prometheus/release/download/v{PROMETHEUS_VERSION}/prometheus-{PROMETHEUS_VERSION}.darwin-amd64.tar.gz
    tar -xzf prometheus-{PROMETHEUS_VERSION}.darwin-amd64.tar.gz
    rm prometheus-{PROMETHEUS_VERSION}.darwin-amd64.tar.gz
  """).format(PROMETHEUS_VERSION=PROMETHEUS_VERSION))

@fabric.task
def archive_data():
  # snapshot prometheus data
  archive_status = fabric.run(dedent("""
    cd /opt/prometheus
    curl -XPOST http://localhost:9090/api/v1/admin/tsdb/snapshot?skip_head=false
  """))
  re = json.loads(archive_status)

  if re['status'] == 'success':
    archive_file = re['data']['name']
    fabric.run(dedent("""
    cd /opt/prometheus/data/snapshots
    mv {archive_file} data
    tar -czvf prometheus_data.tar.gz data
    mv prometheus_data.tar.gz ../..
    """).format(archive_file=archive_file))
  else:
    LOG.error("Archive prometheus data failed. Shell return : {status}".format(status=archive_status))

@fabric.task
def cleanup_shutdown_task():
  fabric.run(dedent("""
    systemctl stop prometheus
    rm -r /opt/prometheus/data
    rm /opt/prometheus/prometheus_data.tar.gz
    mkdir /opt/prometheus/data
    chown -R prometheus:prometheus /opt/prometheus/data
  """))


@fabric.task
def transferfile(local_dir):
  fabric.get('/opt/prometheus/prometheus_data.tar.gz', local_path=local_dir)

@fabric.task
def start_prometheus_systemctl():
  fabric.run("systemctl start prometheus")

def get_prometheus_yml(local_host_target, remote_hosts_target, impalad_hosts_target):
  return dedent("""
    global:
      scrape_interval:     1s
    scrape_configs:
    - job_name: 'prometheus'
      static_configs:
      - targets: ['localhost:9090']
    - job_name: 'node'
      static_configs:
        - targets: [{local_targets}]
          labels:
            group: 'local'
        - targets: [{remote_targets}]
          labels:
            group: 'remote'
    - job_name: 'impala'
      metrics_path: /metrics_prometheus
      static_configs:
        - targets: [{impalad_targets}]
  """.format(local_targets=local_host_target,
             remote_targets=remote_hosts_target,
             impalad_targets=impalad_hosts_target))

def install_prometheus(prometheus_server_host):
  """Installs prometheus on the cluster.
    Args:
      prometheus_server_host: where to install prometheus server, should be an address
  """

  all_nodes = set(impala_hosts)
  all_nodes.add(prometheus_server_host)
  all_nodes.add(catalog_host)
  all_nodes.add(statestore_host)

  # install node_exporter
  with fabric.settings(hosts=all_nodes, warn_only=True):
    fabric.execute(install_node_exporter)
  LOG.info("Install node_exporter on {0}".format(all_nodes))

  all_nodes.remove(prometheus_server_host)
  # install prometheus server
  local_host_target = "'" + prometheus_server_host + ":9100'"
  remote_hosts_target = ",".join(["'{0}:9100'".format(prometheus_node) for prometheus_node in all_nodes])
  impala_hosts_target = ",".join(["'{0}:25000'".format(prometheus_node) for prometheus_node in all_nodes])

  with fabric.settings(hosts=prometheus_server_host, warn_only=True):
    fabric.execute(install_prometheus_server, local_host_target, remote_hosts_target, impala_hosts_target)
  LOG.info("Install prometheus server on {0}".format(prometheus_server_host))

def save_prometheus_data(prometheus_server_host, local_dir):
  """Archive prometheus monitoring data into local folder
    Assumption:
      prometheus already installed and running on the server
    Args:
      prometheus_server_host: server address
      full_result_dir: result dir in local machine
  """
  with fabric.settings(hosts=prometheus_server_host, warn_only=True):
    fabric.execute(archive_data)
    fabric.execute(transferfile, local_dir)

  LOG.info("Archive prometheus data into {0}".format(local_dir))

def start_prometheus_server(prometheus_server_host):
  """Start prometheus server on prometheus_server_host
    Assumption:
      prometheus server already installed through install_prometheus() function
    Arg:
      prometheus_server_host: address of prometheus server
  """
  with fabric.settings(hosts=prometheus_server_host, warn_only=True):
    fabric.execute(start_prometheus_systemctl)

def cleanup_shutdown(prometheus_server_host):
  """clean up prometheus data and shutdown service
  """
  with fabric.settings(hosts=prometheus_server_host, warn_only=True):
    fabric.execute(cleanup_shutdown_task)

  LOG.info("Prometheus data clean up and shutdown")