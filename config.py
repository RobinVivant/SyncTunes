import yaml
import os

def load_config():
    config_path = 'config.yaml'
    if not os.path.exists(config_path):
        config_path = 'default_config.yaml'
    
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)
