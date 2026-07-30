import os
import configparser
from pathlib import Path

from furrifier_utils_enums import FurryTag
from furrifier_utils_notifier import show_notification
from furrifier_utils_basics import are_equal

# Allows getting and setting furrifier settings
# Code from frankk on the creator Musings Discord
# `Path(__file__).resolve()` finds the path to the current file
# The first `.parent` is to step above this file, which is the .ts4script
# The second `.parent` is to step above the .ts4script and into the directory alongside your mod
# Add one more `.parent` for each package that this file is nested in, if any
config_dir = Path(__file__).resolve().parent.parent
config_name = 'furrifier_settings.cfg'  # change this to your file's name
file_path = os.path.join(config_dir, config_name)


# Keep track of default settings
expected_settings = {
    'settings': {
        'automatic_furrifier': 'False',
        'automatic_targets': 'All',  # All, Randoms, or Premades
        'auto_aging': 'True',
        'premade_exempt': 'False',
        'furry_genetics': 'True',
        'strict_genetics': 'True',
        'strict_child_genes': 'False',
        'redo_genetics': 'False',
        'max_logs': '30',
        'eye_fixing': 'False',
        'cheat_mode': 'False',
        'furrification_chance': '100'
    },
    'preferences': {
        'leg_type': 'digitigrade',  # digitigrade, plantigrade, or either
        'head_type': 'either',  # fluffy, shaved, or either
        'fur_colors': 'natural',  # natural_only, natural, mixed, colorful, colorful_only
        'match_hair_fur': 'True',
        'avoid_savestate': 'False',
        'replace_hair': 'False',
        'use_neck_fluff': 'False',
        'use_eyebrows': 'True',  # furry, True, False
        'replace_accessories': 'True',
        'unlock_child_fur': 'False',
        'fixed_heads': 'False',
        'use_animated_tails': 'False',
        'use_extra_textures': 'False',
        'compatible_presets': 'False'
    },
    'autoremovals': {
        'hair': 'False',
        'body_hair': 'scaly',  # scaly, True, False
        'facial_hair': 'True',   # scaly, True, False
        'hats': 'True',
        'shoes_socks': 'True',
        'earrings': 'True',
        'piercings': 'True',
        'glasses': 'False',
        'makeup': 'True',
        'breasts': 'False',
        'clothes': 'False'
    }
}

migrations = {
    "settings.premade_exempt.True": "settings.automatic_targets.Randoms"
}

# For toggle mode, scaly toggles have scaly modes and furry toggles have furry modes
scaly_toggles = ['hair', 'body_hair']
furry_toggles = ['use_eyebrows']

config = configparser.ConfigParser()
# Create cfg if not created yet
if not os.path.exists(file_path):
    with open(file_path, 'w') as file:
        file.write(" ")

# Read and update the settings
with open(file_path) as file:
    config.read_file(file)

    # Migrations
    for migration_from, migration_to in migrations.items():
        migration_from_category, migration_from_setting, migration_from_value = migration_from.split('.')
        migration_to_category, migration_to_setting, migration_to_value = migration_to.split('.')
        if config.has_section(migration_from_category) and config.has_option(migration_from_category, migration_from_setting) and are_equal(migration_from_value, config.get(migration_from_category, migration_from_setting)):
            if not config.has_section(migration_to_category):
                config.add_section(migration_to_category)
            if not config.has_option(migration_to_category, migration_to_setting):
                config.set(migration_to_category, migration_to_setting, migration_to_value)

    # Make sure config has all sections and settings
    for needed_category in expected_settings:
        if not config.has_section(needed_category):
            config.add_section(needed_category)
        for needed_setting in expected_settings[needed_category]:
            if not config.has_option(needed_category, needed_setting):
                config.set(needed_category, needed_setting, expected_settings[needed_category][needed_setting])

    # Save updates
    with open(file_path, 'w') as config_file:
        config.write(config_file)


def get_setting_value(category: str, setting: str) -> str:
    return config.get(category, setting)


def is_setting_on(category: str, setting: str) -> bool:
    return are_equal('True', config.get(category, setting))


def is_automatic() -> bool:
    return are_equal("True", config.get("settings", "automatic_furrifier"))


def are_genetics_furry() -> bool:
    return are_equal("True", config.get("settings", "automatic_furrifier"))


