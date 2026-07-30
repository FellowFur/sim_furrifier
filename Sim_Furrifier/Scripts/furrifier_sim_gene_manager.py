from typing import List

from furrifier_sim_info import FurrySimInfo, get_primary_info
from furrifier_sim_data_manager import FurrySimDataManager, are_sims_probably_identical, is_furry, get_furry_parts, \
    get_missing_body_types, get_sim_existing_tags_from_parts, get_sim_species_from_parts, has_valid_parts
from furrifier_sim_species_manager import FurrySimSpeciesManager, pick_random_species, get_tags_for_species
from furrifier_sim_trait_manager import FurrySimTraitManager, is_exempt
from furrifier_configs_settings_handler import get_preferences, is_setting_on, is_automatic
from furrifier_configs_register_handler import get_registered_species, get_register_parts, get_part_from_id, \
    get_body_type_label
from furrifier_part_alternatives import get_alternatives_label_lists, is_valid_option, get_alternatives
from furrifier_part_picker import FurryPartPicker, choose_parts
from furrifier_part_applier import FurryPartApplier
from furrifier_part_color_picker import get_genetic_pools_from_parts
from furrifier_utils_enums import FurryTag, FurryFlag
from furrifier_utils_basics import remove_duplicates, get_body_type
from furrifier_utils_logger import log_text, log_parts, change_indent, log_tags, close_log
from furrifier_utils_notifier import show_notification

from sims.genealogy_tracker import genealogy_caching
from sims.outfits.outfit_enums import BodyType


