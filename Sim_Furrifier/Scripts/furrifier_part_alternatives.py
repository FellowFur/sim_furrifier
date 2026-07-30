import copy
from collections import defaultdict

from furrifier_utils_weights import get_weight
from furrifier_utils_enums import FurryTag
from furrifier_configs_register_handler import get_register_parts, get_label_from_id, get_part_from_label, get_blank_label_for_body_type
from furrifier_utils_basics import get_body_type
from furrifier_utils_logger import log_text


def get_alternatives_label_lists(part_ids: [int], empty_body_types: [str], tags: {int}) -> {str: {str}}:
    """
    For every given part id, get the actual part, and all its alternatives

    Args:
        part_ids (list of int): The list of part ids to get alternatives for
        empty_body_types (list of str): The empty body types to get the empty parts for
        tags (set of int): The sim's tags

    Returns:
        dict: The dictionary of body_types and their list of equivalents
    """
    parts_data = get_register_parts()

    label_lists = defaultdict(list)
    actual_parts = defaultdict(list)

    # Add actual parts
    for part_id in part_ids:
        category = get_body_type(part_id)
        part_label = get_label_from_id(part_id)
        part = get_part_from_label(part_label, category)

        if part_label is not None:
            # Add part to dict
            label_lists[category].append(part_label)
            actual_parts[category].append(part)

    # Add alternatives
    for category, parts in actual_parts.items():
        label_lists[category].extend(get_alternatives(parts, parts_data[category]['part_options'], tags))

    # Get empty/missing body types
    for empty_body_type in empty_body_types:
        empty_part_label = get_blank_label_for_body_type(empty_body_type)
        if empty_part_label is not None:
            label_lists[empty_body_type].append(empty_part_label)

    return dict(label_lists)


def get_alternatives(options, references: dict, tags: {int}) -> {str}:
    # First get overall validity and possibility
    overall_conditional_tags = copy.copy(tags)
    for option in options:
        if 'requires' in option and not option['requires'].passes(tags):
            overall_conditional_tags.add(FurryTag.CONDITION_NOT_VALID_ALL)
            overall_conditional_tags.add(FurryTag.CONDITION_NOT_POSSIBLE_ALL)
            break
        elif 'weights' in option and get_weight(option['weights'], tags) == 0:
            overall_conditional_tags.add(FurryTag.CONDITION_NOT_POSSIBLE_ALL)

    # Then get alternatives for each option
    alternatives = set()
    for option in options:
        alternatives.update(get_individual_alternatives(option, references, overall_conditional_tags))

    # Redo with more tags if no alternatives found
    redo = False
    if len(alternatives) == 0:
        if FurryTag.CONDITION_NOT_VALID_ALL in overall_conditional_tags:
            overall_conditional_tags.add(FurryTag.CONDITION_NO_VALID_ALTERNATIVES)
            redo = True
        if FurryTag.CONDITION_NOT_POSSIBLE_ALL in overall_conditional_tags:
            overall_conditional_tags.add(FurryTag.CONDITION_NO_POSSIBLE_ALTERNATIVES)
            redo = True
    elif all(not is_possible_option(references[alt], tags) for alt in alternatives) and FurryTag.CONDITION_NOT_POSSIBLE_ALL in overall_conditional_tags:
        overall_conditional_tags.add(FurryTag.CONDITION_NO_POSSIBLE_ALTERNATIVES)
        redo = True

    if redo:
        for option in options:
            alternatives.update(get_individual_alternatives(option, references, overall_conditional_tags))

    return alternatives


def get_individual_alternatives(option: dict, references: dict, tags: {int}, previous_alternatives=None) -> {str}:
    """
    Get all the alternatives for an option

    Returns:
        dict: The full furrifier data register
    """
    if not previous_alternatives:
        previous_alternatives = set()
    alternatives = set()

    if 'alternatives' in option:
        conditional_tags = copy.copy(tags)

        # Get specific validity/possibility
        if not is_valid_option(option, tags):
            conditional_tags.add(FurryTag.CONDITION_NOT_VALID)
            conditional_tags.add(FurryTag.CONDITION_NOT_POSSIBLE)
        elif not is_possible_option(option, tags):
            conditional_tags.add(FurryTag.CONDITION_NOT_POSSIBLE)

        # Get the alternatives
        for alternatives_condition, alternatives_list in option['alternatives'].items():
            if alternatives_condition.passes(conditional_tags):
                for alternative in alternatives_list:
                    alternatives.add(alternative)

                    # Recursively do the alternatives of alternatives
                    if alternative not in previous_alternatives:
                        alternatives.update(get_individual_alternatives(references[alternative], references, tags, alternatives | previous_alternatives))

    return alternatives


# TODO: Expand to ignore preferences
def is_valid_option(option: dict, tags: {int}):
    return 'requires' not in option or option['requires'].passes(tags)


def is_possible_option(option: dict, tags: {int}):
    return is_valid_option(option, tags) and 'weights' in option and get_weight(option['weights'], tags) > 0
