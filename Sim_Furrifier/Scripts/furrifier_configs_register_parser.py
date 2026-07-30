from furrifier_configs_register_default import default_data
import json
import re
import copy
from pathlib import Path
import os
import traceback

from furrifier_utils_notifier import show_notification
from furrifier_utils_enums import FurryTag, FurryFlag, ColorBlock, ColorIndex, expected_json_version
from furrifier_utils_basics import format_exception, hex_to_int, is_part_installed, filter_none, print_file, remove_duplicates_alt, get_mod_dir
from furrifier_utils_tag_block import FurryTagCondition, check_custom_tags, stringify_conditions
from furrifier_res_premades import premades_data
from sims.outfits.outfit_enums import BodyType

# Keep track of any problems encountered during parsing
problems = []
custom_tag_num = 600

# Keep track of what addons and registers are used
used_addons = []


def load_json(reload: bool) -> dict:
    """
    Loads and parses the JSON file

    Args:
        reload (bool): Whether the load is the initial load or a reload

    Returns:
        dict: The parsed furrifier data
    """
    furrifier_data = {}

    FurryTagCondition.custom_tags = {}
    FurryTagCondition.custom_tag_num = 1000
    FurryTagCondition.all_parts = {}
    FurryTagCondition.all_species = {}

    global custom_tag_num, used_addons, problems
    used_addons = []
    problems = []
    try:
        # Load custom base file if it exists
        mods_dir = get_mod_dir()
        if mods_dir:
            registers: [Path] = list(mods_dir.rglob('*.ffr'))

            if len(registers) == 0:
                # If no custom file exists, use the default
                furrifier_data = copy.deepcopy(default_data)
            elif len(registers) == 1:
                used_addons.append(registers[0].stem)
                with open(registers[0], 'r') as file:
                    furrifier_data = json.load(file)
            else:
                raise OSError(f"Too many custom registers! {registers}")
        else:
            # If no custom file exists, use the default
            furrifier_data = copy.deepcopy(default_data)

        # Check for custom tags
        check_custom_tags(furrifier_data['custom_tags'])
        furrifier_data['custom_tags'] = FurryTagCondition.custom_tags

        # Check if the json is valid
        validate_json(furrifier_data)

        # Load addons
        furrifier_data = load_addons(furrifier_data)

        # Convert the strings to ints or objects
        furrifier_data = convert_types(furrifier_data)

        # Collect identifiers
        furrifier_data = collect_identifiers(furrifier_data)

        # Convert Color Key
        furrifier_data = convert_color_key(furrifier_data)

        if problems:
            print_problems()
        elif reload:
            show_notification(text="Successfully reloaded furrifier register", notif_type='confirm', title='Furrifier Reloaded')
    except (Exception,):
        text = traceback.format_exc()
        exception = format_exception(text)
        problems.append(f"\n\n{str(exception)}")
        print_problems()

    return furrifier_data


def load_addons(data: dict, convert=True):
    # Check for official addons
    try:
        from furry_premade_data import get_premade_addon
        used_addons.append("Furry Premade Sims")
        data = apply_addon(get_premade_addon(), "Furry Premade Sims", data, convert, True)
    except ImportError:
        pass

    # Check for unofficial addons
    mods_dir = get_mod_dir()
    if mods_dir:
        addons: [Path] = list(get_mod_dir().rglob('*.ffa'))
        addons.sort(key=lambda x: x.stem)
        for addon in addons:
            addon: Path
            used_addons.append(addon.stem)
            data = apply_addon_file(addon, data, convert)

    return data


def apply_addon_file(path: Path, data: dict, convert=True):
    with open(path, 'r') as file:
        addon_data = json.load(file)
    return apply_addon(addon_data, path.stem, data, convert)