def is_played_exempt() -> bool:
    return are_equal("True", config.get("settings", "played_exempt"))


def is_active_exempt() -> bool:
    return are_equal("True", config.get("settings", "active_exempt"))


def is_eye_fixing() -> bool:
    return are_equal("True", config.get("settings", "eye_fixing"))


def get_preferences() -> [int]:
    preferences = []

    leg_type_raw = config.get("preferences", "leg_type")
    if are_equal("plantigrade", leg_type_raw) or are_equal("either", leg_type_raw):
        preferences.append(FurryTag.LEG_PLANTIGRADE)
    if are_equal("digitigrade", leg_type_raw) or are_equal("either", leg_type_raw):
        preferences.append(FurryTag.LEG_DIGITIGRADE)

    head_type_raw = config.get("preferences", "head_type")
    if are_equal("fluffy", head_type_raw) or are_equal("either", head_type_raw):
        preferences.append(FurryTag.PREF_HEADS_FLUFFY)
    if are_equal("shaved", head_type_raw) or are_equal("either", head_type_raw):
        preferences.append(FurryTag.PREF_HEADS_SHAVED)

    if are_equal("natural_only", config.get("preferences", "fur_colors")):
        preferences.append(FurryTag.COLORS_NATURAL_ONLY)
    elif are_equal("natural", config.get("preferences", "fur_colors")):
        preferences.append(FurryTag.COLORS_NATURAL_PREF)
    elif are_equal("mixed", config.get("preferences", "fur_colors")):
        preferences.append(FurryTag.COLORS_MIXED)
    elif are_equal("colorful", config.get("preferences", "fur_colors")):
        preferences.append(FurryTag.COLORS_COLORFUL_PREF)
    elif are_equal("colorful_only", config.get("preferences", "fur_colors")):
        preferences.append(FurryTag.COLORS_COLORFUL_ONLY)

    if are_equal("True", config.get("preferences", "match_hair_fur")):
        preferences.append(FurryTag.PREF_MATCH_FUR_HAIR)
    if are_equal("True", config.get("preferences", "avoid_savestate")):
        preferences.append(FurryTag.PREF_NO_SS_HEADS)
    if are_equal("True", config.get("preferences", "replace_hair")):
        preferences.append(FurryTag.PREF_USE_SS_HAIR)
    if are_equal("True", config.get("preferences", "use_neck_fluff")):
        preferences.append(FurryTag.PREF_USE_NECK_FLUFF)
    if are_equal("True", config.get("preferences", "unlock_child_fur")):
        preferences.append(FurryTag.PREF_UNLOCKED_CHILD_FUR)
    if are_equal("True", config.get("preferences", "fixed_heads")):
        preferences.append(FurryTag.PREF_FIXED_HEADS)
    if are_equal("True", config.get("preferences", "use_extra_textures")):
        preferences.append(FurryTag.PREF_USE_DETAILS)

    if are_equal("True", config.get("preferences", "use_eyebrows")):
        preferences.append(FurryTag.PREF_EYEBROWS_ALL)
    elif are_equal("furry", config.get("preferences", "use_eyebrows")):
        preferences.append(FurryTag.PREF_EYEBROWS_FURRY)

    if are_equal("True", config.get("preferences", "replace_accessories")):
        preferences.append(FurryTag.PREF_FURRY_ACCESSORIES)

    if are_equal("True", config.get("preferences", "use_animated_tails")):
        preferences.append(FurryTag.PREF_USE_ANIMATED_TAILS)

    if are_equal("True", config.get("settings", "strict_child_genes")):
        preferences.append(FurryTag.PREF_STRICT_CHILD_GENES)

    if are_equal("True", config.get("preferences", "use_animated_tails")):
        preferences.append(FurryTag.PREF_USE_ANIMATED_TAILS)
    if are_equal("True", config.get("preferences", "compatible_presets")):
        preferences.append(FurryTag.PREF_COMPATIBLE_PRESETS)

    if are_equal("True", config.get("autoremovals", "hair")):
        preferences.append(FurryTag.AUTO_REMOVE_HAIR_ALL)
    elif are_equal("scaly", config.get("autoremovals", "hair")):
        preferences.append(FurryTag.AUTO_REMOVE_HAIR_SCALY)
    if are_equal("True", config.get("autoremovals", "body_hair")):
        preferences.append(FurryTag.AUTO_REMOVE_BODY_HAIR_ALL)
    elif are_equal("scaly", config.get("autoremovals", "body_hair")):
        preferences.append(FurryTag.AUTO_REMOVE_BODY_HAIR_SCALY)
    if are_equal("True", config.get("autoremovals", "facial_hair")):
        preferences.append(FurryTag.AUTO_REMOVE_FACIAL_HAIR)
    if are_equal("True", config.get("autoremovals", "hats")):
        preferences.append(FurryTag.AUTO_REMOVE_HATS)
    if are_equal("True", config.get("autoremovals", "shoes_socks")):
        preferences.append(FurryTag.AUTO_REMOVE_SHOES_SOCKS)
    if are_equal("True", config.get("autoremovals", "earrings")):
        preferences.append(FurryTag.AUTO_REMOVE_EARRINGS)
    if are_equal("True", config.get("autoremovals", "piercings")):
        preferences.append(FurryTag.AUTO_REMOVE_PIERCINGS)
    if are_equal("True", config.get("autoremovals", "glasses")):
        preferences.append(FurryTag.AUTO_REMOVE_GLASSES)
    if are_equal("True", config.get("autoremovals", "makeup")):
        preferences.append(FurryTag.AUTO_REMOVE_MAKEUP)
    if are_equal("True", config.get("autoremovals", "breasts")):
        preferences.append(FurryTag.AUTO_REMOVE_BREASTS)
    if are_equal("True", config.get("autoremovals", "clothes")):
        preferences.append(FurryTag.AUTO_REMOVE_CLOTHES)

    return preferences


