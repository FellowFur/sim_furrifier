import copy
import random
from typing import Dict, List

from furrifier_configs_register_handler import get_register_colors, get_part_from_id
from furrifier_utils_enums import FurryTag, ColorFormat, ColorIndex, ColorBlock
from furrifier_utils_basics import is_part_installed, get_format
from furrifier_utils_logger import log_text, change_indent, log_options


def pick_colors(parts_ids: List[List[int]], color_formats: List[int], color_pools: List[str], tags: {int}, genetic_pools=None):
    """
    Given the ids and data of some colored parts, pick the colors they should use

    Args:
        parts_ids (list of list of int): The lists of colored part ids
        color_formats (list of int): the color formats of the lists of colored part ids
        color_pools (list of str): The pool assignment of the lists of colored part ids
        tags (set of int): The sim's tags
        genetic_pools (dict): Has each pool with a list of possible colors for it, inherited from genetics

    Returns:
        list of int: The selected ids for the colored parts
    """
    color_data = get_register_colors()
    adjusted_color_data = adjust_pools(color_data, tags)

    # Determine what colors the parts have available, and which pools are used
    pools_options = get_pool_options(parts_ids, color_formats, color_pools, genetic_pools)

    # Color key keeps track of what color options are still available
    current_color_key = [True] * 125

    # For each color pool, randomly pick an index to use, based on options and weights
    log_text("Picking colors")
    change_indent(1)
    pool_indices = {}
    for color_pool in pools_options.keys():
        color_pool: str
        log_text(f"Picking for pool {color_pool}")
        change_indent(1)
        color_index = pick_color_index(adjusted_color_data, pools_options, color_pool, current_color_key)

        # If something goes wrong, use the default color
        if color_index == -1:
            # Try to find a default color that is valid for the pool, ignoring the color key
            log_text(f"Could not find valid color, checking defaults")
            for default_color in adjusted_color_data['defaults']:
                if pools_options[color_pool][default_color]:
                    color_index = default_color
                    break

        # If still no valid colors are found, pick a random pool-valid color
        if color_index == -1:
            log_text(f"No valid defaults found, picking any random color")
            color_index = pick_color_index(adjusted_color_data, pools_options, color_pool)

        # TODO: add redundancy for genetic inherited colors with no matching parts

        # If not using a random value, modify the color key based on the color's block
        if color_index != -1:
            color_block_index = get_block_index(color_index)
            color_block_key = adjusted_color_data['key'][color_block_index]
            color_full_key = []
            for key_color_block_index in range(len(color_block_key)):
                color_block_length = len(get_indices_for_block(key_color_block_index))
                color_full_key.extend([color_block_key[key_color_block_index]] * color_block_length)
            current_color_key = [a and b for a, b in zip(current_color_key, color_full_key)]

            log_text(f"Updated key to {[ColorIndex(index).name for index in range(len(current_color_key)) if current_color_key[index]]}")
            log_text(f"Picked {color_index} ({ColorIndex(color_index).name})")
        else:
            log_text(f"Picked random color")

        # Record the picked color indices
        pool_indices[color_pool] = color_index

        change_indent(-1)
    change_indent(-1)

    # Get the swatches ids for each part
    # For each part, figure out which pool to draw from and save the id from that pools index
    colored_parts = []
    for idx in range(len(parts_ids)):
        if color_formats[idx] != ColorFormat.HAIR_COLORS:
            color_index = pool_indices[color_pools[idx]]
            colored_parts.append(get_id_for_color(parts_ids[idx], color_formats[idx], color_index))
        # Handle hair formats differently
        else:
            colored_parts.append(parts_ids[idx][get_hair_color_index(tags)])

    # Return the swatches
    return colored_parts


