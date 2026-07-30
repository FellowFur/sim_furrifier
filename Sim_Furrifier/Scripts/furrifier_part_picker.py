from typing import List
import random

from cas.cas import get_caspart_bodytype
from furrifier_sim_info import FurrySimInfo
from furrifier_sim_data_manager import FurrySimDataManager
from furrifier_part_color_picker import pick_colors, pick_valid_pool
from furrifier_configs_register_handler import get_register_parts, get_register_skintones, get_register_sculpts, \
    get_register_colors, get_registered_ids, get_part_from_id, get_label_from_id
from furrifier_utils_basics import get_all_duplicates, int_to_hex, get_body_type, get_format, get_randomizability
from furrifier_utils_weights import weighted_choice
from furrifier_utils_logger import log_parts, log_text, change_indent
from furrifier_utils_enums import FurryTag, FurryFlag


class FurryPartPicker:
    def __init__(self, furry_sim_info: FurrySimInfo, data_manager: FurrySimDataManager):
        self.furry_sim_info = furry_sim_info
        self.data_manager = data_manager

    def choose_parts(self, part_categories=None, extra_parts=None, primary_preferred_parts_lists=None, secondary_preferred_parts_lists=None, genetic_pools=None, random_only=False) -> ([int], {int}):
        if part_categories is None:
            part_categories = list(get_register_parts().keys())
        return choose_parts(self.furry_sim_info.tags, part_categories, extra_parts, primary_preferred_parts_lists, secondary_preferred_parts_lists, genetic_pools, random_only)

    def choose_skintone(self) -> [int]:
        skintone_options_dict = get_register_skintones()
        skintone_id = None

        log_text(f"Choosing skintone: ")
        change_indent(1)

        selected_skintone_key = weighted_choice(skintone_options_dict, self.furry_sim_info.tags)

        # If a skintone was decided, record it
        if selected_skintone_key is not None:
            selected_skintone_value = skintone_options_dict[selected_skintone_key]
            # Add the skintone's tags, if any
            if 'tags' in selected_skintone_value:
                self.furry_sim_info.tags.update(selected_skintone_value['tags'])

            # Add the skintone to the lists of chosen skintones
            if 'ids' in selected_skintone_value:
                skintone_id = random.choice(selected_skintone_value['ids'])

        change_indent(-1)

        return skintone_id

    def choose_sculpts(self, sculpt_categories=get_register_sculpts().keys()) -> [int]:
        sculpts_ids: List[int] = []
        sculpts_data = get_register_sculpts()

        for sculpt_category in sculpt_categories:
            # Get the options for the part for the category
            sculpt_options_dict = sculpts_data[sculpt_category]['sculpt_options']

            log_text(f"Choosing sculpts for category: {sculpt_category}")
            change_indent(1)

            # Make sure options exist
            if sculpt_options_dict is not None:
                selected_sculpt_key = weighted_choice(sculpt_options_dict, self.furry_sim_info.tags)

                # If a sculpt was decided, record it
                if selected_sculpt_key is not None:
                    selected_sculpt_value = sculpt_options_dict[selected_sculpt_key]
                    # Add the sculpt's tags, if any
                    if 'tags' in selected_sculpt_value:
                        self.furry_sim_info.tags.update(selected_sculpt_value['tags'])

                    # Add the sculpt to the lists of chosen sculpts
                    if 'ids' in selected_sculpt_value:
                        sculpts_ids.append(random.choice(selected_sculpt_value['ids']))
            else:
                log_text(f"No valid options exist\n")

            change_indent(-1)

        log_text(f"\nFinal sculpt picks: {[int_to_hex(sculpt_id) for sculpt_id in sculpts_ids]}")

        return sculpts_ids

    def randomize_parts(self) -> ([int], {int}):
        # Figure out what parts are currently equipped and get their full objects
        part_ids = self.data_manager.get_furry_parts()
        body_type_slots = [get_caspart_bodytype(part) for part in part_ids]
        current_furry_parts = []
        current_furry_part_labels = []
        current_furry_parts_ids = []
        current_furry_parts_categories = []
        unused_categories = []

        parts_data = get_register_parts()

        for target_part_category in list(parts_data.keys()):
            if int(target_part_category) in body_type_slots:
                target = part_ids[body_type_slots.index(int(target_part_category))]
                if target in get_registered_ids([target_part_category]):
                    current_part = get_part_from_id(target)
                    if current_part is not None:
                        current_furry_parts.append(current_part)
                        current_furry_part_labels.append(get_label_from_id(target))
                        current_furry_parts_ids.append(target)
                        current_furry_parts_categories.append(get_body_type(target))
            else:
                # Keep track of any categories that aren't currently used, so they can be generated if needed
                unused_categories.append(target_part_category)

        reroll_categories = []
        reroll_swatches = []
        reroll_swatches_labels = []
        re_add_parts = []
        re_add_labels = []
        for idx in range(len(current_furry_parts)):
            current_part = current_furry_parts[idx]
            if 'flags' in current_part and get_randomizability(current_part['flags']) != 0:
                randomizability = get_randomizability(current_part['flags'])
                # If it is only randomizable within itself, have the colors picked again and save its tags
                if randomizability == FurryFlag.RANDOMIZE_COLOR:
                    reroll_swatches.append(current_part)
                    reroll_swatches_labels.append(current_furry_part_labels[idx])
                    if 'tags' in current_part:
                        self.furry_sim_info.tags.update(current_part['tags'])
                # Fully randomizable parts have their entire category picked again
                if randomizability == FurryFlag.RANDOMIZE_PART:
                    reroll_categories.append(current_furry_parts_categories[idx])
            # if it isn't randomizable, collect the tags and add it to the parts to re-add
            else:
                re_add_parts.append(current_furry_parts_ids[idx])
                re_add_labels.append(current_furry_part_labels[idx])
                if 'tags' in current_part:
                    self.furry_sim_info.tags.update(current_part['tags'])

        log_text(f"Randomizing unused categories {[parts_data[part_category]['label'] for part_category in unused_categories]}")
        log_text(f"Randomizing reroll-able categories {[parts_data[part_category]['label'] for part_category in reroll_categories]}")
        log_text(f"Randomizing colors for {reroll_swatches_labels}")
        log_text(f"Retaining {re_add_labels}")

        # Re-roll both re-roll categories and unused categories
        target_categories = unused_categories + reroll_categories

        # Re-order list to follow normal category order
        sorted_categories = sorted(target_categories, key=list(parts_data.keys()).index)

        # Get the new parts to add
        parts, cleared_categories = self.choose_parts(part_categories=sorted_categories, extra_parts=reroll_swatches, random_only=True)

        # Add in the non-randomized parts
        parts += re_add_parts

        # Add the parts to the sim
        return parts, cleared_categories


