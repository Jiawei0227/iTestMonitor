import subprocess
import requests
from textwrap import dedent
import time

PROMETHEUS_VERSION="2.14.0"
NODE_EXPORTER_VERSION="0.18.1"

def run_test(script):
  print("Start test running.")
  p = subprocess.Popen(dedent(
    """{0}"""
  ).format(script), shell=True)
  p.wait()


def stop_prometheus():
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
        --web.enable-admin-api &
        """).format(PROMETHEUS_VERSION), shell=True)
    time.sleep(3)
    print("Prometheus Server Started.")

def install_prometheus_server():
    print("Installing Prometheus Server.") 
    prometheus_yml = get_prometheus_yml()
    p = subprocess.Popen(dedent("""
        # prometheus_server
        mkdir -p ~/SoftwareTest
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

def archive_data():
  # snapshot prometheus data
  re = requests.post(url="http://localhost:9090/api/v1/admin/tsdb/snapshot?skip_head=false")
  archive_file = re.json()["data"]["name"]
  p = subprocess.Popen(dedent("""
    cd ~/SoftwareTest/data/snapshots;
    mv {archive_file} data;
    tar -czvf prometheus_data.tar.gz data;
    mv prometheus_data.tar.gz ../..
  """).format(archive_file=archive_file), shell=True)

def restore_data():
  p = subprocess.Popen(dedent("""
    kill $(pgrep node)
    cd ~/SoftwareTest;
    rm -rf prometheus_data;
    tar -xzvf prometheus_data.tar.gz -C ~/SoftwareTest/snapshot;
    prometheus-{0}.darwin-amd64/prometheus \
    --config.file=prometheus2.yml \
    --storage.tsdb.path=snapshot/data \
    --web.enable-admin-api &
  """).format(PROMETHEUS_VERSION), shell=True) 


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