def pick_color_index(color_data: Dict[str, any], pools_options: Dict[str, List[int]], color_pool: str, color_key=None):
    """
    Picks an appropriate and valid index for a color pool. Ignores the color key if it isn't provided.

    Args:
        color_data (dict): The color data from the dictionary
        pools_options (dict): Tracks what colors indices are available for what pools
        color_pool (str): The name of the pool to draw from
        color_key (list of bool): Which colors can be used

    Returns:
        int: The selected index for the colored part
    """
    colors_block_indices_options = []
    colors_block_indices_weights = []

    for block_index in range(45):
        # If the color pool has any options in a block that are also in the color key (if provided), the block is a valid choice
        if any([pools_options[color_pool][subindex] and (color_key is None or color_key[subindex]) for subindex in get_indices_for_block(block_index)]):
            colors_block_indices_options.append(block_index)
            colors_block_indices_weights.append(color_data['pools'][color_pool]['main'][block_index])

    color_index = -1
    while (color_index == -1) and (colors_block_indices_options and sum(colors_block_indices_weights) > 0):
        log_text("Picking block index: ")
        change_indent(1)
        log_options({ColorBlock(colors_block_indices_options[idx]).name: colors_block_indices_weights[idx] for idx in range(len(colors_block_indices_options))})

        # Pick the index of the color block
        color_block_index = random.choices(colors_block_indices_options, weights=colors_block_indices_weights, k=1)[0]

        block_indices_options = get_indices_for_block(color_block_index)

        # If the block has multiple options, pick one using sub-index weights
        if len(block_indices_options) > 1:
            if len(block_indices_options) == 5:
                weights = color_data['pools'][color_pool]['naturals'].copy()
                # For some reason, the natural dirt colors are ordered darkest to lightest, so swap the order around
                if color_block_index == 25:
                    weights = weights[::-1]
            elif len(block_indices_options) == 4:
                weights = color_data['pools'][color_pool]['noodles'].copy()
            else:
                raise NotImplementedError(f"Color block {color_block_index} has multiple unrecognized values")

            # Get all the full indices in the block and test their validity
            for idx in range(len(block_indices_options)):
                if not pools_options[color_pool][block_indices_options[idx]]:
                    weights[idx] = 0

            log_text("Picking sub-block index: ")
            change_indent(1)
            log_options({ColorIndex(block_indices_options[idx]).name: weights[idx] for idx in range(len(block_indices_options))})
            change_indent(-1)

            if sum(weights) == 0:
                log_text("Blocked ended up having no valid options! Oops! Let's try again")
                colors_block_indices_weights[color_block_index] = 0
            else:
                color_index = random.choices(block_indices_options, weights=weights)[0]
        else:
            color_index = block_indices_options[0]
        change_indent(-1)

        return color_index

    return color_index


def get_pool_options(parts_ids: List[List[int]],  color_formats: List[int], color_pools: List[str], genetic_pools: Dict[str, List[int]]):
    """
    Determines what colors are options for each color pool

    Args:
        parts_ids (list of list of int): The list of possible ids for each colored part
        color_formats (list of int): The color formats for each colored part
        color_pools (list of str): The pool assignments of the colored parts
        genetic_pools (dict): Has each pool with a list of possible colors for it, inherited from genetics

    Returns:
        dict: Each pool name with a list of each possible color index it can use
    """
    # First, for each part, determine which colors are options
    parts_color_options: List[List[bool]] = []
    for idx in range(len(parts_ids)):
        parts_color_options.append(get_options_for_format(parts_ids[idx], color_formats[idx]))

    # Then, for each pool, set its options to be what is an option for each part that can draw from it
    color_pools_options = {}
    for pool in list(get_register_colors()['pools'].keys()):
        pool: str

        # If not genetically based, all swatches are an option
        if not genetic_pools:
            color_pools_options[pool] = [True] * 125
        # Otherwise, only the swatches in the genetic pools are an option
        else:
            color_pools_options[pool] = [False] * 125
            for color_index in genetic_pools[pool]:
                color_pools_options[pool][color_index] = True

        # Keep track if the pool is actually used by any parts
        used = False
        # for each part, if it belongs to that pool, reduce the pool's options and mark it as used
        for idx in range(len(color_pools)):
            if color_pools[idx] == pool:
                used = True
                color_pools_options[pool] = [a and b for a, b in zip(color_pools_options[pool], parts_color_options[idx])]

        if not used:
            color_pools_options[pool] = None

    # Remove unused pools
    color_pools_options = {k: v for k, v in color_pools_options.items() if v is not None}

    return color_pools_options