# Changes a setting to the specified value
def update_setting(category: str, setting: str, value: str, message="", title=""):
    toggle_value = None
    if value == 'toggle':
        toggle_value = determine_toggle(category, setting)
        config.set(category, setting, toggle_value)
    else:
        config.set(category, setting, value)

    with open(file_path, 'w') as configfile:
        config.write(configfile)

    if message and title:
        # If toggling a setting, make the message reflect what the toggle did
        if toggle_value is not None:
            message = message.replace("{status}", "enabled" if toggle_value else "disabled")

        message = message.replace("_", " ")
        show_notification(message, notif_type="confirm", title=title)


# def get_setting_layout(path: str) -> dict:
#     path_parts = path.split('.')
#     return find_setting_layout(get_settings(), path_parts)
#
#
# def find_setting_layout(root: dict, path: [str]) -> dict:
#     if path[0] in root:
#         if len(path) == 1:
#             return root[path[0]]
#         else:
#             return find_setting_layout(root[path[0]], path[1:])
#
#     raise NameError(f"Cannot find requested setting {path}.")
#
#
# def get_current_setting_index(setting_path: str, setting_value: dict) -> int:
#     setting_category, setting = setting_path.split('.', 1)
#     current_value = get_setting_value(setting_category, setting)
#
#     if current_value in setting_value['values']:
#         return setting_value['values'].index(current_value)
#     else:
#         update_setting(setting_category, setting, setting_value['values'][0])
#         return 0
#
#
# def toggle_setting(setting_path: str):
#     setting_category, setting = setting_path.split('.', 1)
#     setting_value = get_setting_layout(setting_path)
#     current_index = get_current_setting_index(setting_path, setting_value)
#
#     if current_index + 1 > len(setting_value['values']):
#         new_index = 0
#     else:
#         new_index = current_index + 1
#
#     update_setting(setting_category, setting, setting_value['values'][new_index])


def determine_toggle(category: str, setting: str) -> str:
    cur_value = config.get(category, setting)

    # Toggles with furry_type specific values
    if setting in scaly_toggles or setting in furry_toggles:
        if are_equal("False", cur_value):
            return 'True'
        elif are_equal("True", cur_value):
            if setting in furry_toggles:
                return 'furry'
            else:
                return 'scaly'
        else:
            return 'False'

    # Regular True/False Toggles
    else:
        return str(cur_value == 'False')


def get_settings_str():
    try:
        with open(file_path) as f:
            setting_str = f.read()

        return setting_str
    except Exception as e:
        return f"Could not load settings: {e}"
