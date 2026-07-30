from typing import Dict

from furrifier_utils_basics import get_body_type
from furrifier_configs_register_parser import load_json

# Always load the json file when the game loads
furrifier_data = load_json(reload=False)


def reload_json():
    """
    Reloads the register from the JSON file after its initial creation
    """
    global furrifier_data
    furrifier_data = load_json(reload=True)


# Gets ids of registered parts for target slots, or all slots
def get_registered_ids(target_body_types=None):
    """
    Gets the ids of registered parts for target body_types, or all body_types

    Args:
        target_body_types (list of str): The body_type to get ids from.

    Returns:
        list of int: The ids for the specified categories.
    """
    if target_body_types is None:
        target_body_types: [str] = list(furrifier_data['parts'].keys())

    ids = set()

    for body_type in target_body_types:
        body_type: str
        if body_type in furrifier_data['parts'] and 'part_options' in furrifier_data['parts'][body_type]:
            # Get all the part ids in a list
            for part in furrifier_data['parts'][body_type]['part_options'].values():
                part: dict
                if part is not None and 'ids' in part:
                    ids.update(part['ids'])

    # Remove None from set, if it exists
    ids = ids - {None}

    return ids


def get_registered_sculpts(target_categories=None, furry_only=True):
    """
    Gets the ids of registered parts for target body_types, or all body_types

    Args:
        target_categories (list of str): The sculpt categories to get ids from.
        furry_only (bool): Whether to get all sculpts or only furry related sculpts

    Returns:
        list of int: The ids for the specified categories.
    """
    if target_categories is None:
        target_categories: [str] = list(furrifier_data['sculpts'].keys())

    ids = set()

    for category in target_categories:
        category: str
        if category in furrifier_data['sculpts']:
            # Get all the part ids in a list
            for sculpt in furrifier_data['sculpts'][category]['sculpt_options'].values():
                sculpt: dict
                if sculpt is not None and 'ids' in sculpt:
                    ids.update(sculpt['ids'])

            # Also add in human sculpts if desired
            if not furry_only and 'vanilla_sculpts' in furrifier_data['sculpts'][category]:
                ids.update(furrifier_data['sculpts'][category]['vanilla_sculpts'])

    # Remove None from set, if it exists
    ids = ids - {None}

    return ids


def get_registered_species(target_categories=None):
    """
    Gets all the species objects for the specified species categories, or all categories

    Args:
        target_categories (list of str): The species categories to get species from.

    Returns:
        dict of dict: The species from the specified categories.
    """
    if target_categories is None:
        target_categories: [str] = list(furrifier_data['species_categories'].keys())

    species = {}

    for category in target_categories:
        category: str
        if category in furrifier_data['species_categories']:
            species.update(furrifier_data['species_categories'][category]['species'])

    return species


def is_furry_part(part_id: int):
    """
    Checks if a part id is in the furry register

    Args:
        part_id (int): The id of the part to test

    Returns:
        bool: Whether the part is a furry part
    """
    body_type = get_body_type(part_id)
    return part_id in get_registered_ids([body_type])


def get_used_body_types():
    """
    Returns all the body_type that are categories in the register

    Returns:
        set of int: The body_types that are categories in the register
    """
    return set(int(body_type) for body_type in list(furrifier_data['parts'].keys()))


def get_substitutable_body_types():
    """
    Get the body type slots that a sim can have substituted

    Returns:
        list of int: The body type slots that can be substituted
    """
    return [int(slot) for slot in list(furrifier_data['substitutes'].keys())]


def get_clearable_body_types():
    return set(int(body_type) for body_type, part_category in furrifier_data['parts'].items() if 'removal' in part_category)


def is_valid_sub_part(part_id: int, tags: {int}):
    """
    Checks if the part id is a substitute part that is valid for the sim

    Args:
        part_id (int): The part id to check
        tags (set of int): The sim's tags

    Returns:
        bool: whether the part is a valid substitute part
    """
    # Check all the substitution parts. If there is a matching id, check the tags
    for substitution_category in furrifier_data['substitutes'].values():
        substitution_category: dict
        for substitution_option in substitution_category.values():
            substitution_option: dict
            if part_id in list(substitution_option['part_options'].values()) and ("requires" not in substitution_option or substitution_option["requires"].passes(tags)):
                return True

    return False


def get_body_type_label(body_type) -> str:
    return furrifier_data['parts'][str(body_type)]['label']