def adjust_pools(color_data: Dict[str, any], tags: {int}):
    """
    Modifies the color data by applying any applicable overwrites

    Args:
        color_data (dict): The unmodified color data
        tags (set of int): The sim's tags

    Returns:
        dict: The new modified color data
    """
    new_color_data = copy.deepcopy(color_data)

    for overwrite_type in list(new_color_data['overwrites'].values()):
        overwrite_type: dict
        if overwrite_type['requires'].passes(tags):
            # If the overwrite can be applied, apply it depending on the type
            for overwrite in list(overwrite_type['overwrite'].keys()):
                for color_pool in (new_color_data['pools'].keys()):
                    if overwrite == 'all' or overwrite == color_pool:
                        for color_pool_section in list(overwrite_type['overwrite'][overwrite].keys()):
                            if overwrite_type['type'] == 'set':
                                new_color_data['pools'][color_pool][color_pool_section] = overwrite_type['overwrite'][overwrite][color_pool_section]
                            elif overwrite_type['type'] == 'add':
                                new_color_data['pools'][color_pool][color_pool_section] = [new_color_data['pools'][color_pool][color_pool_section][i] + overwrite_type['overwrite'][overwrite][color_pool_section][i] for i in range(len(new_color_data['pools'][color_pool][color_pool_section]))]
                            elif overwrite_type['type'] == 'multiply':
                                new_color_data['pools'][color_pool][color_pool_section] = [new_color_data['pools'][color_pool][color_pool_section][i] * overwrite_type['overwrite'][overwrite][color_pool_section][i] for i in range(len(new_color_data['pools'][color_pool][color_pool_section]))]

    log_text("Final Color Pools:")
    for pool in new_color_data['pools'].keys():
        log_text(f"{pool} : {new_color_data['pools'][pool]}")

    return new_color_data


def get_options_for_format(part_ids: List[int], color_format):
    """
    Determines what color indices are valid for a part, based on what ids it has and what its color format is, and what is installed

    Args:
        part_ids (list of int): The colored ids for a part
        color_format: The part's format

    Returns:
        list of bool: The indices that are options
    """
    # Track valid indices from the full format, assume invalid by default
    options = [False] * 125
    # For Custom colors, mark only the given colors as valid, all others as invalid
    if isinstance(color_format, list):
        for idx in range(len(color_format)):
            if part_ids[idx] is not None:
                custom_index = color_format[idx]
                options[custom_index] = True

    # Check every id to see if it exists or not, and what subindices are valid
    elif color_format != ColorFormat.HAIR_COLORS:
        for idx in range(len(part_ids)):
            if part_ids[idx] is not None:
                target_idx = idx
                # Skip Savestate indices if only looking at naturals
                if color_format == ColorFormat.NATURAL_AND_SORA_COLORS:
                    target_idx += 13

                options[target_idx] = True

    return options


