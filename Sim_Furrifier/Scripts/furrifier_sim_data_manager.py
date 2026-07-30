from typing import List
import services
from cas.cas import get_tags_from_outfit
import random

from furrifier_sim_info import FurrySimInfo, FormInfoCollection
from furrifier_sim_trait_manager import mark_exempt, update_furry_traits, is_exempt
from furrifier_sim_species_manager import get_tags_for_species
from furrifier_configs_register_handler import get_register, get_part_from_id, is_furry_part, get_register_parts, \
    is_preference_part, get_label_from_id, get_register_sculpts, get_registered_sculpts, \
    get_register_special_deletions, get_register_substitutes, get_body_type_label
from furrifier_configs_settings_handler import get_setting_value
from furrifier_utils_basics import get_body_type
from furrifier_utils_weights import get_weight
from furrifier_utils_logger import log_text, log_parts, log_tags, change_indent
from furrifier_part_alternatives import is_valid_option, is_possible_option

from protocolbuffers import Outfits_pb2, PersistenceBlobs_pb2
from sims4.resources import Types
from traits.trait_type import TraitType
from sims.occult.occult_enums import OccultType
from sims.outfits.outfit_enums import BodyType, OutfitCategory
from sims.sim_info_types import Age, Species
from sims.sim_info import SimInfo


