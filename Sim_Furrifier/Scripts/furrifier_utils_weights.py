import random

from furrifier_part_color_picker import has_valid_pools
from furrifier_utils_enums import FurryFlag
from furrifier_utils_logger import log_options, log_text
from furrifier_utils_basics import get_format, get_randomizability
from furrifier_utils_tag_block import FurryTagCondition


def weighted_choice(option_dict: dict, tags: {int}, log_choice=True, format_constraints=None, random_only=False):
    options_labels = list(option_dict.keys())
    options_values = list(option_dict.values())

    # Split into parallel lists
    options_weight_lists = [option['weights'] if ('weights' in option) else {} for option in options_values]
    options_requirement_lists = [option['requires'] if ('requires' in option) else None for option in options_values]

    # If given format_restraints, check each parts pools and formats and remove incompatible ones
    if format_constraints:
        options_formats = [get_format(option['flags']) if ('flags' in option) else None for option in options_values]
        options_pools_lists = [option['pools'] if ('pools' in option) else None for option in options_values]

        for idx in range(len(options_labels)):
            if options_formats[idx] and options_pools_lists[idx] and not has_valid_pools(options_formats[idx], options_pools_lists[idx], format_constraints):
                options_weight_lists[idx] = {FurryTagCondition("MISC_VALID"): 0}

    # If random only, only randomizable parts can be picked
    if random_only:
        for idx in range(len(options_labels)):
            if 'flags' in options_values[idx] and get_randomizability(options_values[idx]['flags']) != FurryFlag.RANDOMIZE_PART:
                options_weight_lists[idx] = {FurryTagCondition("MISC_VALID"): 0}

    # Determine weights from tags
    options_weights = get_weights(options_weight_lists, tags, requirements_lists=options_requirement_lists)

    # Pick an index from the list, if any have weights > 0
    if sum(options_weights) > 0:
        chosen_label = random.choices(options_labels, weights=options_weights, k=1)[0]
    else:
        chosen_label = None

    # Log if enabled
    if log_choice:
        filtered_indices = [idx for idx in range(len(options_labels)) if ((not options_requirement_lists[idx] or options_requirement_lists[idx].passes(tags)) and options_weight_lists[idx])]
        filtered_list = {options_labels[idx]: options_weights[idx] for idx in filtered_indices}
        log_options(filtered_list)

        if chosen_label is not None:
            log_text(f"Picked choice {chosen_label}\n")
        else:
            log_text(f"Failed to choose anything")

    if chosen_label is not None:
        return chosen_label
    else:
        return None


def get_weights(options_weight_lists: list, tags: {int}, requirements_lists=None):
    """
    Determine the weights of options based on their tags and the sim's tags

    Args:
        options_weight_lists (list of list): The weight lists for each option
        tags (set of int): The sim's tags
        requirements_lists (list of list of int): The requirements for each option

    Returns:
        list of int: The list of weights
    """
    # Create default weights list
    option_weights = [0] * len(options_weight_lists)

    # For every option, check all of its weight tag lists against the sims tags
    for idx, option_weight_dict in enumerate(options_weight_lists):
        # For check that the option passes all requirements
        if not requirements_lists or (requirements_lists and (not requirements_lists[idx] or requirements_lists[idx].passes(tags))):
            # Go through each weight tag list to determine the final weight
            option_weights[idx] = get_weight(option_weight_dict, tags)

    return option_weights


def get_weight(weights_lists: {FurryTagCondition: int}, tags: {int}):
    """
    Determine the final weight for a full weights lists

    Args:
        weights_lists (dict): The weight list for the option
        tags (set of int): The sim's tags

    Returns:
        int: The weight for the option
    """
    final_weight = 0
    for weight_condition, weight in weights_lists.items():
        if weight_condition.passes(tags):
            final_weight = weight
    return final_weight