def apply_addon(addon_data: dict, addon_name: str, data: dict, convert=True, force=False):
    try:
        # Handle custom tags before anything else
        if 'custom_tags' in addon_data:
            check_custom_tags(addon_data['custom_tags'])
            data['custom_tags'] = FurryTagCondition.custom_tags

        # Check if the json is valid
        validate_json(addon_data)

        for addon_key in addon_data.keys():
            addon_key: str
            if addon_key != 'custom_tags':
                # Apply addon parts
                if addon_key in data:
                    new_data = apply_addon_part(addon_data[addon_key], data[addon_key], force)
                    if new_data is not None:
                        data[addon_key] = new_data
                    else:
                        del data[addon_key]
                else:
                    problems.append(f'Addon {addon_name} is trying to overwrite {addon_key}, which does not exist.')

        return data

    except (Exception,):
        text = traceback.format_exc()
        exception = format_exception(text)
        problems.append(f"\n\n{str(exception)}")
        return data


def apply_addon_part(addon_part, data_part: dict, force=False):
    """
    Recursively applies addon parts to the data

    Args:
        addon_part: The part of the addon being applied
        data_part (dict): The part of the data the addon is being applied to

    Returns:
        dict: The modified data part
    """
    # TODO: Fix keys with empty dicts as values being deleted
    # If the value is a dict, run this on each key
    if isinstance(addon_part, dict):
        for addon_key in addon_part.keys():
            addon_key: str

            # Check if the data part has that field
            if addon_key not in data_part:
                # If the data part does not have that field, create the field with the expected type
                if isinstance(addon_part[addon_key], dict):
                    data_part[addon_key] = {}
                elif isinstance(addon_part[addon_key], list):
                    data_part[addon_key] = []
                else:
                    data_part[addon_key] = None

            new_data = apply_addon_part(addon_part[addon_key], data_part[addon_key], force)
            if new_data is not None or force:
                data_part[addon_key] = new_data
            else:
                del data_part[addon_key]
    # If the value is a list, Replace the old list with the new list, replacing any ADDON_COPYs with the old list
    elif isinstance(addon_part, list):
        new_list = []
        for element in addon_part:
            if isinstance(element, str) and element.strip().casefold() == "ADDON_COPY".casefold():
                new_list.extend(data_part)
            else:
                new_list.append(element)
        data_part = new_list
    # If the value is a string, replace any instances of ADDON_COPY with the old value
    elif isinstance(addon_part, str):
        data_part = addon_part.replace("ADDON_COPY", f"({data_part})")
    # If the value is any other value, replace the old value with the new value
    else:
        data_part = addon_part

    return data_part