def get_label_from_id(part_id: int):
    """
    Given a part id, return the label of its full part

    Args:
        part_id (int): The part id to check

    Returns:
        str: the label of the full part
    """
    category = get_body_type(part_id)

    if category != "0":
        if category in furrifier_data['parts'] and 'part_options' in furrifier_data['parts'][category]:
            for label, part in furrifier_data['parts'][category]['part_options'].items():
                label: str
                part: dict
                if 'ids' in part and part_id in part['ids']:
                    return label
    else:
        for target_category in get_register_parts().values():
            if 'part_options' in target_category:
                for label, part in target_category['part_options'].items():
                    label: str
                    part: dict
                    if 'ids' in part and part_id in part['ids']:
                        return label

    return None


def get_part_from_id(part_id: int):
    """
    Given a part id, return the part it comes from

    Args:
        part_id (int): The part id to check

    Returns:
        dict: the full part
    """
    category = get_body_type(part_id)

    if category in furrifier_data['parts']:
        for full_part in furrifier_data['parts'][category]['part_options'].values():
            full_part: dict
            if 'ids' in full_part and part_id in full_part['ids']:
                return full_part

    return None


def get_part_from_label(label: str, body_type: str):
    """
    Given a label of a part and its body type, return the part

    Args:
        label (str): The name of the part to find
        body_type (str): The body_type of the part

    Returns:
        dict: the full part
    """
    if body_type in furrifier_data['parts'] and 'part_options' in furrifier_data['parts'][body_type] and label in furrifier_data['parts'][body_type]['part_options']:
        return furrifier_data['parts'][body_type]['part_options'][label]

    return None


def get_age_up_parts_for_part(part: dict, body_type: str):
    """
    Returns all the parts from a part's age_up list

    Args:
        part (dict): The name of the part to find
        body_type (str): The body_type of the part

    Returns:
        dict: the full part
    """
    age_up_parts = {}
    if 'age_up' in part:
        for part_label in part['age_up']:
            part_label: str
            age_up_parts[part_label] = get_part_from_label(part_label, body_type)
    return age_up_parts


def get_blank_part_for_body_type(body_type: str):
    """
    Returns the blank part for a body_type it if it exists

    Args:
        body_type (str): The body_type to check

    Returns:
        dict: the blank part
    """
    if body_type in furrifier_data['parts'] and 'part_options' in furrifier_data['parts'][body_type]:
        return next((part for part in furrifier_data['parts'][body_type]['part_options'].values() if 'ids' not in part), None)


def get_blank_label_for_body_type(body_type: str):
    """
    Returns the label of the blank part for a body_type it if it exists

    Args:
        body_type (str): The body_type to check

    Returns:
        str: the blank part's label
    """
    if body_type in furrifier_data['parts'] and 'part_options' in furrifier_data['parts'][body_type]:
        return next((label for label, part in furrifier_data['parts'][body_type]['part_options'].items() if 'ids' not in part), None)


def is_preference_part(part: dict):
    """
    Checks if a part has any preference based requirements

    Args:
        part (dict): The part to check

    Returns:
        bool: whether the part has preference based requirements
    """
    if 'requires' not in part:
        return False
    else:
        return part['requires'].is_pref_based()


# Returns the category for a sculpt id
def get_sculpt_category(sculpt_id: int):
    """
    Returns the category for a sculpt id

    Args:
        sculpt_id (int): The sculpt id to check

    Returns:
        str: The category of the sculpt
    """
    for category in furrifier_data['sculpts'].keys():
        if sculpt_id in get_registered_sculpts([category], furry_only=False):
            return category
    return None


def get_register():
    """
    Returns the full furrifier data register

    Returns:
        dict: The full furrifier data register
    """
    return furrifier_data


def get_register_parts():
    """
    Returns the furrifier register's parts

    Returns:
        dict: The furrifier's parts
    """
    return furrifier_data['parts']


def get_register_colors():
    """
    Returns the furrifier register's color info

    Returns:
        dict: The furrifier's color info
    """
    return furrifier_data['colors']


def get_register_skintones():
    """
    Returns the furrifier register's skintones

    Returns:
        dict: The furrifier's skintones
    """
    return furrifier_data['skintones']


def get_register_skintones_ids():
    skintones = set()
    for skintone in furrifier_data['skintones'].values():
        skintones.update(skintone['ids'])

    return skintones


def get_register_sculpts():
    """
    Returns the furrifier register's sculpts

    Returns:
        dict: The furrifier's sculpts
    """
    return furrifier_data['sculpts']


def get_register_substitutes() -> Dict:
    return furrifier_data['substitutes']


def get_register_special_deletions() -> Dict:
    return furrifier_data['special_removals']


def get_register_presets() -> Dict:
    return furrifier_data['presets']


def get_register_species_categories():
    """
    Returns the furrifier register species info

    Returns:
        dict: The furrifier's species info
    """
    return furrifier_data['species_categories']


def get_custom_tags():
    """
    Returns the furrifier register's custom tags

    Returns:
        dict: The furrifier's custom tags
    """
    return furrifier_data['custom_tags']
