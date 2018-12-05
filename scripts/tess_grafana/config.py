from attrdict import AttrDict
import json
import os

class Configuration:
    config = None
    def __init__(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(dir_path+'/config.json') as json_data_file:
            self.config = AttrDict(json.load(json_data_file))