def get_block_index(index: int):
    """
    Given the full index of a color, returns the colors block index

    Args:
        index (int): The color's full index

    Returns:
        int: The color's block index
    """
    if index <= 12:
        return index
    elif index <= 27:
        return ((index-13)//5)+13
    elif index <= 32:
        return index-12
    elif index <= 57:
        return ((index-33)//5)+21
    elif index <= 60:
        return index-32
    elif index <= 124:
        return ((index-61)//4)+29
    else:
        raise Exception(f"Index {index} does not have an equivalent block index.")


def get_indices_for_block(block_index: int):
    """
    Given the block index of a color, returns the full indices of all colors in that block

    Args:
        block_index (int): The color's block index

    Returns:
        list of int: The full indices in the color block
    """
    if 0 <= block_index <= 12:
        return [block_index]
    elif 13 <= block_index <= 15:
        block_start = ((block_index-13)*5)+13
        return list(range(block_start, block_start+5))
    elif 16 <= block_index <= 20:
        return [block_index+12]
    elif 21 <= block_index <= 25:
        block_start = ((block_index - 21) * 5) + 33
        return list(range(block_start, block_start+5))
    elif 26 <= block_index <= 28:
        return [block_index + 32]
    elif 29 <= block_index <= 44:
        block_start = ((block_index - 29) * 4) + 61
        return list(range(block_start, block_start+4))
    else:
        raise Exception(f"Index {block_index} doesn't belong to a block")


def get_color_indices_range(color_index: int, color_range: int):
    """
    Given a color index and a range, returns all color indices in the same block within the range

    Args:
        color_index (int): A full color index
        color_range (int): The size of the range to get colors from

    Returns:
        list of int: The full indices in the same color block within the range
    """
    block_indices = get_indices_for_block(get_block_index(color_index))

    index_in_block = block_indices.index(color_index)
    colors_in_range: List[int] = []

    for value in range(index_in_block-color_range, index_in_block+color_range+1):
        if 0 <= value < len(block_indices):
            colors_in_range.append(block_indices[value])

    return colors_in_range


def get_hair_color_index(tags: {int}):
    """
    Returns the index that matches a sim's hair color

    Args:
        tags (set of int): The sim's tags

    Returns:
        int: The index of the sim's hair color
    """
    hair_colors = [
        FurryTag.HAIR_NEUTRAL_BLACK,
        FurryTag.HAIR_BLACK,
        FurryTag.HAIR_DARK_BROWN,
        FurryTag.HAIR_WARM_BROWN,
        FurryTag.HAIR_BROWN,
        FurryTag.HAIR_LIGHT_BROWN,
        FurryTag.HAIR_RED,
        FurryTag.HAIR_AUBURN,
        FurryTag.HAIR_ORANGE,
        FurryTag.HAIR_NEUTRAL_BLONDE,
        FurryTag.HAIR_LIGHT_BLONDE,
        FurryTag.HAIR_BLONDE,
        FurryTag.HAIR_DIRTY_BLONDE,
        FurryTag.HAIR_PLATINUM,
        FurryTag.HAIR_WHITE,
        FurryTag.HAIR_WHITE_BLONDE,
        FurryTag.HAIR_GRAY,
        FurryTag.HAIR_PURPLE_PASTEL,
        FurryTag.HAIR_HOT_PINK,
        FurryTag.HAIR_DARK_BLUE,
        FurryTag.HAIR_TURQUOISE,
        FurryTag.HAIR_GREEN,
        FurryTag.HAIR_BLACK_SALT_AND_PEPPER,
        FurryTag.HAIR_BROWN_SALT_AND_PEPPER
    ]

    for idx in range(len(hair_colors)):
        if hair_colors[idx] in tags:
            return idx

    raise Exception(f"Sim has no identified hair color.")


def get_color_of_part(part_id: int):
    """
    Returns the full color index of a given part

    Args:
        part_id (int): The id of the part

    Returns:
        int: The part's full color index
    """
    full_part = get_part_from_id(part_id)

    if 'custom_format' in full_part:
        return full_part['custom_format'][full_part['ids'].index(part_id)]
    elif 'flags' in full_part:
        part_format = get_format(full_part['flags'])
        if part_format == ColorFormat.FULL_COLORS or part_format == ColorFormat.SAVESTATE_COLORS:
            return full_part['ids'].index(part_id)
        elif part_format == ColorFormat.NATURAL_AND_SORA_COLORS:
            return full_part['ids'].index(part_id) + 13

    return None


def get_id_for_color(part_ids: [int], color_format, color_index: int):
    """
    Given a list of ids, a format, and a color index, return the correct id for the color

    Args:
        part_ids (list of int): The id of the part
        color_format: The format of the part
        color_index (int): The color index to get

    Returns:
        int: The part's id
    """
    if color_index != -1:
        # Handle special formats if needed
        if color_format == ColorFormat.NATURAL_AND_SORA_COLORS:
            color_index = color_index - 13
        elif isinstance(color_format, list):
            color_index = color_format.index(color_index)

        # Get the swatch that matches the index
        if len(part_ids) > color_index:
            return part_ids[color_index]
        else:
            return None
    else:
        # If pool didn't work, just pick a completely random part from the parts that are installed
        return random.choice([part_id for part_id in part_ids if (part_id is not None and is_part_installed(part_id))])


def pick_valid_pool(full_part: Dict[str, any], color_format: int, format_constraints: Dict[str, List[int]]):
    possible_pools: List[str] = []
    possible_pool_weights: List[int] = []

    backup_possible_pools: List[str] = []
    backup_possible_pool_weights: List[int] = []

    used_pools = get_used_pools(format_constraints)

    for idx in range(len(full_part['pools'])):
        if full_part['pools'][idx].startswith('!'):
            if (full_part['pools'][idx][1:] in used_pools) and are_formats_compatible(color_format, format_constraints[full_part['pools'][idx][1:]]):
                possible_pools.append(full_part['pools'][idx][1:])
                if 'pool_weights' in full_part:
                    possible_pool_weights.append(full_part['pool_weights'][idx])
        elif full_part['pools'][idx].startswith('?'):
            if are_formats_compatible(color_format, format_constraints[full_part['pools'][idx][1:]]):
                backup_possible_pools.append(full_part['pools'][idx][1:])
                if 'pool_weights' in full_part:
                    backup_possible_pool_weights.append(full_part['pool_weights'][idx])
        elif are_formats_compatible(color_format, format_constraints[full_part['pools'][idx]]):
            possible_pools.append(full_part['pools'][idx])
            if 'pool_weights' in full_part:
                possible_pool_weights.append(full_part['pool_weights'][idx])

    if not possible_pools:
        possible_pools = backup_possible_pools
        possible_pool_weights = backup_possible_pool_weights

    if not possible_pools:
        log_text("No valid color pools for part, something went wrong")
        return None

    log_text(f"Picking color pool for part from options: {', '.join(possible_pools)}.")

    if possible_pool_weights:
        chosen_pool = random.choices(possible_pools, weights=possible_pool_weights, k=1)[0]
    else:
        chosen_pool = random.choice(possible_pools)

    log_text(f"Picked {chosen_pool} for color pool.\n")

    return chosen_pool


def has_valid_pools(color_format, pools: List[str], format_constraints: Dict[str, List[int]]):
    """
    Checks if any of the given pools are compatible with the given format given the format_constraints

    Args:
        color_format: The part's color format
        pools (list of str): The pools to check
        format_constraints (dict): The available pools and what formats are drawing from them already

    Returns:
        bool: Whether any pools are compatible with the format
    """
    used_pools = get_used_pools(format_constraints)

    for pool in pools:
        if pool.startswith('!'):
            if pool[1:] in used_pools and are_formats_compatible(color_format, format_constraints[pool[1:]]):
                return True
        elif pool.startswith('?'):
            if are_formats_compatible(color_format, format_constraints[pool[1:]]):
                return True
        elif are_formats_compatible(color_format, format_constraints[pool]):
            return True

    return False


def get_used_pools(format_constraints: Dict[str, List[int]]):
    """
    Determines what pools are currently used, based on the format constraints

    Args:
        format_constraints (dict): The available pools and what formats are drawing from them already

    Returns:
        list of str: The pools that are currently used
    """
    return [pool_key for pool_key in list(format_constraints.keys()) if format_constraints[pool_key]]


def are_formats_compatible(color_format: int, format_list: list):
    # Check non-custom compatibility
    if color_format == ColorFormat.SAVESTATE_COLORS and ColorFormat.NATURAL_AND_SORA_COLORS in format_list:
        return False
    if color_format == ColorFormat.NATURAL_AND_SORA_COLORS and ColorFormat.SAVESTATE_COLORS in format_list:
        return False

    # Check compatibility with custom format
    if isinstance(color_format, list):
        if ColorFormat.SAVESTATE_COLORS in format_list and not any(0 <= idx <= 12 for idx in color_format):
            return False
        if ColorFormat.NATURAL_AND_SORA_COLORS in format_list and not any(13 <= idx <= 60 for idx in color_format):
            return False
        for test_format in format_list:
            if isinstance(test_format, list) and not set(color_format) & set(test_format):
                return False

    # Check compatibility with custom formats in list
    for test_format in format_list:
        if isinstance(test_format, list):
            if color_format == ColorFormat.SAVESTATE_COLORS and not any(0 <= idx <= 12 for idx in test_format):
                return False
            if color_format == ColorFormat.NATURAL_AND_SORA_COLORS and not any(13 <= idx <= 60 for idx in test_format):
                return False

    return True


def get_genetic_pools_from_parts(part_ids: List[int]):
    """
    Given a list of parts, construct a genetic pool

    Args:
        part_ids (list of int): The part ids to construct the pool from

    Returns:
        dict: The genetic pool
    """
    color_data = get_register_colors()

    genetic_pool = {key: set() for key in list(color_data['pools'].keys())}
    secondary_genetic_pool = []

    for part_id in part_ids:
        full_part = get_part_from_id(part_id)
        if 'pools' in full_part:
            part_color_index = get_color_of_part(part_id)
            part_color_range_indices = get_color_indices_range(part_color_index, 1)
            part_color_pool_options = full_part['pools']

            # Remove all the ! and ? from the parts pools
            for idx in range(len(part_color_pool_options)):
                if part_color_pool_options[idx].startswith('!') or part_color_pool_options[idx].startswith('?'):
                    part_color_pool_options[idx] = part_color_pool_options[idx][1:]

            # If a single pool choice, add all colors in the part's color range to that pool's options
            if len(part_color_pool_options) == 1:
                genetic_pool[part_color_pool_options[0]].update(part_color_range_indices)
            # Otherwise, track it
            else:
                secondary_genetic_pool.append({'pools': part_color_pool_options, 'colors': part_color_range_indices})

    # Any parts with multiple pool options, whose color options do not match any of their pools, get their color options added to all pool options
    for secondary_option in secondary_genetic_pool:
        has_match = False
        for pool in secondary_option['pools']:
            for color in secondary_option['colors']:
                if color in genetic_pool[pool]:
                    has_match = True
                    break
            if has_match:
                break

        if not has_match:
            for pool in secondary_option['pools']:
                genetic_pool[pool].update(secondary_option['colors'])

    log_text("Constructed genetic color pool: ")
    change_indent(1)
    for pool_label, pool_options in genetic_pool.items():
        log_text(f"{pool_label}: {[ColorIndex(index).name for index in pool_options]}")
    change_indent(-1)

    return genetic_pool