# TODO: Add more tests
def validate_json(data: dict):
    """
    Runs a series of checks to make sure the json will work correctly

    Args:
        data (dict): The furrifier data to check
    """
    # Collect all parts and species using addon application logic to make sure addons are treated correctly
    if 'parts' in data:
        for part_category in data['parts'].values():
            if 'part_options' in part_category:
                FurryTagCondition.all_parts = apply_addon_part(part_category['part_options'], FurryTagCondition.all_parts)
    if 'substitutes' in data:
        for substitute_category in data['substitutes'].values():
            FurryTagCondition.all_parts = apply_addon_part(substitute_category, FurryTagCondition.all_parts)
    if 'special_removals' in data:
        for removal_category in data['special_removals'].values():
            FurryTagCondition.all_parts = apply_addon_part(removal_category, FurryTagCondition.all_parts)
    if 'species_categories' in data:
        for species_category in data['species_categories'].values():
            if 'species' in species_category:
                FurryTagCondition.all_species = apply_addon_part(species_category['species'], FurryTagCondition.all_species)

    # Test version
    if 'version' in data and data['version'] != expected_json_version:
        problems.append(f"Custom Json Version {data['version']} is not compatible with Furrifier Version. Expected JSON Version: {expected_json_version}. Please update the custom json to avoid issues.")

    # Test species
    if 'species_categories' in data:
        for species_category in data['species_categories'].values():
            species_category: dict
            for species_label, species in species_category['species'].items():
                # Check that alternate spcies exist
                if 'alternatives' in species:
                    for species_list in species["alternatives"].values():
                        for label in species_list:
                            if label not in FurryTagCondition.all_species.keys() and label != "ADDON_COPY":
                                problems.append(f"ERROR: Alternative species {label} for species {species_label} does not exist")

    # Test parts
    unique_ids = set()
    if 'parts' in data:
        for part_category in data['parts'].values():
            part_category: dict

            if 'part_options' in part_category:
                for part_label, part in part_category['part_options'].items():
                    part_label: str
                    part: dict
                    if part is not None:
                        if 'ids' in part:
                            # Check that ids are unique, ignoring racoon tails
                            if 'Racoon' not in part_label:
                                temp_ids = set()
                                for part_id in part['ids']:
                                    part_id: str
                                    if part_id is not None and part_id != "ADDON_COPY":
                                        if part_id in unique_ids:
                                            problems.append(f"WARNING: Part {part_label} has non-unique id {part_id}")
                                        temp_ids.add(part_id)
                                unique_ids.update(temp_ids)

                        if 'flags' in part:
                            for flag in part['flags']:
                                if flag not in FurryFlag and flag != "ADDON_COPY":
                                    problems.append(f"Flag '{flag}' on '{part_label}' is not recognized")

                        if 'custom_format' in part:
                            # Test custom formats
                            if isinstance(part['custom_format'], list):
                                # Test custom formats to make sure they're all in range
                                if any(0 > ColorIndex[idx].value > 44 for idx in part['custom_format'] if idx != "ADDON_COPY"):
                                    problems.append(f"ERROR: Custom format specifies invalid indices: {part_label}")
                                # Test custom formats to make sure they are the same lengths as the ids
                                if len(part['custom_format']) != len(part['ids']):
                                    problems.append(f"ERROR: Custom format length doesn't match part list length: {part_label}")

                        if "flags" in part:
                            # Test that formats are the correct len
                            if "FORMAT_FULL" in part['flags'] and len(part['ids']) != 125:
                                problems.append(f"ERROR: Wrong number of options for format Full: {part_label} ({len(part['ids'])} vs {125})")
                            elif "FORMAT_NATURAL_AND_SORA" in part['flags'] and len(part['ids']) != 48:
                                problems.append(f"ERROR: Wrong number of options for format Naturals and Sora: {part_label} ({len(part['ids'])} vs {48})")
                            elif "FORMAT_SAVESTATE" in part['flags'] and len(part['ids']) != 13:
                                problems.append(f"ERROR: Wrong number of options for format Savestate: {part_label} ({len(part['ids'])} vs {13})")
                            elif "FORMAT_HAIR" in part['flags'] and len(part['ids']) != 24:
                                problems.append(f"ERROR: Wrong number of options for format Hair: {part_label} ({len(part['ids'])} vs {24})")

                            # Test that formats have pools provided, if not hair
                            if ("FORMAT_FULL" in part['flags'] or "FORMAT_NATURAL_AND_SORA" in part['flags'] or "FORMAT_SAVESTATE" in part['flags']) and 'pools' not in part:
                                problems.append(f"ERROR: Colored part has no assigned pool: {part_label}")
                            elif not ("FORMAT_FULL" in part['flags'] or "FORMAT_NATURAL_AND_SORA" in part['flags'] or "FORMAT_SAVESTATE" in part['flags']) and 'pools' in part and 'custom_format' not in part:
                                problems.append(f"ERROR: Colored part has no assigned format: {part_label}")

                        # Check that alternate parts exist
                        if 'alternatives' in part:
                            for part_list in part["alternatives"].values():
                                for label in part_list:
                                    if label not in FurryTagCondition.all_parts.keys() and label != "ADDON_COPY":
                                        problems.append(f"ERROR: Alternative part {label} for part {part_label} does not exist")

    # Test removals
    if 'special_removals' in data:
        for removal_category in data['species_categories'].values():
            removal_category: dict
            for label, part in removal_category['species'].items():
                pass

    # Test substitutes
    if 'species_categories' in data:
        for sub_category in data['species_categories'].values():
            sub_category: dict
            for label, part in sub_category['species'].items():
                pass

    # Test presets
    # if 'presets' in data:
    #     for sim_name in data['presets'].keys():
    #         if sim_name not in premades_data and sim_name != "GENERIC":
    #             problems.append(f"ERROR: Sim {sim_name} from presets not recognized")


