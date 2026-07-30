from Utilities import compile_module
from settings import *
import time
import shutil

DEV_MODE = True
DEV_MODE = False

if not DEV_MODE:
    root = os.path.dirname(os.path.realpath('__file__'))
    compile_module(creator_name, root, mods_folder)

    t = time.localtime()
    current_time = time.strftime("%#I:%M", t)
    print(f"\nCompiled Successfully at {current_time}")
else:
    source_folder = os.path.dirname(os.path.realpath('__file__')) + "/Scripts"
    destination_folder = mods_folder + "/../DEV_CREATOR/Scripts"

    if os.path.exists(destination_folder):
        shutil.rmtree(destination_folder)

    shutil.copytree(source_folder, destination_folder)

    t = time.localtime()
    current_time = time.strftime("%#I:%M", t)
    print(f"\nDEV Copied Successfully at {current_time}")