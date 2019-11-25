import prometheus

def main():
    prometheus.install_prometheus_server()
    prometheus.install_node_exporter()
    prometheus.start_prometheus()
    prometheus.archive_data()
    prometheus.stop_prometheus()

if __name__ == "__main__":
    main()
    #prometheus.restore_data()