def convert_types(data: dict):
    """
    Changes all the strings in the furrifier data into ints or enums, so we don't need to do any conversions while using it

    Args:
        data (dict): data being converted

    Returns:
        dict: The modified furrifier data
    """
    if 'species_categories' in data:
        for species_category in data['species_categories'].values():
            species_category: dict
            if "icon_id" in species_category:
                species_category['icon_id'] = int(species_category['icon_id'], 16)
            if "localized_name_id" in species_category:
                species_category['localized_name_id'] = int(species_category['localized_name_id'], 16)

            convert_types_in_list(species_category['species'].values())

            for species in species_category['species'].values():
                species: dict
                if "icon_id" in species:
                    species['icon_id'] = int(species['icon_id'], 16)
                if "localized_name_id" in species:
                    species['localized_name_id'] = int(species['localized_name_id'], 16)

    if 'parts' in data:
        new_parts_data = {}
        for part_category_label, part_category_value in data['parts'].items():
            part_category_label: str
            part_category_value: dict
            if 'removal' in part_category_value:
                convert_types_for_item(part_category_value['removal'])
            if 'part_options' in part_category_value:
                convert_types_in_list(part_category_value['part_options'].values(), True)

            new_parts_data[str(BodyType[part_category_label].value)] = part_category_value

        data['parts'] = new_parts_data

    if 'sculpts' in data:
        for sculpt_category in data['sculpts'].values():
            sculpt_category: dict
            if 'vanilla_sculpts' in sculpt_category:
                sculpt_category['vanilla_sculpts'] = convert_id_list(sculpt_category['vanilla_sculpts'])
            if 'sculpt_options' in sculpt_category:
                convert_types_in_list(sculpt_category['sculpt_options'].values())

    if 'skintones' in data:
        convert_types_in_list(data['skintones'].values())

    if 'special_removals' in data:
        new_removals_data = {}
        for removal_category_label, removal_category_value in data['special_removals'].items():
            removal_category_label: str
            removal_category_value: dict

            convert_types_in_list(removal_category_value.values(), True)

            new_removals_data[str(BodyType[removal_category_label].value)] = data['special_removals'][removal_category_label]
        data['special_removals'] = new_removals_data

    if 'substitutes' in data:
        new_substitutes_data = {}
        new_subs = copy.deepcopy(data['substitutes'])
        for substitute_category in data['substitutes']:
            substitute_category: str
            for substitute_part in data['substitutes'][substitute_category]:
                substitute_part: str

                if 'part_options' in new_subs[substitute_category][substitute_part]:
                    new_subs[substitute_category][substitute_part]['part_options'] = {}
                    for part in data['substitutes'][substitute_category][substitute_part]['part_options']:
                        if is_part_installed(hex_to_int(data['substitutes'][substitute_category][substitute_part]['part_options'][part])):
                            new_subs[substitute_category][substitute_part]['part_options'][hex_to_int(part)] = hex_to_int(data['substitutes'][substitute_category][substitute_part]['part_options'][part])
                        else:
                            new_subs[substitute_category][substitute_part]['part_options'][hex_to_int(part)] = None

                    if not any(part_id is not None for part_id in new_subs[substitute_category][substitute_part]['part_options'].values()):
                        new_subs[substitute_category][substitute_part]['requires'] = "MISC_INVALID"

                if 'requires' in new_subs[substitute_category][substitute_part]:
                    new_subs[substitute_category][substitute_part]['requires'] = convert_condition(new_subs[substitute_category][substitute_part]['requires'])

                if 'flags' in new_subs[substitute_category][substitute_part]:
                    new_subs[substitute_category][substitute_part]['flags'] = convert_flag_list(new_subs[substitute_category][substitute_part]['flags'])

            new_substitutes_data[str(BodyType[substitute_category].value)] = new_subs[substitute_category]
        data['substitutes'] = new_substitutes_data

    if 'colors' in data:
        if 'defaults' in data['colors']:
            new_format = []
            for index in data['colors']['defaults']:
                index: str
                new_format.append(ColorIndex[index].value)
            data['colors']['defaults'] = new_format

        if 'overwrites' in data['colors']:
            for color_overwrite in data['colors']['overwrites'].values():
                color_overwrite: dict
                color_overwrite['requires'] = convert_condition(color_overwrite['requires'])

    if 'presets' in data:
        for sim_name, preset_options in data['presets'].items():
            for preset_name, preset in preset_options.items():
                if 'requires' in preset:
                    preset['requires'] = convert_condition(preset['requires'])
                if 'weights' in preset:
                    preset['weights'] = {convert_condition(condition): weight for condition, weight in preset['weights'].items()}

                for form in preset['appearance'].values():
                    new_outfits_data = {}
                    if 'outfits' in form:
                        for outfit_name, outfit in form['outfits'].items():
                            new_outfits_data[outfit_name] = convert_conditions_mapping_lists(outfit)
                        form['outfits'] = new_outfits_data

                    if 'genetics' in form:
                        new_genetics_data = {}
                        if 'parts' in form['genetics']:
                            new_genetics_data['parts'] = convert_conditions_mapping_lists(form['genetics']['parts'])
                        if 'sculpts' in form['genetics']:
                            new_genetics_data['sculpts'] = [hex_to_int(sculpt) for sculpt in form['genetics']['sculpts']]
                        if 'sliders' in form['genetics']:
                            new_genetics_data['sliders'] = {hex_to_int(slider): value for slider, value in form['genetics']['sliders'].items()}
                        if 'body_sliders' in form['genetics']:
                            new_genetics_data['body_sliders'] = {hex_to_int(slider): value for slider, value in form['genetics']['body_sliders'].items()}
                        if 'fit' in form['genetics']:
                            new_genetics_data['fit'] = form['genetics']['fit']
                        if 'fat' in form['genetics']:
                            new_genetics_data['fat'] = form['genetics']['fat']
                        if 'skin_tone' in form['genetics']:
                            new_genetics_data['skin_tone'] = hex_to_int(form['genetics']['skin_tone'])
                        if 'skin_tone_val_shift' in form['genetics']:
                            new_genetics_data['skin_tone_val_shift'] = form['genetics']['skin_tone_val_shift']
                        form['genetics'] = new_genetics_data
    return data


