import traceback

from Utilities import compile_module
from settings import *

import shutil
import json
from pathlib import Path
import os
import time

DEV_MODE = False
# DEV_MODE = True

try:
    file_path = Path("Scripts/furrifier_configs_register.json")
    with open(file_path) as file:
        data = json.load(file)

    file_path = Path("Scripts/furrifier_configs_register_default.py")
    processed_json = f"default_data = {json.dumps(data).replace('null', 'None')}\n"

    with open(file_path, 'w') as file:
        file.write(processed_json)
except (Exception,):
    print(traceback.format_exc())

print("JSON conversion finished")

if not DEV_MODE:
    root = os.path.dirname(os.path.realpath('__file__'))
    compile_module(creator_name, root, mods_folder)

    t = time.localtime()
    current_time = time.strftime("%#I:%M", t)
    print(f"\nCompiled Successfully at {current_time}")
else:
    source_folder = os.path.dirname(os.path.realpath('__file__')) + "/Scripts"
    destination_folder = mods_folder + "/../DEV_FURRIFIER/Scripts"

    if os.path.exists(destination_folder):
        shutil.rmtree(destination_folder)

    shutil.copytree(source_folder, destination_folder)

    t = time.localtime()
    current_time = time.strftime("%#I:%M", t)
    print(f"\nDEV Copied Successfully at {current_time}")

