from typing import List

from furrifier_configs_register_handler import get_registered_species
from furrifier_part_alternatives import get_alternatives, is_valid_option, is_possible_option
from furrifier_utils_weights import weighted_choice
from furrifier_utils_enums import FurryTag
from furrifier_utils_logger import log_text, change_indent
from furrifier_utils_basics import filter_none
from furrifier_sim_info import FurrySimInfo


class FurrySimSpeciesManager:
    def __init__(self, furry_sim_info: FurrySimInfo):
        self.furry_sim_info = furry_sim_info

    def get_tags_for_species(self, species: str) -> {int}:
        return get_tags_for_species(species, self.furry_sim_info.tags)

    def pick_random_species(self, limited_species=None, inherited=False) -> str:
        if inherited:
            log_text(f"Picking an inheritable species")
            return pick_random_species(self.furry_sim_info.tags | {FurryTag.OPERATION_INHERIT}, limited_species)
        else:
            return pick_random_species(self.furry_sim_info.tags, limited_species)

    def filter_valid_species(self, species_list: List[str]):
        species_data = get_registered_species()
        filtered_species = filter_none(species_list)

        log_text(f"Starting species list: {filtered_species}")

        # Grab alternatives for selected species
        full_species = [species_data[species] for species in filtered_species]
        alternative_species = get_alternatives(full_species, species_data, self.furry_sim_info.tags)

        log_text(f"Expanding species list with alternatives: {alternative_species}")
        filtered_species.extend(alternative_species)

        # Then filter to only valid ones
        valid_species = [species for species in filtered_species if is_valid_option(species_data[species], self.furry_sim_info.tags)]

        log_text(f"Filtered species list: {valid_species}")

        return valid_species

    def has_valid_species(self):
        return has_valid_species(self.furry_sim_info.tags, self.furry_sim_info.is_auto)


def get_tags_for_species(species: str, tags=None) -> {int}:
    log_text(f"Getting species tags for species '{species}'")

    species_data = get_registered_species()
    species = species.lower()

    if species in species_data:
        return species_data[species]['tags']
    elif species == 'random':
        chosen_species_label = pick_random_species(tags)
        return species_data[chosen_species_label]['tags']
    else:
        log_text(f"Species not recognized: '{species}'")
        raise ValueError(f"Species not recognized: '{species}'")


def pick_random_species(tags: {int}, limited_species=None) -> str:
    # If using limited species options, limit the options
    species_data = get_registered_species()
    if limited_species:
        active_species_data = {species_name: species_data[species_name] for species_name in limited_species}
    else:
        active_species_data = species_data

    log_text(f"Choosing Species: ")
    change_indent(1)

    chosen_species_label = weighted_choice(active_species_data, tags)

    change_indent(-1)

    return chosen_species_label


def has_valid_species(tags: {int}, is_auto=False) -> bool:
    for species in get_registered_species().values():
        if is_valid_option(species, tags) and (not is_auto or is_possible_option(species, tags)):
            log_text("Sim has valid species options")
            return True
    return False


def get_species_icon(species: str) -> int:
    species_data = get_registered_species()

    if species in get_registered_species() and 'icon_id' in species_data[species] and species_data[species]['icon_id']:
        return species_data[species]['icon_id']
    else:
        return 0x25eea5cdba6a6fd6