def convert_types_in_list(item_list: [dict], check_installation=False):
    for item in item_list:
        if item is not None:
            convert_types_for_item(item, check_installation)


def convert_types_for_item(item: dict, check_installation=False):
    if 'ids' in item:
        item['ids'] = convert_id_list(item['ids'], check_installation)
        if check_installation and not any(part_id is not None for part_id in item['ids']):
            item['requires'] = "MISC_INVALID"
    if 'requires' in item:
        item['requires'] = convert_condition(item['requires'])
    if 'weights' in item:
        item['weights'] = {convert_condition(condition): weight for condition, weight in item['weights'].items()}
    if 'tags' in item:
        item['tags'] = convert_tag_list(item['tags'])
    if 'flags' in item:
        item['flags'] = convert_flag_list(item['flags'])
    if 'alternatives' in item:
        item['alternatives'] = {convert_condition(condition): alternatives for condition, alternatives in item['alternatives'].items()}
    if 'custom_format' in item:
        new_format = []
        for index in item['custom_format']:
            index: str
            new_format.append(ColorIndex[index].value)
        item['custom_format'] = new_format


def convert_tag_list(tags: [str]):
    new_tags = []
    if tags is None:
        return
    for tag in tags:
        if isinstance(tag, str):
            new_tags.append(check_tag(tag))
        else:
            new_tags.append(tag)
    return remove_duplicates_alt(filter_none(new_tags))


def check_tag(tag: str):
    try:
        if tag.casefold() in FurryTagCondition.custom_tags:
            return FurryTagCondition.custom_tags[tag.casefold()]
        elif tag in FurryTag:
            return FurryTag[tag].value
    except AttributeError:
        pass
    problems.append(f'Unknown tag: {tag}')
    return None


