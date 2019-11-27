import prometheus
import config

def runtest():
    config = config.Config()
    script = config.get_test_run_script()
    
    pass

def main():
    prometheus.install_prometheus_server()
    prometheus.install_node_exporter()
    prometheus.start_prometheus()
    runtest()
    prometheus.archive_data()
    prometheus.stop_prometheus()

if __name__ == "__main__":
    main()
    #prometheus.restore_data()