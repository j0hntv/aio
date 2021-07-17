import json
import os
from glob import glob


def load_routes(directory_path='routes'):
    for filepath in glob(os.path.join(directory_path, '*.json')):
        with open(filepath) as file:
            yield json.load(file)
