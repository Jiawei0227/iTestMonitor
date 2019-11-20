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
        if self.config["prometheus"]["runningMethod"] == "mvn":
            return "mvn test -f " + self.config["prometheus"]["projectLocation"]
        elif self.config["prometheus"]["runningMethod"] == "java":
            return "java -jar" + self.config["prometheus"]["projectLocation"]
        elif self.config["prometheus"]["runningMethod"] == "bash":
            return "bash " + self.config["prometheus"]["bashFileLoc"]
        else: 
            return "wrong running method"
        

    def get_test_run_metrics(self):
        # TODO
        pass



def main():
    
    c = Config()
    config = c.get_config()
    #print(config["prometheus"]["server"])
    #print(config)
    runningMethod = c.get_test_run_script()
    print(runningMethod)



if __name__ == "__main__":
    main()