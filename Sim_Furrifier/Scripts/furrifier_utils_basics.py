import os

import services
from interactions.context import InteractionContext
from interactions.priority import Priority
from cas.cas import get_caspart_bodytype
from pathlib import Path
import re
import linecache

from furrifier_utils_enums import ColorFormat


def flatten(x: list):
    """
    Flattens a list

    Args:
        x (list): The list to flatten

    Returns:
        list: The flattened list
    """
    if isinstance(x, list) and not isinstance(x, str):
        return [a for i in x for a in flatten(i)]
    else:
        return [x]


def filter_none(x: list):
    """
    Filters out None values from a list

    Args:
        x (list): The list to filter

    Returns:
        list: The filtered list
    """
    return list(filter(lambda item: item is not None, x))


def first_real(x: list):
    """
    Returns the first value from a list that isn't none, or None if all items are none

    Args:
        x (list): The list to find a value from

    Returns:
        any: The first real value
    """
    for item in x:
        if item is not None:
            return item
    return None


def are_equal(str1: str, str2: str):
    return str(str1).casefold() == str(str2).casefold()


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


def hex_to_int(x: str):
    """
    Converts a hex values to an int value

    Args:
        x (str): The value to convert

    Returns:
        int: The converted value
    """
    if isinstance(x, int):
        return x
    elif x.startswith('-'):
        return -int(x[1:], 16)
    else:
        return int(x, 16)


def get_all_duplicates(x: list, y: list):
    """
    Returns a list of all the values shared between two lists
    If either list has duplicate values within itself, it returns that value multiple times

    Args:
        x (list): The first list to check
        y (list): The second list to check

    Returns:
        list: The values in both lists
    """
    new_list = []
    for value in x:
        if value in y and value not in new_list:
            new_list.extend([value] * max(x.count(value), y.count(value)))
    return new_list


def remove_duplicates(target_list: list):
    """
    Removes all duplicates from a list

    Args:
        target_list (list): The list to filter

    Returns:
        list: The filtered list
    """
    return list(set(target_list))


def remove_duplicates_alt(target_list: list):
    # Removes duplicates while maintaining order and allowing nested lists
    result = []
    for item in target_list:
        if item not in result:
            result.append(item)
    return result


def run_interaction(interaction_id: int, sim):
    """
    Runs the specified interaction on the specified sim

    Args:
        interaction_id (int): The id of the interaction to run
        sim (Sim): The sim to run the interaction on
    """
    affordance_manager = services.affordance_manager()
    si = affordance_manager.get(interaction_id)
    context = InteractionContext(sim, InteractionContext.SOURCE_SCRIPT, Priority.High)
    sim.push_super_affordance(si, sim, context)


def is_nude_part(part_id: int):
    """
    Converts a hex values to an int value

    Args:
        part_id (int): The part to check

    Returns:
        bool: Whether the part is a nude part
    """
    nude_parts = [6562, 6540, 6544, 6574]
    return part_id in nude_parts


def get_format(flags: [int]):
    try:
        for flag in flags:
            if flag < 10:
                return ColorFormat(flag)
    except (Exception, ):
        pass

    return None


def get_randomizability(flags: [int]) -> int:
    try:
        for flag in flags:
            if flag == 11 or flag == 12:
                return flag
    except (Exception, ):
        pass

    return 0


# Returns the category of a part
def get_body_type(part_id: int):
    """
    Return the body_type a part id belongs to

    Args:
        part_id (int): The id of the part to test

    Returns:
        str: The body_type of the part
    """
    if part_id is None:
        return None
    else:
        try:
            return str(int(get_caspart_bodytype(part_id)))
        except (Exception,):
            return None


def is_part_installed(part_id: int):
    try:
        if isinstance(part_id, str):
            return get_caspart_bodytype(hex_to_int(part_id)) > 0
        else:
            return get_caspart_bodytype(int(part_id)) > 0
    except (Exception,):
        return False


def is_any_part_installed(part_ids: [int]):
    return any(is_part_installed(part_id) for part_id in part_ids)


def format_exception(text: str):
    """
    Cleans the full file paths out of exceptions

    Args:
        text (str): The text to format

    Returns:
        str: The formatted text
    """
    exception = ""
    lines = text.splitlines()
    for line in lines:
        exception += re.sub(r'File ".*[\\/]([^\\/]+.py)"', r'File "\1"', line) + "\n"

    return exception


def print_file(text: str, filepath: str):
    """
    Prints a message to a given file path

    Args:
        text (str): The text to print
        filepath (str): The name or path of the file
    """
    directory = Path(__file__).resolve().parent.parent
    file_path = directory/filepath
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w') as f:
        f.write(text)


def get_sim_name(sim_info) -> str:
    sim_name = ""
    if sim_info.first_name:
        sim_name += sim_info.first_name.strip()
        if sim_info.last_name and sim_info.last_name != "!":
            sim_name += f" {sim_info.last_name.strip()}"
    elif sim_info.last_name:
        sim_name += sim_info.last_name.strip()
    elif sim_info.full_name:
        sim_name += sim_info.full_name.strip()
    else:
        return "INVALID"

    return sim_name.strip()


def get_mod_dir() -> Path:
    # furrifier_dir = Path(__file__).resolve().parent
    # if furrifier_dir.parent.name.casefold() == "Mods".casefold():
    #     return furrifier_dir.parent.resolve()
    # elif furrifier_dir.parent.parent.name.casefold() == "Mods".casefold():
    #     return furrifier_dir.parent.parent.resolve()
    # elif furrifier_dir.parent.parent.parent.name.casefold() == "Mods".casefold():
    #     return furrifier_dir.parent.parent.parent.resolve()
    # else:
    #     # Give up and just return the parent dir of the furrifier
    #     return furrifier_dir.parent.resolve()
    # From Wicked Whims
    file_path = os.path.normpath(os.path.dirname(os.path.realpath(__file__))).replace(os.sep, '/')
    lowercase_file_path_segments = file_path.lower().split('/')
    file_path_segments = file_path.split('/')
    root_segment_index = lowercase_file_path_segments.index('mods')
    root_dir = os.sep.join(file_path_segments[:root_segment_index]) + os.sep
    mods_dir_path = '{}Mods{}'.format(root_dir, os.sep)
    return Path(mods_dir_path)


def get_game_version() -> str:
    try:
        sims_dir = get_mod_dir().parent.resolve()
        config_line = linecache.getline(str(sims_dir/"Config.log"), 3)

        if not config_line:
            return ''

        version = config_line.lstrip("Version:").strip()
        return version

    except (FileNotFoundError, ValueError):
        return ''


def is_game_version_valid(expected_version: str, found_version: str) -> bool:
    expected_segments = expected_version.split('.')
    found_segments = found_version.split('.')

    for i in range(3):
        if int(found_segments[i]) < int(expected_segments[i]):
            return False
        elif int(found_segments[i]) != int(expected_segments[i]):
            break

    return True
