import re
import json
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'Scripts'))
from furry_premade_data import furrifier_addon

new_file_path = Path('./Furry_Premade_Sims.ffa')

def substitutions(text: str):
    """
    Makes the format purdy

    Args:
        text (str): The og text

    Returns:
        str: The modified text
    """
    text = re.sub(r'\[\s+([\d\-ntf"])', r'[\1', text)
    text = re.sub(r'([\dle"]),\n+(?!\s+"\w+":)', r'\1, ', text)
    text = re.sub(r', +', ', ', text)
    text = re.sub(r'([\dle"])\s+]', r'\1]', text)
    text = re.sub(r'\[\s+\[(.+)],\s+(?=[\d\-ntf"])', r'[[\1], ', text)

    return text

def int_to_hex(x: int):
    """
    Converts an int value to a hex value

    Args:
        x (int): The value to convert

    Returns:
        str: The converted value
    """
    if isinstance(x, str):
        return x
    elif x < 0:
        y = f"{abs(x):x}".upper().rjust(16, '0')
        return f"-{y}"
    else:
        return f"{x:x}".upper().rjust(16, '0')


for sim_name, sim_presets in furrifier_addon['presets'].items():
    for preset_name, preset_value in sim_presets.items():
        for occult_label, occult_appearance in preset_value["appearance"].items():
            for outfit_label, outfit_conditions in occult_appearance["outfits"].items():
                for outfit_condition, outfit_parts in outfit_conditions.items():
                    outfit_conditions[outfit_condition] = [int_to_hex(part) for part in outfit_parts]

            for part_condition in occult_appearance['genetics']['parts']:
                occult_appearance['genetics']['parts'][part_condition] = [int_to_hex(part) for part in occult_appearance['genetics']['parts'][part_condition]]

            occult_appearance['genetics']['sliders'] = {int_to_hex(key): value for key, value in occult_appearance['genetics']['sliders'].items()}

            occult_appearance['genetics']['sculpts'] = [int_to_hex(part) for part in occult_appearance['genetics']['sculpts']]
            occult_appearance['genetics']['skin_tone'] = int_to_hex(occult_appearance['genetics']['skin_tone'])


print(len(furrifier_addon['presets']))
with open(new_file_path, 'w') as f:
    f.write(substitutions(json.dumps(furrifier_addon, indent=4)))