class FurrySimDataManager:
    def __init__(self, furry_sim_info: FurrySimInfo):
        self.furry_sim_info = furry_sim_info

    def get_current_parts(self) -> [int]:
        return get_current_parts(self.furry_sim_info.primary_sim_info)

    def get_furry_parts(self) -> [int]:
        return get_furry_parts(self.furry_sim_info.primary_sim_info)

    def get_current_sculpts(self) -> [int]:
        return get_current_sculpts(self.furry_sim_info.primary_sim_info)

    def can_be_furrified(self):
        return can_be_furrified(self.furry_sim_info.base_sim_info, self.furry_sim_info.is_auto,
                                self.furry_sim_info.is_age_up, self.furry_sim_info.is_disguise)

    def has_furry_identifier(self):
        return has_furry_identifier(self.furry_sim_info.base_sim_info)

    def get_sim_species_tags(self) -> {int}:
        return get_sim_species_tags(self.furry_sim_info.base_sim_info)

    def get_sim_existing_tags(self):
        return get_sim_existing_tags(self.furry_sim_info.base_sim_info)

    def get_invalid_parts_and_categories(self, part_ids: List[int], preferred_only=False, old_tags=None) -> ([int], [str]):
        parts_data = get_register_parts()

        invalid_categories: List[str] = []
        invalid_parts: List[int] = []
        need_recheck = True

        # first check for invalid parts
        while need_recheck:
            need_recheck = False
            for idx in range(len(part_ids)):
                full_part = get_part_from_id(part_ids[idx])
                part_category = get_body_type(part_ids[idx])
                # If the part exists, the category isn't already invalid, and the part is invalid, make the category invalid
                if (full_part is not None and part_category not in invalid_categories) and not is_valid_option(full_part, self.furry_sim_info.tags):
                    # If old_tags are provided and the part was also invalid previously, disregard it
                    if old_tags and not is_valid_option(full_part, old_tags):
                        continue

                    # If only checking preferences, skip is part is not preference based
                    if preferred_only and not is_preference_part(full_part):
                        continue

                    # Record part and category
                    invalid_parts.append(part_ids[idx])
                    invalid_categories.append(part_category)

                    # Remove all tags that part added
                    if 'tags' in full_part:
                        self.furry_sim_info.tags.difference_update(full_part['tags'])

                    need_recheck = True

        sorted_categories = sorted(invalid_categories, key=list(parts_data.keys()).index)

        log_text(f"Found new invalid categories for sim: {', '.join([f'{get_body_type_label(category)}-{BodyType(int(category)).name}' for category in sorted_categories])}")
        return invalid_parts, sorted_categories

    def get_missing_body_types(self, part_ids: List[int], preferred_only=False) -> [str]:
        body_types = [get_body_type(part) for part in part_ids]
        parts_data = get_register_parts()

        # then check for missing parts
        missing_body_types = []
        for body_type in parts_data.keys():
            if body_type not in body_types and (not preferred_only or self.are_preference_parts_available(str(body_type))):
                missing_body_types.append(str(body_type))

        log_text(f"Found missing categories for sim: {', '.join([f'{get_body_type_label(category)}-{BodyType(int(category)).name}' for category in missing_body_types])}")

        return missing_body_types

    def get_missing_sculpt_categories(self, sculpts: List[int]) -> [str]:
        sculpts_data = get_register_sculpts()
        sculpts_set = set(sculpts)

        missing_categories = []
        for category in sculpts_data.keys():
            # If a category has no assigned sculpts, check if not having a sculpt for that category is an option
            if len(get_registered_sculpts([category], furry_only=True) & sculpts_set) == 0:
                if any([('ids' in sculpt_option and not get_weight(sculpt_option['weights'],
                                                                   self.furry_sim_info.tags) == 0) for sculpt_option in
                        sculpts_data[category]['sculpt_options'].values()]):
                    missing_categories.append(category)

        return missing_categories

    def are_preference_parts_available(self, body_type: str) -> bool:
        parts_data = get_register_parts()

        if body_type in parts_data.keys() and 'part_options' in parts_data[body_type]:
            for full_part in parts_data[body_type]['part_options'].values():
                if is_preference_part(full_part) and is_possible_option(full_part, self.furry_sim_info.tags):
                    return True
        return False

    def is_furry(self) -> bool:
        return is_furry(self.furry_sim_info.base_sim_info)

    def is_disguised(self) -> bool:
        return is_disguised(self.furry_sim_info.base_sim_info)

    def has_disguise(self) -> bool:
        return has_disguise(self.furry_sim_info.base_sim_info)

    def get_hair_color_index(self, body_type=BodyType.HAIR) -> int:
        # Get the CAS part tags associated with the sim's hair
        (outfit_category, outfit_index) = list(self.furry_sim_info.primary_sim_info.get_all_outfit_entries())[0]
        # noinspection PyProtectedMember
        hair_tags_raw = list(
            get_tags_from_outfit(self.furry_sim_info.base_sim_info._base, outfit_category, outfit_index,
                                 body_type_filter=body_type).values())
        if len(hair_tags_raw) == 0:
            return 0

        hair_tags = set(hair_tags_raw[0])

        if len(hair_tags) == 0:
            return 0

        # Figure out which hair color CAS part tag is in the sim's CAS part tags
        hair_colors = [2528, 131, 133, 2529, 132, 2530, 136, 896, 135, 2531, 2532, 94, 900, 96, 905, 2533, 134, 903, 902, 899, 904, 901, 897, 898]

        for hair_color in hair_colors:
            if hair_color in hair_tags:
                return hair_colors.index(hair_color)

        # If something goes wrong, default to the most neutral hair color
        return 0

    def is_bald(self) -> bool:
        bald_ids = {57926, 51615, 42928, 42934, 51617, 51611, 42929, 280288, 273811, 27057, 27060, 27048, 160849, 310528, 280299, 27050, 280297, 282511, 280298, 280289, 51607, 51620, 57925, 273812, 42931, 51601, 310516, 310526, 310518, 51606, 27054, 27052, 310521, 280300, 51604, 51609, 51602, 51613, 51612, 273808, 160850, 51603, 310525, 310530, 42935, 273810, 310519, 310517, 42930, 310527, 280302, 273813, 282510, 310524, 282515, 280290, 160846, 51610, 51605, 27062, 160851, 27056, 310515, 310529, 51618, 27053, 310523, 282514, 280287, 27049, 27061, 51619, 282513, 280301, 280286, 273809, 280285, 160847, 27059, 310522, 160843, 160844, 27063, 27058, 160845, 27051, 160848, 51614, 42933, 51608, 51621, 282512, 27047}
        return len(set(self.get_current_parts()) & bald_ids) != 0

    def get_substitute_part(self, part_id: int):
        body_type = get_body_type(part_id)
        if body_type in get_register_substitutes():
            for substitute_section in get_register_substitutes()[body_type].values():
                substitute_section: dict
                if part_id in substitute_section['part_options']:
                    if "requires" not in substitute_section or substitute_section["requires"].passes(self.furry_sim_info.tags):
                        return substitute_section['part_options'][part_id]

        return None

    def get_deletion_part(self, body_type: int):
        deletion_options = get_register_special_deletions()
        body_type_str = str(body_type)
        if body_type_str in deletion_options:
            for deletion_option in deletion_options[body_type_str].values():
                deletion_option: dict
                if deletion_option["requires"].passes(self.furry_sim_info.tags):
                    if 'flags' in deletion_option and 'FORMAT_HAIR' in deletion_option['flags']:
                        hair_index = self.get_hair_color_index(body_type)
                        return deletion_option['ids'][hair_index]
                    else:
                        return random.choice(deletion_option['ids'])

        return None


