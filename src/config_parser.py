import configparser


class CustomConfigParser(configparser.ConfigParser):
    def __init__(self):
        super().__init__()

    def _to_dict(self) -> dict:
        return self._sections
    
    # Prints the configuration nicely
    def show(self):
        print("\n* Current Configuration")
        for s in self.sections():
            print("-------------")
            print(s)
            for i in self.options(s):
                print("   " + i + ": " + self.get(s, i))
        print("-------------\n") 

    # Returns the configuration of a sections as dict
    def get_config(self, section: str) -> dict:
        config_dict = self._to_dict()
        return config_dict[section]
    

def load_config(config_path="config/gsm8k_cot_gpt.yml") -> CustomConfigParser:
    # Use parser that can read YML files
    parser = CustomConfigParser()

    parser.read(config_path)
    # parser.show()

    # 1. Verify that all sections are present
    for s in ['dataset', 'method', 'model', 'metric']:
        assert s in parser.sections()

    # Todo: Validate the parameters

    return parser