class FurrySimGenesManager:
    def __init__(self, furry_sim_info: FurrySimInfo, trait_manager: FurrySimTraitManager, species_manager: FurrySimSpeciesManager, data_manager: FurrySimDataManager, part_picker: FurryPartPicker, part_applier: FurryPartApplier):
        self.furry_sim_info = furry_sim_info

        self.trait_manager = trait_manager
        self.species_manager = species_manager
        self.data_manager = data_manager
        self.part_picker = part_picker
        self.part_applier = part_applier

        self.genetic_parts: List[int] = []
        self.genetic_none_slots: List[str] = []
        self.genetic_species_options: List[str] = []

        self.genetic_human_skintones: List[(int, int)] = []

        self.parents_furry = 0
        self.parents_human = 0
        self.other_furry_relatives = 0
        self.other_human_relatives = 0

        self.is_genetically_identical = False

    def choose_parts_from_genes(self) -> ([int], {str}):
        self.populate_genetic_data()
        log_text(f"Genetic data gathered")

        if not self.is_genetically_identical:
            log_text(f"Sim is not a twin")

            # If a sim has no species from relatives, decide all parts randomly
            if len(self.genetic_species_options) == 0:
                log_text(f"No genetic parts found, using random generation instead")
                self.furry_sim_info.tags.update(self.species_manager.get_tags_for_species(self.species_manager.pick_random_species(())))
                return self.part_picker.choose_parts()

            # If a sim has 1 recognized furry parent, no human parent, and no other furry relatives, invent another parent
            if self.parents_furry == 1 and self.parents_human == 0 and self.other_furry_relatives == 0:
                log_text(f"Only 1 parent found, inventing other parent")
                change_indent(1)

                fake_tags = {FurryTag.OCCULT_HUMAN, FurryTag.GENDER_MALE, FurryTag.FRAME_MASCULINE, FurryTag.STYLE_MASCULINE, FurryTag.HAIR_BLACK, FurryTag.AGE_ADULT, FurryTag.AGE_GROUP_TEEN_UP}

                # Add other tags from preferences
                fake_tags.update(get_preferences())

                fake_species_label = pick_random_species(fake_tags)
                fake_species_tags = get_tags_for_species(fake_species_label, fake_tags)
                fake_tags.update(fake_species_tags)

                # All species/parts from parents are added twice
                self.genetic_species_options.append(fake_species_label)
                self.genetic_species_options.append(fake_species_label)

                log_text("Tags for fake parent:")
                log_tags(fake_tags)

                fake_parts, cleared_categories = choose_parts(fake_tags)

                # All species/parts from parents are added twice to double chance of appearing
                self.genetic_parts.extend(fake_parts)
                self.genetic_parts.extend(fake_parts)
                self.genetic_none_slots.extend(cleared_categories)

                change_indent(-1)

            # Determine what species the sim should be
            species = self.determine_genetic_species()

            # Stop now if sim cannot be properly furrified
            if species == 'potential':
                self.trait_manager.mark_potential_furry()
                if not self.furry_sim_info.is_auto:
                    show_notification(f"Sim {self.furry_sim_info.base_sim_info.first_name} {self.furry_sim_info.base_sim_info.last_name} should be genetically furrified, but doesn't have any valid species options with your settings", title="Cannot Genetically Furrify")
                close_log(f"Sim {self.furry_sim_info.base_sim_info.first_name} {self.furry_sim_info.base_sim_info.last_name} should be genetically furrified, but doesn't have any valid species options with your settings.\nStopping Furrification")
                return None, None
            elif species == 'human':
                self.furry_sim_info.tags.update(self.species_manager.get_tags_for_species(species))
                self.part_applier.unfurrify(self.genetic_human_skintones)

                if not self.furry_sim_info.is_auto:
                    show_notification(f"Sim {self.furry_sim_info.base_sim_info.first_name} {self.furry_sim_info.base_sim_info.last_name} has been genetically chosen to remain human", title="Sim Staying Human")
                close_log(f"Sim {self.furry_sim_info.base_sim_info.first_name} {self.furry_sim_info.base_sim_info.last_name} has been genetically chosen to remain human.\nStopping Furrification")
                return None, None

            # Sims with non-strict genetics don't care about species
            if not is_setting_on('settings', 'strict_genetics'):
                log_text(f"Non-strict genes detected, not using species")
                species = 'chimera'

            self.furry_sim_info.tags.update(self.species_manager.get_tags_for_species(species))

            log_text("\nFull genetic parts options:")
            change_indent(1)
            log_parts(self.genetic_parts)
            change_indent(-1)

            genetic_label_lists = get_alternatives_label_lists(self.genetic_parts, self.genetic_none_slots, self.furry_sim_info.tags | {FurryTag.OPERATION_INHERIT})
            genetic_label_lists['label'] = 'genetic parts'

            # Create a genetic color key from the genetic parts
            genetic_pools = get_genetic_pools_from_parts(self.genetic_parts)

            # FINALLY, get the genetically chosen parts for the sim and return them
            return self.part_picker.choose_parts(primary_preferred_parts_lists=genetic_label_lists, genetic_pools=genetic_pools)
        else:
            log_text(f"Sim is a twin")

            # First, re-pick any parts from the twin/clone that aren't valid for the sim
            invalid_parts, invalid_categories = self.data_manager.get_invalid_parts_and_categories(self.genetic_parts)

            # Sort invalid categories to match register order
            sorted_categories = sorted(invalid_categories, key=list(get_register_parts().keys()).index)

            genetic_label_lists = get_alternatives_label_lists(self.genetic_parts, self.genetic_none_slots, self.furry_sim_info.tags | {FurryTag.OPERATION_INHERIT})
            genetic_label_lists['label'] = 'identical genetic parts'

            # Add all the tags from the twin's parts
            existing_tags = get_sim_existing_tags_from_parts(self.genetic_parts)
            self.furry_sim_info.tags.update(existing_tags)

            # Decide new parts for all the invalid categories
            # TODO: figure out color matching still
            new_part_ids, cleared_categories = self.part_picker.choose_parts(part_categories=sorted_categories, primary_preferred_parts_lists=genetic_label_lists)

            # Merge the twins valid parts into the new parts
            for part in self.genetic_parts:
                if get_body_type(part) not in sorted_categories:
                    new_part_ids.append(part)

            return new_part_ids, cleared_categories

    def choose_age_up_parts(self, part_ids: List[int], species: str, old_tags: {int}):
        # Get parental data sets to reference
        self.populate_genetic_data()

        # Add all the tags from the sim's existing parts
        existing_tags = get_sim_existing_tags_from_parts(part_ids)
        self.furry_sim_info.tags.update(existing_tags)

        # Figure empty part categories
        missing_categories = self.data_manager.get_missing_body_types(part_ids)

        # if not self.is_genetically_identical:
        if True:
            # Change species if necessary
            species_data = get_registered_species()
            change_species = False

            # Changes species if The sim's current species is no longer an option
            if not is_valid_option(species_data[species], self.furry_sim_info.tags) and is_valid_option(species_data, old_tags):
                log_text(f"Old species ({species}) is no longer valid, swapping to a new species")
                change_species = True
            # Or if redo genetics is on, furrifying to a teen, species doesn't match parents, or doesn't match only parent with no source siblings
            if is_setting_on('settings', 'redo_genetics') and \
                    (self.genetic_species_options and species not in self.genetic_species_options) and \
                    (self.parents_furry >= 2 or (self.parents_furry == 1 and self.other_furry_relatives == 0)):
                genetic_alternatives = get_alternatives(self.genetic_species_options, species_data, self.furry_sim_info.tags)
                # TODO bugfixing: This doesn't run if a dog is child of two foxes. Possibly becuase dog is valid alt of fox?
                if species in genetic_alternatives:
                    log_text(f"Species ({species}) doesn't match parents but is among valid alternatives to parent species: {genetic_alternatives}")
                else:
                    log_text(f"Species ({species}) doesn't match parents and is not among valid alternatives to parent species: {genetic_alternatives}")
                    log_text(f"Redoing species to better match parents")
                    change_species = True

            if change_species:
                # If alts fail fallback to genes
                self.furry_sim_info.tags = self.furry_sim_info.tags - set(species_data[species]['tags'])
                new_species = self.determine_genetic_species(species)

                log_text(f"Changed species from {species} to {new_species}")
                species = new_species

                self.furry_sim_info.tags.update(self.species_manager.get_tags_for_species(species))

            # Figure out which parts the sim has that actually need replacing
            invalid_parts, invalid_categories = self.data_manager.get_invalid_parts_and_categories(part_ids, old_tags=old_tags)

            # Potentially re-roll missing categories if new options have opened up
            new_categories = []
            for category in missing_categories:
                if category not in invalid_categories and (has_valid_parts(self.furry_sim_info.tags, category) and not has_valid_parts(old_tags, category)):
                    new_categories.append(category)
            log_text(f"Found new potential categories for sim: {', '.join([f'{get_body_type_label(category)}-{BodyType(int(category)).name}' for category in new_categories])}")
            invalid_categories.extend(new_categories)
            missing_categories = list(set(missing_categories) - set(new_categories))
            self.genetic_none_slots = list(set(self.genetic_none_slots) - set(new_categories))

            # Re-roll missing categories if a parent has a part that is an identifier or has the INHERITANCE_STRONG flag
            important_genetic_categories = []
            for genetic_part_id in self.genetic_parts:
                part_category = get_body_type(genetic_part_id)
                if part_category in missing_categories:
                    full_part = get_part_from_id(genetic_part_id)
                    if full_part and (('species' in full_part and species == full_part['species'])
                    or ('subspecies' in full_part and species in full_part['subspecies'].values())
                    or ('flags' in full_part and FurryFlag.INHERITANCE_STRONG in full_part['flags'])):
                        important_genetic_categories.append(part_category)
            log_text(f"Found new genetically important categories for sim: {', '.join([f'{get_body_type_label(category)}-{BodyType(int(category)).name}' for category in important_genetic_categories])}")
            invalid_categories.extend(important_genetic_categories)
            missing_categories = list(set(missing_categories) - set(important_genetic_categories))
            self.genetic_none_slots = list(set(self.genetic_none_slots) - set(important_genetic_categories))

            # Resort invalid categories to match register order
            invalid_categories = sorted(invalid_categories, key=list(get_register_parts().keys()).index)

            age_up_label_lists = get_alternatives_label_lists(part_ids, missing_categories, self.furry_sim_info.tags)
            genetic_label_lists = get_alternatives_label_lists(self.genetic_parts, self.genetic_none_slots, self.furry_sim_info.tags | {FurryTag.OPERATION_INHERIT})
            age_up_label_lists['label'] = 'age up parts'
            genetic_label_lists['label'] = 'genetic parts'

            if invalid_categories:
                # Decide new parts for all the invalid categories
                new_part_ids, cleared_categories = self.part_picker.choose_parts(part_categories=invalid_categories, primary_preferred_parts_lists=age_up_label_lists, secondary_preferred_parts_lists=genetic_label_lists)

                # Merge the old valid parts into the new parts
                for part_id in part_ids:
                    if get_body_type(part_id) not in invalid_categories:
                        new_part_ids.append(part_id)
            else:
                new_part_ids = []
                cleared_categories = []
        # TODO: Uncomment once twins have been figured out
        # else:
        #     genetic_label_lists['label'] = 'identical genetic parts'
        #
        #     # Decide new parts for all the invalid categories
        #     # TODO: figure out color matching still
        #     new_part_ids, cleared_categories = self.part_picker.choose_parts(part_categories=invalid_categories, primary_preferred_parts_lists=genetic_label_lists, secondary_preferred_parts_lists=age_up_label_lists)

        return new_part_ids, cleared_categories

    def populate_genetic_data(self):
        with genealogy_caching():
            parents = remove_duplicates([rel_info for rel_info in self.furry_sim_info.base_sim_info.genealogy.get_parent_sim_infos_gen()])
            siblings = remove_duplicates([rel_info for rel_info in self.furry_sim_info.base_sim_info.genealogy.get_siblings_sim_infos_gen()])
            children = remove_duplicates([rel_info for rel_info in self.furry_sim_info.base_sim_info.genealogy.get_child_sim_infos_gen()])

            parent_parts: List[int] = []
            other_parts: List[int] = []

            parent_none_slots: List[str] = []
            other_none_slots: List[str] = []

            parent_species: List[str] = []
            other_species: List[str] = []

            parent_human_skintones: List[(int, int)] = []
            other_human_skintones: List[(int, int)] = []

            # First check parents for furryness, and get their parts if they are furry
            for parent in parents:
                log_text(f"\nChecking Parent: {parent.first_name} {parent.last_name}")
                change_indent(1)

                # If they are furry, add their parts
                if is_furry(parent):
                    parental_part_ids = get_furry_parts(get_primary_info(parent, self.furry_sim_info.is_disguise))

                    parental_blank_slots = get_missing_body_types(parental_part_ids)
                    parental_species = get_sim_species_from_parts(parental_part_ids)

                    parent_parts.extend(parental_part_ids)
                    parent_none_slots.extend(parental_blank_slots)
                    if parental_species:
                        parent_species.append(parental_species)
                    self.parents_furry += 1

                # If they aren't furry or human, they should become one of them soon, so incidentally check the grandparents just in case
                elif (not is_exempt(parent)) and is_automatic():
                    furry_grandparents = 0
                    for grandparent in parent.genealogy.get_parent_sim_infos_gen():
                        log_text(f"\nChecking Grandparent: {grandparent.first_name} {grandparent.last_name}")
                        change_indent(1)
                        # If they are furry, add their parts
                        if is_furry(grandparent):
                            grandparent_part_ids = get_furry_parts(get_primary_info(grandparent, self.furry_sim_info.is_disguise))
                            other_parts.extend(grandparent_part_ids)
                            other_none_slots.extend(get_missing_body_types(grandparent_part_ids))

                            grandparent_species = get_sim_species_from_parts(grandparent_part_ids)
                            if grandparent_species:
                                other_species.append(grandparent_species)

                            furry_grandparents += 1
                            if furry_grandparents == 2:
                                self.parents_furry += 1
                        change_indent(-1)

                # If they aren't  furry intentionally, record them as human
                else:
                    # Manual furrifications should not ever pick a human parent
                    if self.furry_sim_info.is_auto:
                        log_text(f"\nParent identified as intentionally human")
                        parent_species.append('human')
                        parent_human_skintones.append((parent.skin_tone, parent.skin_tone_val_shift))
                    self.parents_human += 1

                change_indent(-1)

            # Check siblings and children for parts as well
            for sibling in siblings:
                log_text(f"\nChecking sibling: {sibling.first_name} {sibling.last_name}")
                change_indent(1)

                if is_furry(sibling):
                    sibling_parts = get_furry_parts(get_primary_info(sibling, self.furry_sim_info.is_disguise))
                    sibling_none_slots = get_missing_body_types(sibling_parts)
                    sibling_species = get_sim_species_from_parts(sibling_parts)
                    self.other_furry_relatives += 1

                    # If they are an identical twin, draw only from their parts and species
                    if are_sims_probably_identical(self.furry_sim_info.base_sim_info, sibling):
                        log_text(f"\nSibling identified as twin")
                        self.is_genetically_identical = True
                        return

                    # Check if they are a step-sibling from an un-related furry parent. If they are, remove parts from that parent
                    for parent in sibling.genealogy.get_parent_sim_infos_gen():
                        if is_furry(parent) and parent not in parents:
                            log_text(f"\nChecking step-parent: {parent.first_name} {parent.last_name}")
                            change_indent(1)

                            step_parent_parts = get_furry_parts(get_primary_info(parent, self.furry_sim_info.is_disguise))
                            step_parent_none_slots = get_missing_body_types(step_parent_parts)
                            # ignore stepparent parts the parent also has
                            modified_step_parent_parts = list(set(step_parent_parts) - set(parent_parts))
                            modified_step_parent_none_slots = list(set(step_parent_none_slots) - set(parent_none_slots))

                            sibling_parts = list(set(sibling_parts) - set(modified_step_parent_parts))
                            sibling_none_slots = list(set(sibling_none_slots) - set(modified_step_parent_none_slots))

                            step_parent_species = get_sim_species_from_parts(step_parent_parts)
                            if sibling_species is not None and step_parent_species is not None and set(step_parent_species) == set(sibling_species):
                                sibling_species = None

                            change_indent(-1)

                    # Add the sibling's species as an option if it doesn't come from other parent
                    if sibling_species:
                        other_species.append(sibling_species)

                    other_parts.extend(sibling_parts)
                    other_none_slots.extend(sibling_none_slots)

                elif is_exempt(sibling) or not is_automatic():
                    if self.furry_sim_info.is_auto:
                        log_text(f"\nSibling identified as intentionally human")
                        other_species.append('human')
                        other_human_skintones.append((sibling.skin_tone, sibling.skin_tone_val_shift))
                    self.other_human_relatives += 1

                change_indent(-1)

            for child in children:
                log_text(f"\nChecking child: {child.first_name} {child.last_name}")
                change_indent(1)

                if is_furry(child):
                    child_parts = get_furry_parts(get_primary_info(child, self.furry_sim_info.is_disguise))
                    child_none_slots = get_missing_body_types(child_parts)
                    child_species = get_sim_species_from_parts(child_parts)
                    self.other_furry_relatives += 1

                    # If they are a clone, draw only from their parts and species
                    if are_sims_probably_identical(self.furry_sim_info.base_sim_info, child, match_age=False):
                        log_text(f"\nChild identified as clone")
                        self.is_genetically_identical = True
                        return

                    # Filter out parts from child's other parent
                    for parent in child.genealogy.get_parent_sim_infos_gen():
                        if parent != self.furry_sim_info.base_sim_info and is_furry(parent):
                            log_text(f"\nChecking partner: {parent.first_name} {parent.last_name}")
                            change_indent(1)

                            partner_parts = get_furry_parts(get_primary_info(parent, self.furry_sim_info.is_disguise))
                            partner_none_slots = get_missing_body_types(partner_parts)

                            child_parts = list(set(child_parts) - set(partner_parts))
                            child_none_slots = list(set(child_none_slots) - set(partner_none_slots))

                            partner_species = get_sim_species_from_parts(partner_parts)
                            if child_species is not None and partner_species is not None and set(partner_species) == set(child_species):
                                child_species = None

                            change_indent(-1)

                    # Add the child's species as an option if it doesn't come from other parent
                    if child_species:
                        other_species.append(child_species)

                    other_parts.extend(child_parts)
                    other_none_slots.extend(child_none_slots)

                elif is_exempt(child) or not is_automatic():
                    if self.furry_sim_info.is_auto:
                        log_text(f"\nChild identified as intentionally human")
                        other_species.append('human')
                        other_human_skintones.append((child.skin_tone, child.skin_tone_val_shift))
                    self.other_human_relatives += 1

                change_indent(-1)

            # If two parents found, just use parent parts
            if self.parents_furry + self.parents_human >= 2:
                self.genetic_parts = parent_parts
                self.genetic_none_slots = parent_none_slots
                self.genetic_species_options = parent_species

                self.genetic_human_skintones = parent_human_skintones
            # Merge the parent and other lists, with parent parts duplicated to double their weights
            else:
                self.genetic_parts = remove_duplicates(parent_parts) + remove_duplicates(parent_parts + other_parts)
                self.genetic_none_slots = remove_duplicates(parent_none_slots) + remove_duplicates(parent_none_slots + other_none_slots)
                self.genetic_species_options = remove_duplicates(parent_species) + remove_duplicates(parent_species + other_species)

                self.genetic_human_skintones = remove_duplicates(parent_human_skintones) + remove_duplicates(parent_human_skintones + other_human_skintones)

    def determine_genetic_species(self, species=None):
        # First filter out all species that are not valid for the sim
        log_text(f"\nAttempting to decide genetic species.")
        filtered_genetic_species = self.species_manager.filter_valid_species(self.genetic_species_options)
        log_text(f"Genetic options: {filtered_genetic_species}")

        if species:
            log_text(f"\nComparing alternatives for current species.")
            alternate_species = self.species_manager.filter_valid_species([species])

            overlapping_species = set(filtered_genetic_species) & set(alternate_species)

            # First try to pick a species that is an alt of given species AND match or alt of genetic species
            log_text(f"Checking for valid species alternatives to current that are genetically appropriate: {overlapping_species}")
            if len(overlapping_species) > 0:
                log_text("Found options!")
                return self.species_manager.pick_random_species(limited_species=overlapping_species, inherited=True)
            # Then try to pick an alt of given species
            alternates_to_current_species = set(alternate_species) - {species}
            log_text(f"None found, checking for any valid species alternatives to current: {alternates_to_current_species}")
            if len(alternates_to_current_species) > 0:
                log_text("Found options!")
                return self.species_manager.pick_random_species(limited_species=alternates_to_current_species, inherited=True)

        # Then try to pick alt of genetic species
        log_text(f"Checking for any genetically appropriate species: {filtered_genetic_species}")
        if len(filtered_genetic_species) > 0:
            log_text("Found options!")
            return self.species_manager.pick_random_species(limited_species=filtered_genetic_species, inherited=True)
        # If there are no valid species, but strict genetics are enabled, mark them for later furrification
        elif is_setting_on('settings', 'strict_child_genes'):
            log_text(f"Failed to pick genetic species, marking for retry later...")
            return 'potential'
        # Otherwise give up and just pick any species they can get
        else:
            log_text(f"Failed to pick genetic species, picking at random...")
            return self.species_manager.pick_random_species()
