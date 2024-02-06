import os
import json
import datetime

class Configuration:
    '''
    Reading file configuration (config.json)
    located in the main directory of the project 
    '''
    
    def __init__(self, default='default', location='config.json', create_directory=True):
        self.parent_directory = os.path.dirname(os.getcwd())
        self.default = default
        self.location = os.path.join(os.getcwd(), 'config.json')
        self.create_directory = create_directory
        
    def set_location(self, location):
        self.location = location
        return self

    def get_location(self):
        return self.location

    def check_directory(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
        return self
    
    def get(self):
        with open(self.get_location()) as file_config:
            load_config = json.load(file_config)
            get_config = load_config['default']
            start_date = datetime.datetime.strptime(load_config['type'][get_config]['start_date'],'%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)
            end_date = datetime.datetime.strptime(load_config['type'][get_config]['end_date'],'%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)
            input_directory = load_config['type'][get_config]['input_directory']
            output_directory = load_config['output_directory']
            save_to_database = load_config['save_to_database']
            cpu_used = load_config['cpu_used']
            
            config = {
                'default' : get_config,
                'cpu_used': cpu_used,
                'save_to_database': save_to_database,
                'start_date' : start_date,
                'end_date' : end_date,
                'input_directory' : input_directory,
                'output_directory' : output_directory,
                'index_directory' : os.path.join(output_directory, 'Index'),
                'converted_directory' : os.path.join(output_directory, 'Converted'),
                'dayplot_directory' : os.path.join(output_directory, 'Dayplots'),
                'spectogram_directory' : os.path.join(output_directory, 'Spectogram'),
                'channels' : load_config['type'][get_config]['channels'] if get_config == 'sac' else [],
                'stations' : load_config['type'][get_config]['stations'] if get_config == 'lokon' else [],
                'type': load_config['type'],
                'code': load_config['type'][get_config]['code'] if 'code' in load_config['type'][get_config].keys() else None,
            }

            if not os.path.exists(input_directory):
                raise FileNotFoundError("Input directory tidak ditemukan : {}".format(input_directory))

            if (self.create_directory):
                self.check_directory(config['output_directory'])
                self.check_directory(config['index_directory'])
                self.check_directory(config['converted_directory'])
                self.check_directory(config['dayplot_directory'])
                self.check_directory(config['spectogram_directory'])

            return config