def should_stay_human():
    furrification_roll = random.random() * 100
    is_human = furrification_roll >= int(get_setting_value('settings', 'furrification_chance'))
    log_text(f"Rolled {int(furrification_roll)}/{get_setting_value('settings', 'furrification_chance')}, staying human: {is_human}")
    return is_human


def get_current_parts(primary_info: SimInfo) -> [int]:
    # Get a sample outfit
    (outfit_category, outfit_index) = list(primary_info.get_all_outfit_entries())[0]
    target_outfit = primary_info.get_outfit(outfit_category, outfit_index)

    # Get sim outfit information
    outfits_msg = Outfits_pb2.OutfitList()
    # noinspection PyProtectedMember
    outfits_msg.ParseFromString(primary_info._base.outfits)

    # Match the outfit's id to the full outfit data to get the data of the sample outfit
    for outfit in outfits_msg.outfits:
        if outfit.outfit_id == target_outfit.outfit_id:
            # Get the outfit part lists
            return list(outfit.parts.ids)  # This one has the id's of all the parts used in the outfit


def get_furry_parts(primary_info: SimInfo) -> [int]:
    # Get all the sims parts
    part_ids = get_current_parts(primary_info)

    # Filter out non-furry parts
    part_ids = [part_id for part_id in part_ids if is_furry_part(part_id)]

    log_text("Furry parts on sim:")
    change_indent(1)
    log_parts(part_ids)
    change_indent(-1)

    return part_ids


def get_current_sculpts(primary_info: SimInfo) -> [int]:
    appearance_attributes = PersistenceBlobs_pb2.BlobSimFacialCustomizationData()
    appearance_attributes.ParseFromString(primary_info.facial_attributes)

    return set(appearance_attributes.sculpts)


def can_be_furrified(sim_info: SimInfo, is_auto=False, is_age_up=False, is_disguise=False):
    trait_manager = services.get_instance_manager(Types.TRAIT)
    # Check if not exempt from furrification
    if is_auto and is_exempt(sim_info):
        log_text("Sim is exempt from furrification")
        return False, "Sim is exempt from automatic furrification"
    # And are human
    elif sim_info.species != Species.HUMAN:
        log_text("Sim is not a human!")
        return False, "Target is not a human"
    # And aren't too young
    elif sim_info.age == Age.BABY:
        log_text("Sim is a baby!")
        return False, "Sim is a baby!"
    # And aren't a potential furry, while they are not aging up
    # If aging up, always false
    # If not auto, always false
    # If auto and not aging up, True
    elif (is_auto and not is_age_up and (not is_age_up and is_auto)) and sim_info.has_trait(trait_manager.get(12283065628421974891)):
        log_text("Sim identified is a potential furry and is not aging up")
        return False, "Sim identified is a potential furry and doesn't have furry parts to match their parents yet"
    # And aren't a robot or skeleton (checking code from WW)
    elif any(trait.trait_type == TraitType.ROBOT for trait in sim_info.trait_tracker.equipped_traits):
        log_text("Sim is a robot")
        mark_exempt(sim_info)
        return False, "Sim is a robot"
    elif any(trait.guid64 in [175972, 177810, 178437, 253237] for trait in sim_info.trait_tracker.equipped_traits):
        log_text("Sim identified as a skeleton")
        return False, "Sim is a skeleton"
    # And aren't a Batuu alien
    elif any(trait.trait_type == TraitType.BATUU_ALIEN for trait in sim_info.trait_tracker.equipped_traits):
        log_text("Sim identified as a Batuu alien")
        mark_exempt(sim_info)
        return False, "Sim is a Batuu alien"
    # And aren't a Stormtrooper
    elif sim_info.has_trait(trait_manager.get(233346)):
        log_text("Sim identified as a stormtrooper")
        mark_exempt(sim_info)
        return False, "Sim is a stormtrooper"
    # And aren't Patchy, Trashley, Death, or imaginary friends
    elif any(trait.guid64 in [187088, 395139, 16851, 455630, 455631, 455632, 455633] for trait in sim_info.trait_tracker.equipped_traits):
        log_text("Sim is unique and not furrifiable")
        mark_exempt(sim_info)
        return False, "Sim is unique and not furrifiable"
    # And aren't an alien with a missing true form
    elif (not is_disguise) and sim_info.occult_tracker.has_occult_type(OccultType.ALIEN) and not sim_info.occult_tracker.get_occult_sim_info(OccultType.ALIEN):
        log_text("Could not find alien's alien form")
        return False, "Could not find alien's alien form"
    # And aren't an alien with a missing disguised form
    elif is_disguise and sim_info.occult_tracker.has_occult_type(OccultType.ALIEN) and not sim_info.occult_tracker.get_occult_sim_info(OccultType.HUMAN):
        log_text("Could not find alien's disguise form")
        return False, "Could not find alien's disguise form"
    # Then they can be furrified
    else:
        log_text("Sim can be furrified")
        return True, "Sim can be furrified"


