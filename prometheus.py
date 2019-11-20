import subprocess
from textwrap import dedent
import time

PROMETHEUS_VERSION="2.14.0"
NODE_EXPORTER_VERSION="0.18.1"

def stop_prometheus():
    time.sleep(5)
    p = subprocess.Popen("""
       kill -9 $(pgrep prometheus); 
    """, shell=True)
    print("Prometheus Server Stopped.")

def start_prometheus():
    p = subprocess.Popen(dedent("""
        kill -9 $(pgrep prometheus); 
        cd ~/SoftwareTest/prometheus-{0}.darwin-amd64;
        ./prometheus \
        --config.file=../prometheus.yml \
        --storage.tsdb.path=../data \
        --web.enable-admin-api
        """).format(PROMETHEUS_VERSION), shell=True )
    print("Prometheus Server Started.")

def install_prometheus_server():
    print("Installing Prometheus Server.") 
    prometheus_yml = get_prometheus_yml()
    p = subprocess.Popen(dedent("""
        # prometheus_server
        cat > ~/SoftwareTest/prometheus.yml<<EOF{PROMETHEUS_YML}EOF
        mkdir -p ~/SoftwareTest/data;
        cd ~/SoftwareTest;
        if [ -d ~/SoftwareTest/prometheus-{PROMETHEUS_VERSION}.darwin-amd64 ]; then exit 0; fi;
        wget --quiet https://github.com/prometheus/prometheus/releases/download/v{PROMETHEUS_VERSION}/prometheus-{PROMETHEUS_VERSION}.darwin-amd64.tar.gz;
        tar -xzvf prometheus-{PROMETHEUS_VERSION}.darwin-amd64.tar.gz;
        rm prometheus-{PROMETHEUS_VERSION}.darwin-amd64.tar.gz;
        """).format(PROMETHEUS_VERSION=PROMETHEUS_VERSION, PROMETHEUS_YML=prometheus_yml), shell=True)
    p.wait()
    print("Install Prometheus Server on localhost successfully!")

def install_node_exporter():
    print("Installing Node Exporter.")  
    p = subprocess.Popen(dedent("""
        mkdir -p ~/SoftwareTest;
        cd ~/SoftwareTest;
        if [ -d ~/SoftwareTest/node_exporter-{NODE_EXPORTER_VERSION}.darwin-amd64 ]; then exit 0; fi;
        wget --quiet https://github.com/prometheus/node_exporter/releases/download/v{NODE_EXPORTER_VERSION}/node_exporter-{NODE_EXPORTER_VERSION}.darwin-amd64.tar.gz;
        tar -xzvf node_exporter-{NODE_EXPORTER_VERSION}.darwin-amd64.tar.gz;
        rm node_exporter-{NODE_EXPORTER_VERSION}.darwin-amd64.tar.gz;
        """).format(NODE_EXPORTER_VERSION=NODE_EXPORTER_VERSION), shell=True)
    p.wait()
    print("Install Node Exporter successfully.")

def get_prometheus_yml():
  return dedent("""
    global:
      scrape_interval: 1s
    scrape_configs:
    - job_name: 'prometheus'
      static_configs:
      - targets: ['localhost:9090']
    - job_name: 'node'
      static_configs:
        - targets: ['localhost:9100']
  """.format())