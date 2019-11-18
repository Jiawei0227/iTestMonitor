import yaml


"""
Config file for iTestMonitor framework
"""
class Config():
    def __init__(self):
        self.config = yaml.safe_load(open("config.yml"))
    
    def get_config(self):
        return self.config

    def get_test_run_script(self):
        # TODO
        pass

    def get_test_run_metrics(self):
        # TODO
        pass



def main():
    c = Config()
    config = c.get_config()
    print(config["prometheus"]["server"])

if __name__ == "__main__":
    main()