def has_furry_identifier(sim_info: SimInfo, update_if_true=True):
    # Check all forms for identifiers
    for form_info in FormInfoCollection(sim_info).get_all_infos():
        if form_info is not None:
            part_ids = get_furry_parts(form_info)
            species_tags = get_sim_species_tags_from_parts(part_ids)

            # If the sim has an identifiable species, add the trait if missing for easier identification later
            if species_tags is not None:
                if update_if_true:
                    update_furry_traits(sim_info, species_tags)

                return True

    return False


def get_sim_species_tags(sim_info: SimInfo) -> {int}:
    part_ids = get_furry_parts(sim_info)
    return get_sim_species_tags_from_parts(part_ids)


def get_sim_species_tags_from_parts(part_ids: List[int]) -> {int}:
    species_str = get_sim_species_from_parts(part_ids)

    if species_str is not "":
        return get_tags_for_species(species_str)

    return None


def get_sim_species_from_parts(part_ids: List[int]) -> str:
    data = get_register()
    body_types = [get_body_type(part) for part in part_ids]
    labels = [get_label_from_id(part) for part in part_ids]
    species_str = None

    # Check each identifier category, and see if a sim has a part of the same category
    for body_type in data['identifiers']:
        if body_type in body_types:
            target_index = body_types.index(body_type)
            target_label = labels[target_index]

            # First check if there are and full identifier parts, and if the sim has them
            if 'full_parts' in data['identifiers'][body_type] and target_label in data['identifiers'][body_type]['full_parts']:
                species_str = data['identifiers'][body_type]['full_parts'][target_label]
                log_text(f"Sim identified as {species_str} using identifier " + f"({target_label})")
                break

    # Check subidentifiers after identifiers
    if species_str is not None:
        for body_type in data['subidentifiers']:
            if body_type in body_types:
                target_index = body_types.index(body_type)
                target_label = labels[target_index]

                # First check if there are and full identifier parts, and if the sim has them
                if target_label in data['subidentifiers'][body_type] and species_str in \
                        data['subidentifiers'][body_type][target_label]:
                    species_str = data['subidentifiers'][body_type][target_label][species_str]
                    log_text(f"Sim sub-identified as {species_str} using identifier " + f"({target_label})")
                    break

    if species_str is not None:
        return species_str
    else:
        log_text(f"Sim not identified as a furry.")
        return ""


def get_sim_existing_tags(sim_info: SimInfo) -> {int}:
    part_ids = get_furry_parts(sim_info)
    return get_sim_existing_tags_from_parts(part_ids)


def get_sim_existing_tags_from_parts(part_ids: List[int]) -> {int}:
    tags = set()
    identifier_tags = get_sim_species_tags_from_parts(part_ids)
    if identifier_tags is not None:
        tags.update(identifier_tags)

    for idx in range(len(part_ids)):
        part = get_part_from_id(part_ids[idx])
        if part is not None and 'tags' in part:
            tags.update(part['tags'])

    log_text("Found tags for sim:")
    change_indent(1)
    log_tags(tags)
    change_indent(-1)

    return tags