def choose_parts(tags: {int}, part_categories=get_register_parts().keys(), extra_parts=None, primary_preferred_parts_lists=None, secondary_preferred_parts_lists=None, genetic_pools=None, random_only=False) -> ([int], {int}):
    # Keep track of the randomly decided parts
    colorless_parts_ids: List[int] = []

    colored_part_ids: List[List[int]] = []
    colored_parts_formats: list = []
    colored_parts_pools: list = []

    colored_part_constraints = {pool_key: [] for pool_key in list(get_register_colors()['pools'].keys())}

    parts_data = get_register_parts()

    cleared_categories = set()

    for part_category_key in part_categories:
        selected_part_key = None
        part_options = None

        log_text(f"Choosing parts for {parts_data[part_category_key]['label']} ({part_category_key})")
        change_indent(1)

        # If both category in both preferred parts lists, first try to choose from both
        if primary_preferred_parts_lists is not None and secondary_preferred_parts_lists is not None and part_category_key in primary_preferred_parts_lists and part_category_key in secondary_preferred_parts_lists:

            # Get parts that are in both preferences lists
            preference_intersection_list = get_all_duplicates(primary_preferred_parts_lists[part_category_key],
                                                              secondary_preferred_parts_lists[part_category_key])

            # Convert parts to dict
            part_labels = preference_intersection_list
            part_options = get_part_options(parts_data, part_category_key, part_labels)

            log_text(f"Choosing parts using preferred lists '{primary_preferred_parts_lists['label']}' and '{secondary_preferred_parts_lists['label']}'")
            change_indent(1)

            if 'genetic parts' in primary_preferred_parts_lists['label'] or 'genetic parts' in secondary_preferred_parts_lists['label']:
                selected_part_key = weighted_choice(part_options, tags | {FurryTag.OPERATION_INHERIT}, format_constraints=colored_part_constraints, random_only=random_only)
            else:
                selected_part_key = weighted_choice(part_options, tags, format_constraints=colored_part_constraints, random_only=random_only)

        # Next try just the primary list
        if selected_part_key is None and primary_preferred_parts_lists is not None and part_category_key in primary_preferred_parts_lists:
            # Convert parts to dict
            part_labels = primary_preferred_parts_lists[part_category_key]
            part_options = get_part_options(parts_data, part_category_key, part_labels)

            log_text(f"Choosing parts using primary preferred list '{primary_preferred_parts_lists['label']}'")
            change_indent(1)

            if 'genetic parts' in primary_preferred_parts_lists['label']:
                selected_part_key = weighted_choice(part_options, tags | {FurryTag.OPERATION_INHERIT}, format_constraints=colored_part_constraints, random_only=random_only)
            else:
                selected_part_key = weighted_choice(part_options, tags, format_constraints=colored_part_constraints, random_only=random_only)

        # Next try just the secondary list
        if selected_part_key is None and secondary_preferred_parts_lists is not None and part_category_key in secondary_preferred_parts_lists:
            # Convert parts to dict
            part_labels = secondary_preferred_parts_lists[part_category_key]
            part_options = get_part_options(parts_data, part_category_key, part_labels)

            log_text(f"Choosing parts using secondary preferred list '{secondary_preferred_parts_lists['label']}'")
            change_indent(1)

            if 'genetic parts' in secondary_preferred_parts_lists['label']:
                selected_part_key = weighted_choice(part_options, tags | {FurryTag.OPERATION_INHERIT}, format_constraints=colored_part_constraints, random_only=random_only)
            else:
                selected_part_key = weighted_choice(part_options, tags, format_constraints=colored_part_constraints, random_only=random_only)

        # Finally, try to pick from full list
        if selected_part_key is None:
            log_text(f"Choosing any parts")
            change_indent(1)

            part_options = get_part_options(parts_data, part_category_key)
            selected_part_key = weighted_choice(part_options, tags, format_constraints=colored_part_constraints, random_only=random_only)

        # If a part was decided, record it
        if selected_part_key is not None:
            selected_part_value = part_options[selected_part_key]
            # Add the part's tags, if any
            if 'tags' in selected_part_value:
                tags.update(selected_part_value['tags'])

            # Add the part to the lists of chosen parts and color infos, if part is colored
            if 'ids' in selected_part_value:
                if 'flags' in selected_part_value:
                    color_format = get_format(selected_part_value['flags'])

                    if color_format is not None:
                        colored_part_ids.append(selected_part_value['ids'])

                        # Keep track of color information for color deciding later
                        colored_parts_formats.append(color_format)
                        if 'pools' in selected_part_value:
                            # Assign it to a pool that does not have any incompatible formats in it
                            assigned_pool = pick_valid_pool(selected_part_value, color_format, colored_part_constraints)
                            colored_parts_pools.append(assigned_pool)

                            # Also track in color_constraints
                            colored_part_constraints[assigned_pool].append(color_format)
                            log_text(f"Updated constraints for {assigned_pool}: {colored_part_constraints[assigned_pool]}")
                        else:
                            colored_parts_pools.append(None)
                    else:
                        colorless_parts_ids.append(random.choice(selected_part_value['ids']))
                else:
                    colorless_parts_ids.append(random.choice(selected_part_value['ids']))
            # Handle force clears
            elif selected_part_key == "FORCE_CLEAR":
                cleared_categories.add(part_category_key)
        else:
            log_text(f"No part was decided\n")

        change_indent(0)

    # Add in extra parts that need to have color re-rolled
    if extra_parts is not None:
        log_text(f"Also checking extra parts:")
        for full_part in extra_parts:
            if 'flags' in full_part:
                color_format = get_format(full_part['flags'])

                if color_format is not None:
                    colored_part_ids.append(full_part['ids'])

                    # Keep track of color information for color deciding later
                    colored_parts_formats.append(color_format)
                    if 'pools' in full_part:
                        # Assign it to a pool that does not have any incompatible formats in it
                        assigned_pool = pick_valid_pool(full_part, color_format, colored_part_constraints)
                        colored_parts_pools.append(assigned_pool)

                        # Also track in color_constraints
                        colored_part_constraints[assigned_pool].append(color_format)
                    else:
                        colored_parts_pools.append(None)
                else:
                    colorless_parts_ids.append(random.choice(full_part['ids']))
            else:
                colorless_parts_ids.append(random.choice(full_part['ids']))

    # Send the list of decided colored parts to the color picker to determine what swatches to use
    colored_parts_swatches = pick_colors(colored_part_ids, colored_parts_formats, colored_parts_pools, tags,
                                         genetic_pools=genetic_pools)

    log_text(f"\nFinal part picks:")
    change_indent(1)
    log_parts(colorless_parts_ids + colored_parts_swatches)
    change_indent(-1)
    log_text(f"Final removal picks: {', '.join(cleared_categories)}\n")

    return colorless_parts_ids + colored_parts_swatches, cleared_categories


def get_part_options(parts_data, part_category_key, part_labels=None):
    if 'part_options' in parts_data[part_category_key]:
        if part_labels:
            part_options = {label: parts_data[part_category_key]['part_options'][label] for label in part_labels}
        else:
            part_options = parts_data[part_category_key]['part_options']
    else:
        part_options = dict()

    if 'removal' in parts_data[part_category_key]:
        part_options["FORCE_CLEAR"] = parts_data[part_category_key]['removal']

    return part_options