def convert_id_list(ids: [str], check_installation=False):
    new_ids = []
    for part_id in ids:
        if part_id is not None:
            part_id = hex_to_int(part_id)
            if check_installation and not is_part_installed(part_id):
                part_id = None
        new_ids.append(part_id)
    return new_ids


def convert_flag_list(flags: []):
    new_flags = []
    for flag in flags:
        if flag in FurryFlag:
            new_flags.append(FurryFlag[flag].value)

    return new_flags


def convert_condition(condition: str) -> FurryTagCondition:
    try:
        return FurryTagCondition(condition)
    except (ValueError, RecursionError) as e:
        problems.append(str(e))


def convert_conditions_mapping_lists(mapping: {str: []}) -> {FurryTagCondition: [int]}:
    new_mapping = {}
    for condition, items in mapping.items():
        new_condition = convert_condition(condition)
        if new_condition in new_mapping:
            new_mapping[new_condition].extend(convert_id_list(items))
        else:
            new_mapping[new_condition] = convert_id_list(items)

    return new_mapping


def collect_identifiers(data: dict):
    """
    Goes through the data file for any identifier part and saves them in a new entry

    Args:
        data (dict): Data to check though

    Returns:
        dict: The data with collected identifiers
    """
    data['identifiers'] = {}
    data['subidentifiers'] = {}
    if 'parts' in data:
        for body_type in data['parts']:
            if 'part_options' in data['parts'][body_type]:
                for label, part in data['parts'][body_type]['part_options'].items():
                    if 'species' in part:
                        # create dict if needed
                        if body_type not in data['identifiers']:
                            data['identifiers'][body_type] = {'full_parts': {}}

                        data['identifiers'][body_type]['full_parts'][label] = part['species']

                    if 'subspecies' in part:
                        # create dict if needed
                        if body_type not in data['subidentifiers']:
                            data['subidentifiers'][body_type] = {}

                        data['subidentifiers'][body_type][label] = part['subspecies']

    return data


def convert_color_key(data: dict):
    """
    Converts a color key from strings to bools

    Args:
        data (dict): The modified data

    Returns:
        dict: The value of the tag
    """
    converted_key = [[False] * 45 for _ in range(45)]

    for color_block_label, color_block_values in data['colors']['key'].items():
        color_block_label: str
        color_block_values: [str]
        for valid_block in color_block_values:
            valid_block: str
            converted_key[ColorBlock[color_block_label].value][ColorBlock[valid_block].value] = True

    data['colors']['key'] = converted_key

    return data


def print_problems():
    """
    Prints a notification will all the found problems
    """
    message = "Something went wrong loading the furrifier json. You can fix it and reload without restarting the game with the command 'furrifier_reload'. Problems:\n"
    show_notification(message + "\n".join(problems), notif_type="exception", title="Furrifier JSON Error")

    log_location = Path(__file__).resolve().parent.parent / "Furrifier Logs" / "furrifier_parse_error.log"
    print_file(message + "\n".join(problems), str(log_location))


def get_problems():
    return problems


def get_used_addons():
    """
    Returns labels of all addons used

    Returns:
        list of str: The names of the addons
    """
    return used_addons


def print_register_str(print_type=""):
    if print_type == 'parsed':
        string_data = stringify_conditions(load_json(False))

    else:
        # Load custom base file if it exists
        furrifier_dir = Path(__file__).resolve().parent.parent
        custom_base_name = 'furrifier_custom_register.json'
        custom_base_path = os.path.join(furrifier_dir, custom_base_name)

        if os.path.exists(custom_base_path):
            with open(custom_base_path, 'r') as file:
                string_data = json.load(file)
        else:
            # If no custom file exists, use the default
            string_data = copy.deepcopy(default_data)

        # Check for and load addons
        string_data = load_addons(string_data, False)

    json_formatted = substitutions(json.dumps(string_data, indent=4))
    print_file(json_formatted, 'furrifier_current_register.json')
    show_notification("Printed register to file.")


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