def get_missing_body_types(part_ids: List[int]) -> [str]:
    body_types = [get_body_type(part) for part in part_ids]
    parts_data = get_register_parts()

    # then check for missing parts
    missing_body_types = []
    for body_type in parts_data.keys():
        if body_type not in body_types:
            missing_body_types.append(str(body_type))

    log_text(
        f"Found missing categories for sim: {', '.join([(parts_data[category]['label']) for category in missing_body_types])} ({', '.join([BodyType(int(category)).name for category in missing_body_types])})")

    return missing_body_types


def is_furry(sim_info: SimInfo, update_if_true=True) -> bool:
    trait_manager = services.get_instance_manager(Types.TRAIT)
    furry_trait = trait_manager.get(16979007351164161671)
    scaly_trait = trait_manager.get(10841828803585111305)
    feathery_trait = trait_manager.get(11960148769534105407)
    if sim_info.has_trait(furry_trait) or sim_info.has_trait(scaly_trait) or sim_info.has_trait(feathery_trait):
        log_text("Sim identified as furry")
        return True
    elif sim_info.species == Species.HUMAN:
        return has_furry_identifier(sim_info, update_if_true)
    log_text("Sim is not a furry")
    return False


def is_disguised(sim_info: SimInfo) -> bool:
    return sim_info.occult_tracker.has_occult_type(OccultType.ALIEN) and sim_info.occult_tracker.get_current_occult_types() is OccultType.HUMAN


def has_disguise(sim_info: SimInfo) -> bool:
    return sim_info.occult_tracker.has_occult_type(OccultType.ALIEN)


def get_sim_outfits(sim_info: SimInfo) -> [(OutfitCategory, int, dict)]:
    full_outfits = []

    outfits_msg = Outfits_pb2.OutfitList()
    # noinspection PyProtectedMember
    outfits_msg.ParseFromString(sim_info._base.outfits)
    sim_outfits = outfits_msg.outfits

    outfit_categories = list(sim_info.get_all_outfit_entries())

    for outfit_category, outfit_slot in outfit_categories:
        shallow_outfit = sim_info.get_outfit(outfit_category, outfit_slot)
        for outfit in sim_outfits:
            if outfit.outfit_id == shallow_outfit.outfit_id:
                full_outfits.append((outfit_category, outfit_slot, outfit))
                break

    return full_outfits


def are_sims_probably_identical(sim_info, other_sim_info, match_age=True) -> bool:
    # Code by SonozakiSisters - https://www.patreon.com/posts/twins-mod-1-0-107832232
    if not sim_info.gender == other_sim_info.gender:
        log_text(f"Genetic similarity is invalid due to different sexes")
        return False
    elif match_age and not (sim_info.age == other_sim_info.age):
        log_text(f"Genetic similarity is invalid due to different ages")
        return False

    actor_facial_attributes = PersistenceBlobs_pb2.BlobSimFacialCustomizationData()
    actor_facial_attributes.MergeFromString(sim_info.facial_attributes)
    target_facial_attributes = PersistenceBlobs_pb2.BlobSimFacialCustomizationData()
    target_facial_attributes.MergeFromString(other_sim_info.facial_attributes)
    total_weighted_modifiers = 0
    similar_weighted_modifiers = 0
    for (actor_modifier, target_modifier) in zip(actor_facial_attributes.face_modifiers,
                                                 target_facial_attributes.face_modifiers):
        total_weighted_modifiers += 2
        if abs(actor_modifier.amount - target_modifier.amount) <= 0.4:
            similar_weighted_modifiers += 2
    for (actor_modifier, target_modifier) in zip(actor_facial_attributes.body_modifiers,
                                                 target_facial_attributes.body_modifiers):
        total_weighted_modifiers += 1
        if abs(actor_modifier.amount - target_modifier.amount) <= 0.35:
            similar_weighted_modifiers += 1

    similarity = similar_weighted_modifiers / total_weighted_modifiers
    log_text(f"Genetic similarity is {similarity:.1%}")

    # TODO: this method passes on sims with no actual relation!!
    # return similarity >= 0.75
    return False


def has_valid_parts(tags: {int}, body_type: str) -> bool:
    parts_data = get_register_parts()

    if body_type in parts_data and 'part_options' in parts_data[body_type]:
        for full_part in parts_data[body_type]['part_options'].values():
            if is_possible_option(full_part, tags):
                return True
    return False
