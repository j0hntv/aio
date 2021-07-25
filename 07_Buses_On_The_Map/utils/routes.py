import json
import os
from glob import glob


def load_routes(directory_path, routes_number):
    for filepath in glob(os.path.join(directory_path, '*.json'))[:routes_number]:
        with open(filepath) as file:
            yield json.load(file)
