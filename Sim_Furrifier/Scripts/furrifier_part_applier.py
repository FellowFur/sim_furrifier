import bisect
import random
import enum
from copy import copy

from furrifier_sim_info import FurrySimInfo
from furrifier_sim_data_manager import FurrySimDataManager, get_sim_outfits
from furrifier_configs_register_handler import is_furry_part, is_valid_sub_part, get_substitutable_body_types, \
    get_registered_sculpts, get_register_sculpts, get_used_body_types, get_register_skintones_ids, get_label_from_id, get_register_presets
from furrifier_configs_settings_handler import is_setting_on
from furrifier_res_premades import premades_data
from furrifier_utils_basics import is_nude_part, is_part_installed, int_to_hex, hex_to_int, \
    get_sim_name
from furrifier_utils_logger import log_text, change_indent, indent
from furrifier_utils_notifier import show_notification
from objects.components.consumable_component import ConsumableComponent

from protocolbuffers import Outfits_pb2, S4Common_pb2, PersistenceBlobs_pb2
from sims.outfits.outfit_enums import BodyType, OutfitCategory
from sims.occult.occult_enums import OccultType
from cas.cas import get_caspart_bodytype


class SliderType(enum.Int):
    FACE = 1
    BODY = 2


class FurryPartApplier:
    non_genetic_body_types = {BodyType.HAT, BodyType.HAIR, BodyType.FULL_BODY, BodyType.UPPER_BODY, BodyType.LOWER_BODY,
                              BodyType.SHOES, BodyType.CUMMERBUND, BodyType.EARRINGS, BodyType.GLASSES,
                              BodyType.NECKLACE, BodyType.GLOVES, BodyType.WRIST_LEFT, BodyType.WRIST_RIGHT,
                              BodyType.LIP_RING_LEFT, BodyType.LIP_RING_RIGHT, BodyType.NOSE_RING_LEFT,
                              BodyType.NOSE_RING_RIGHT, BodyType.BROW_RING_LEFT, BodyType.BROW_RING_RIGHT,
                              BodyType.INDEX_FINGER_LEFT, BodyType.INDEX_FINGER_RIGHT, BodyType.RING_FINGER_LEFT,
                              BodyType.RING_FINGER_RIGHT, BodyType.MIDDLE_FINGER_LEFT, BodyType.MIDDLE_FINGER_RIGHT,
                              BodyType.LIPS_TICK, BodyType.EYE_SHADOW, BodyType.EYE_LINER, BodyType.BLUSH,
                              BodyType.FACEPAINT, BodyType.SOCKS, 37, BodyType.TIGHTS, BodyType.FINGERNAIL,
                              BodyType.TOENAIL}

    ignored_body_types = {BodyType.FUR_BODY, BodyType.EARS, BodyType.SADDLE, BodyType.BRIDLE,
                          BodyType.REINS, BodyType.BLANKET, BodyType.SKINDETAIL_HOOF_COLOR, BodyType.HAIR_MANE,
                          BodyType.HAIR_TAIL, BodyType.HAIR_FORELOCK, BodyType.HAIR_FEATHERS, BodyType.HORN,
                          BodyType.TAIL_BASE, BodyType.HEAD, BodyType.NONE}

    growable_body_types = {BodyType.FACIAL_HAIR, BodyType.BODYHAIR_ARM, BodyType.BODYHAIR_LEG,
                           BodyType.BODYHAIR_TORSOBACK, BodyType.BODYHAIR_TORSOFRONT}

    def __init__(self, furry_sim_info: FurrySimInfo, data_manager: FurrySimDataManager):
        self.furry_sim_info = furry_sim_info
        self.data_manager = data_manager

    def resend_appearances(self):
        for sim_info in self.furry_sim_info.form_infos.get_editable_infos(self.furry_sim_info.is_disguise):
            sim_info.resend_outfits()
            sim_info.resend_facial_attributes()

    def set_parts(self, part_ids: [int], clear_old=False, force_clear=None, use_special_parts=True, target_outfits=None, update_genetics=True):
        """
        Adds a list of cas_parts to a sim, optionally removing existing furry parts

        Args:
            part_ids (list of int): The ids of the parts to apply
            clear_old (bool): Whether to remove old furry parts
            force_clear (list of int): The body_types to forcibly clear
            use_special_parts (bool): Whether to use removal and substitute parts
            target_outfits (list of int): The ids of outfits to edit
            update_genetics (bool): Whether to update genetics or not
        """

        log_text("Modifying outfits...")
        log_text(f"{len(part_ids)} Parts to apply: {', '.join(int_to_hex(part) for part in part_ids)}")

        # Before applying any parts, loop through the chosen parts and make sure they all exist
        uninstalled_ids = []
        for part_id in part_ids:
            if not is_part_installed(part_id):
                uninstalled_ids.append(part_id)

        if uninstalled_ids:
            self.invalid_parts_warning(uninstalled_ids)
            part_ids = list(set(part_ids) - set(uninstalled_ids))

        body_types = [get_caspart_bodytype(part_id) for part_id in part_ids]
        new_parts = dict(zip(body_types, part_ids))

        # Only cycle through the body types slots that the mod affects
        checked_body_types_master = get_used_body_types()
        if clear_old:
            checked_body_types_master = set(BodyType) - self.ignored_body_types

        # Make sure body types from new parts are always included
        checked_body_types_master.update(body_types)

        # Determine which body type slots need removing
        clearing_body_types = set()
        if force_clear is not None:
            clearing_body_types.update(force_clear)
        checked_body_types_master.update(clearing_body_types)

        # Determine which body type slots need substituting
        substitutable_body_types = []
        if use_special_parts:
            substitutable_body_types = get_substitutable_body_types()
        checked_body_types_master.update(substitutable_body_types)

        # Make sure all body types are ints
        checked_body_types_master = {int(body_type) for body_type in checked_body_types_master}
        substitutable_body_types = {int(body_type) for body_type in substitutable_body_types}
        clearing_body_types = {int(body_type) for body_type in clearing_body_types}

        if not update_genetics:
            checked_body_types_master = checked_body_types_master & self.non_genetic_body_types

        log_text(f"Slots to force delete: {', '.join([BodyType(int(body_type)).name for body_type in clearing_body_types])}")
        log_text(f"Slots to check for substitution: {', '.join([BodyType(int(body_type)).name for body_type in substitutable_body_types])}\n")

        for sim_info in self.furry_sim_info.form_infos.get_editable_infos(self.furry_sim_info.is_disguise):
            # Check mermaid status, if the form is a mermaid form don't add furry legs or tails
            # TODO: Convert this to flags, MERMAID_INVALID flag
            checked_body_types = checked_body_types_master.copy()
            if self.furry_sim_info.form_infos.is_mermaid_info(sim_info):
                if BodyType.SKINDETAIL_MOLE_LIP_LEFT in checked_body_types:
                    checked_body_types.remove(BodyType.SKINDETAIL_MOLE_LIP_LEFT)
                if BodyType.SKINDETAIL_FRECKLES in checked_body_types:
                    checked_body_types.remove(BodyType.SKINDETAIL_FRECKLES)

            # Update the sim's outfits
            # Inspired by Lynire's Unify Hair, Makeup, and Tattoos mod
            # Get sim outfit information
            outfits_msg = Outfits_pb2.OutfitList()
            # noinspection PyProtectedMember
            outfits_msg.ParseFromString(sim_info._base.outfits)

            # Edit all the sim's outfits
            for outfit in outfits_msg.outfits:
                if outfit.outfit_id > 0 and (not target_outfits or outfit.outfit_id in target_outfits):
                    log_text(f"\n")
                    log_text(f"Looking at outfit {outfit.outfit_id} in category {OutfitCategory(int(outfit.category)).name}")
                    self.modify_outfit(outfit, new_parts, checked_body_types, clearing_body_types, substitutable_body_types, clear_old)

            if update_genetics:
                # Also update the sim's genetic info
                # Thanks to Deaderpool for help with this segment
                genetic_msg = Outfits_pb2.GeneticData()
                # noinspection PyProtectedMember
                genetic_msg.ParseFromString(sim_info._base.genetic_data)

                # Only add parts as genetic parts if they belong to genetic slots, growth parts if they are growth parts, etc
                genetic_checked_body_types = list(set(checked_body_types) - FurryPartApplier.non_genetic_body_types)
                growth_checked_body_types = list(set(checked_body_types) & FurryPartApplier.growable_body_types)

                log_text(f"\nModifying growth parts")
                change_indent(1)
                self.modify_genetics(genetic_msg.growth_parts_list.parts, new_parts, growth_checked_body_types, clearing_body_types, substitutable_body_types, clear_old)
                change_indent(-1)

                log_text(f"\nModifying genetic parts")
                change_indent(1)
                self.modify_genetics(genetic_msg.parts_list.parts, new_parts, genetic_checked_body_types, clearing_body_types, substitutable_body_types, clear_old)
                change_indent(-1)

                # Resend the genetic info to the game
                # noinspection PyProtectedMember
                sim_info._base.genetic_data = genetic_msg.SerializeToString()

            # Resend the outfit info to the game
            # noinspection PyProtectedMember
            sim_info._base.outfits = outfits_msg.SerializeToString()

            outfits_msg = Outfits_pb2.OutfitList()
            # noinspection PyProtectedMember
            outfits_msg.ParseFromString(sim_info._base.outfits)

    def set_skin(self, skintone: int, val_shift=0.0):
        if skintone:
            for info in list(self.furry_sim_info.form_infos.get_editable_infos(self.furry_sim_info.is_disguise)):
                log_text(f"Changing skintone from {int_to_hex(info.skin_tone)} to {int_to_hex(skintone)}")
                info.skin_tone = skintone
                info.skin_tone_val_shift = val_shift
        else:
            log_text(f"No skintone to change to.")

    def set_sculpts(self, new_sculpts: [int], clear_old=True, force_delete=None):
        sculpt_categories = get_register_sculpts().keys()
        new_sculpts = set(new_sculpts)

        for info in list(self.furry_sim_info.form_infos.get_editable_infos(self.furry_sim_info.is_disguise)):
            appearance_attributes = PersistenceBlobs_pb2.BlobSimFacialCustomizationData()
            appearance_attributes.ParseFromString(info.facial_attributes)

            # Convert to set to make operations faster, need to un-covert and re-order later
            current_sculpts = set(appearance_attributes.sculpts)

            # Subtract force_deleted sculpts
            if force_delete is not None:
                current_sculpts = current_sculpts - set(force_delete)

            log_text('Modifying Sculpts')
            change_indent(1)

            nl = '\n\t\t'
            log_text(f"Before: {nl}{nl.join([f'{indent()}{int_to_hex(sculpt)}' for sculpt in appearance_attributes.sculpts])}\n")

            # Loop through all sculpt categories
            for sculpt_category in sculpt_categories:
                furry_category_sculpts = get_registered_sculpts([sculpt_category], furry_only=True)
                all_category_sculpts = get_registered_sculpts([sculpt_category], furry_only=False)

                # Check if applying any sculpts from that category
                new_sculpt_for_category = new_sculpts & furry_category_sculpts

                # If applying new sculpts for a category, remove all existing sculpts for that category
                if len(new_sculpt_for_category) > 0:
                    invalid_sculpts = current_sculpts & all_category_sculpts
                    current_sculpts = current_sculpts.difference(invalid_sculpts)

                    log_text(f"Added new sculpt {[int_to_hex(sculpt_id) for sculpt_id in new_sculpt_for_category]} for category {sculpt_category}, removed {[int_to_hex(sculpt_id) for sculpt_id in invalid_sculpts] if invalid_sculpts else 'nothing'}")

                    current_sculpts.update(new_sculpt_for_category)
                # If not, only remove existing furry sculpts for that category if clear_old is True
                elif clear_old:
                    invalid_sculpts = current_sculpts & furry_category_sculpts
                    current_sculpts = current_sculpts.difference(furry_category_sculpts)

                    log_text(f"Added no sculpt for category {sculpt_category}, removed {[int_to_hex(sculpt_id) for sculpt_id in invalid_sculpts] if invalid_sculpts else 'nothing'}")
                # Or, if there are multiple sculpts applied to the category, remove excess sculpts
                elif len(current_sculpts & all_category_sculpts) > 1:
                    current_furry_category_sculpts = current_sculpts & furry_category_sculpts
                    human_category_sculpts = set(get_register_sculpts()[sculpt_category]["vanilla_sculpts"])
                    # If there is a furry sculpt applied, remove all human sculpts and all furry sculpts except one
                    if len(current_furry_category_sculpts) >= 1:
                        excess_furry_sculpts = set(random.sample(current_furry_category_sculpts, len(current_furry_category_sculpts)-1))

                        invalid_sculpts = current_sculpts & (human_category_sculpts | excess_furry_sculpts)
                        current_sculpts = current_sculpts.difference(invalid_sculpts)
                    # Otherwise, remove all but one human sculpts
                    else:
                        current_human_category_sculpts = current_sculpts & human_category_sculpts
                        excess_human_sculpts = set(random.sample(current_human_category_sculpts, len(current_human_category_sculpts)-1))

                        invalid_sculpts = current_sculpts & excess_human_sculpts
                        current_sculpts = current_sculpts.difference(invalid_sculpts)

                    log_text(f"Added no sculpt for category {sculpt_category}, removed {[int_to_hex(sculpt_id) for sculpt_id in invalid_sculpts] if invalid_sculpts else 'nothing'} due to duplication issues")

            # Next, reassert the order of remaining existing sculpts, just in case
            reordered_sculpts = []
            for sculpt in appearance_attributes.sculpts:
                if sculpt in current_sculpts and sculpt not in new_sculpts:
                    # Avoid re-adding duplicates, remove old position and re-add in new position
                    if sculpt in reordered_sculpts:
                        reordered_sculpts.remove(sculpt)

                    reordered_sculpts.append(sculpt)
            # Order of new sculpts doesn't matter, just dump them in
            reordered_sculpts.extend(new_sculpts)

            # Remove old sculpts and dump in new ones
            del appearance_attributes.sculpts[:]
            appearance_attributes.sculpts.extend(reordered_sculpts)

            log_text(f"After: {nl}{nl.join([f'{indent()}{int_to_hex(sculpt)}' for sculpt in appearance_attributes.sculpts])}\n")

            change_indent(-1)

            info.facial_attributes = appearance_attributes.SerializeToString()
            # info.resend_facial_attributes()

    def set_fit(self, fit: float):
        log_text(f"Changing fitness from {self.furry_sim_info.base_sim_info.fit} to {fit}")
        self.furry_sim_info.base_sim_info.commodity_tracker.set_value(ConsumableComponent.FIT_COMMODITY, fit)
        self.furry_sim_info.base_sim_info._set_fit_fat()

    def set_fat(self, fat: float):
        log_text(f"Changing fatness from {self.furry_sim_info.base_sim_info.fat} to {fat}")
        self.furry_sim_info.base_sim_info.commodity_tracker.set_value(ConsumableComponent.FAT_COMMODITY, fat)
        self.furry_sim_info.base_sim_info._set_fit_fat()

    def set_sliders(self, sliders: {int: float}, slider_type):
        for info in list(self.furry_sim_info.form_infos.get_editable_infos(self.furry_sim_info.is_disguise)):
            appearance_attributes = PersistenceBlobs_pb2.BlobSimFacialCustomizationData()
            appearance_attributes.ParseFromString(info.facial_attributes)

            log_text('Modifying Sliders')
            change_indent(1)
            if slider_type == SliderType.FACE:
                self.set_sliders_helper(copy(sliders), appearance_attributes.face_modifiers)
            else:
                self.set_sliders_helper(copy(sliders), appearance_attributes.body_modifiers)
            change_indent(-1)

            log_text('Modifying Aged Sliders')
            change_indent(1)
            if slider_type == SliderType.FACE:
                self.set_sliders_helper(copy(sliders), appearance_attributes.aged_face_modifiers)
            else:
                self.set_sliders_helper(copy(sliders), appearance_attributes.aged_body_modifiers)
            change_indent(-1)

            info.facial_attributes = appearance_attributes.SerializeToString()

    def set_sliders_helper(self, sliders: {int: float}, current_sliders):
        # Modify Existing Sliders
        for slider in current_sliders:
            if slider.key in sliders:
                log_text(f"Modifying slider {int_to_hex(slider.key)} from {slider.amount} to {sliders[slider.key]}")
                slider.amount = sliders[slider.key]
                del sliders[slider.key]

        # Add new Sliders
        for slider_key, slider_amount in sliders.items():
            log_text(f"Adding new slider {int_to_hex(slider_key)} with {slider_amount}")
            new_slider = current_sliders.add()
            new_slider.key = slider_key
            new_slider.amount = slider_amount

    def unfurrify(self, potential_skintones=None):
        # TODO: Add defaults handling
        log_text("Clearing parts")
        self.set_parts([], clear_old=True, use_special_parts=False)

        log_text("Clearing sculpts")
        self.set_sculpts([], clear_old=True)

        if self.furry_sim_info.base_sim_info.skin_tone in get_register_skintones_ids():
            log_text("Resetting skintone")
            if not potential_skintones:
                skintone = (263958, 0.0)
            else:
                skintone = random.choice(potential_skintones)

            self.set_skin(skintone[0], skintone[1])

        self.resend_appearances()

    def modify_outfit(self, outfit, new_parts: dict, checked_body_types: set, clearing_body_types: set, substitutable_body_types: set, clear_old: bool):
        change_indent(1)
        # Get the outfit part lists
        outfit_parts = {
            "part_ids": list(outfit.parts.ids),  # This one has the id's of all the parts used in the outfit
            "body_types": list(outfit.body_types_list.body_types),  # This one has the body type slots of those parts (defined in the BodyType Enum)
            "color_shifts": list(outfit.part_shifts.color_shift),
            "object_ids": list(outfit.object_ids.object_id),
            "layer_ids": (list(outfit.layer_ids.layer_id) if outfit.layer_ids else [0x00000000 * len(outfit.parts.ids)])
        }

        self.clean_outfit(outfit_parts)

        # Check each body type slot worth checking
        for body_type in checked_body_types:
            part_indices = find_outfit_part_indices(outfit_parts, body_type)

            # If adding a type that doesn't exist, add it
            if body_type in new_parts and not part_indices:
                self.add_outfit_part(outfit_parts, body_type, new_parts[body_type])
            # When adding a type that already exists, replace all
            elif body_type in new_parts:
                for index in part_indices:
                    replace_outfit_part(outfit_parts, index, new_parts[body_type], layer_id=outfit_parts["layer_ids"][index])
            # If the type is in the outfit, do more checks
            elif part_indices:
                for index in part_indices:
                    target_part_id = outfit_parts['part_ids'][index]

                    # if a part has a substitute, switch to the substitute
                    if body_type in substitutable_body_types:
                        # check if the specific part has a substitute
                        substitute = self.data_manager.get_substitute_part(target_part_id)

                        if substitute is not None:
                            replace_outfit_part(outfit_parts, index, substitute, rep_type='sub', layer_id=outfit_parts["layer_ids"][index])
                            # move to next part if subbing, we don't want to delete it
                            continue

                    # if the slot is being deleted, delete the slot, or
                    # if clearing old parts, and not replacing an existing part, remove it if it's a furry part
                    # do not delete substitution parts if they are still valid, and do not delete basic nude parts
                    if (body_type in clearing_body_types or (clear_old and is_furry_part(target_part_id))) and (not is_valid_sub_part(target_part_id, self.furry_sim_info.tags) and not is_nude_part(target_part_id)):
                        self.delete_outfit_part(outfit_parts, index)

        change_indent(-1)

        # Add new parts
        outfit.parts = S4Common_pb2.IdList()
        outfit.parts.ids.extend(outfit_parts['part_ids'])

        outfit.body_types_list = Outfits_pb2.BodyTypesList()
        outfit.body_types_list.body_types.extend(outfit_parts['body_types'])

        outfit.part_shifts = Outfits_pb2.ColorShiftList()
        outfit.part_shifts.color_shift.extend(outfit_parts['color_shifts'])

        outfit.object_ids = Outfits_pb2.ObjectIdsList()
        outfit.object_ids.object_id.extend(outfit_parts['object_ids'])

        outfit.layer_ids = Outfits_pb2.LayerIdsList()
        outfit.layer_ids.layer_id.extend(outfit_parts['layer_ids'])

    def modify_genetics(self, genetic_parts: list, new_parts: dict, checked_body_types: list, clearing_body_types: set, substitutable_body_types: set, clear_old: bool):
        parts_str = f"\n{indent()}".join([f"{get_genetic_slot_str(genetic_part)}: {get_part_str(genetic_part.id)}" for genetic_part in genetic_parts])
        log_text(f"Before: \n{indent()}{parts_str}\n")

        clean_genetics(genetic_parts)

        body_types = [part.body_type for part in genetic_parts]
        # Check each body type slot worth checking
        for body_type in checked_body_types:
            part_indices = find_genetic_indices(genetic_parts, body_type)

            # If adding a type that doesn't exist, add it
            if body_type in new_parts and not part_indices:
                add_genetic_part(genetic_parts, body_type, new_parts[body_type])
            # When adding a type that already exists, replace all
            elif body_type in new_parts:
                for index in part_indices:
                    replace_genetic_part(genetic_parts[index], new_parts[body_type], layer_id=genetic_parts[index].layer_id)
            # If the type is in the outfit, do more checks
            elif part_indices:
                for index in part_indices:
                    target_part_id = genetic_parts[index].id

                    # if a part has a substitute, switch to the substitute
                    if str(int(body_type)) in substitutable_body_types:
                        # check if the specific part has a substitute
                        substitute = self.data_manager.get_substitute_part(target_part_id)
                        if substitute is not None:
                            replace_genetic_part(genetic_parts[index], substitute, rep_type='sub', layer_id=genetic_parts[index].layer_id)
                            # move to next part if subbing, we don't want to delete it
                            continue

                    # if the slot is being deleted, delete the slot, or
                    # if clearing old parts, and not replacing an existing part, remove it if it's a furry part
                    # do not delete substitution parts if they are still valid
                    if (body_type in clearing_body_types or (clear_old and is_furry_part(target_part_id))) and not is_valid_sub_part(target_part_id, self.furry_sim_info.tags):
                        # Sub for a deletion part if it exists
                        del_part = self.data_manager.get_deletion_part(int(body_type))
                        if del_part is not None:
                            replace_genetic_part(genetic_parts[index], del_part, rep_type='del', layer_id=genetic_parts[index].layer_id)
                        else:
                            log_text(f"{BodyType(int(body_type)).name}: Part is being deleted, id was {get_part_str(target_part_id)}")
                            del genetic_parts[index]
                            del body_types[index]

        parts_str = "\n\t\t".join([f"{get_genetic_slot_str(genetic_part)}: {get_part_str(genetic_part.id)}" for genetic_part in genetic_parts])
        log_text(f"After: \n{indent()}{parts_str}\n")

    def apply_preset(self, preset_name: str):
        presets = get_register_presets()

        sim_identifier = self.furry_sim_info.premade_identification if self.furry_sim_info.premade_identification else self.furry_sim_info.name

        if sim_identifier not in presets or preset_name not in presets[sim_identifier]:
            if preset_name in presets["GENERIC"]:
                sim_identifier = "GENERIC"
            else:
                raise Exception(f"Preset with name {preset_name} for {sim_identifier} does not exist or is not installed")

        preset = presets[sim_identifier][preset_name]

        # Use default appearance if possible, can only be not compatible if default exists
        default_appearance = dict()
        is_compatible = True
        overwrite = True
        if sim_identifier in premades_data:
            default_appearance = premades_data[self.furry_sim_info.premade_identification]['appearance']
            is_compatible = is_setting_on('preferences', 'compatible_presets')
            overwrite = not is_compatible

        for form_key, form in preset['appearance'].items():
            log_text(f"\nApplying preset to {form_key}")
            change_indent(1)

            self.furry_sim_info.form_infos.set_target_form(OccultType[form_key])
            target_info = next(iter(self.furry_sim_info.form_infos.info_map[OccultType[form_key]]))

            # Filter and apply genetics first
            if 'genetics' in form:
                log_text(f"\nApplying preset genetics")
                change_indent(1)

                genetics = form['genetics']

                # Parts
                if 'parts' in genetics:
                    genetic_parts_sections = genetics['parts'] if ('parts' in genetics and genetics['parts'] is not None) else dict()
                    genetics_parts, genetic_delete_slots = self.filter_parts_sections(genetic_parts_sections)
                    if not is_compatible:
                        genetics_parts = add_default_parts(genetics_parts, genetic_delete_slots, default_appearance[form_key]['genetics']['parts'])
                    if overwrite or not is_compatible:
                        genetic_delete_slots = list(set(BodyType) - {BodyType.TEETH, BodyType.EYECOLOR} - self.non_genetic_body_types - self.ignored_body_types)

                    self.set_parts(genetics_parts, force_clear=genetic_delete_slots, use_special_parts=False, clear_old=overwrite)

                # Sculpts
                if 'sculpts' in genetics:
                    sculpts = [sculpt for sculpt in genetics['sculpts'] if sculpt > 0]
                    remove_sculpts = [sculpt for sculpt in genetics['sculpts'] if sculpt < 0]
                    if not is_compatible:
                        sculpts = add_default_sculpts(sculpts, remove_sculpts, default_appearance[form_key]['genetics']['sculpts'])
                    self.set_sculpts(sculpts, force_delete=remove_sculpts, clear_old=overwrite)

                # Sliders
                if 'sliders' in genetics:
                    sliders = genetics['sliders']
                    if not is_compatible:
                        sliders = add_default_sliders(sliders, default_appearance[form_key]['genetics']['sliders'])
                    self.set_sliders(sliders, SliderType.FACE)
                if 'body_sliders' in genetics:
                    sliders = genetics['body_sliders']
                    if not is_compatible:
                        sliders = add_default_sliders(sliders, default_appearance[form_key]['genetics']['body_sliders'])
                    self.set_sliders(sliders, SliderType.BODY)

                if 'fit' in genetics:
                    self.set_fit(genetics['fit'])
                elif not is_compatible and 'fit' in default_appearance[form_key]['genetics']:
                    self.set_fit(default_appearance[form_key]['genetics']['fit'])

                if 'fat' in genetics:
                    self.set_fat(genetics['fat'])
                elif not is_compatible and 'fat' in default_appearance[form_key]['genetics']:
                    self.set_fat(default_appearance[form_key]['genetics']['fat'])

                if 'skin_tone' and 'skin_tone_val_shift' in genetics:
                    self.set_skin(genetics['skin_tone'], genetics['skin_tone_val_shift'])
                elif 'skin_tone' in genetics:
                    self.set_skin(genetics['skin_tone'])
                elif not is_compatible:
                    self.set_skin(default_appearance[form_key]['genetics']['skin_tone'], default_appearance[form_key]['genetics']['skin_tone_val_shift'])

                change_indent(-1)

            if 'outfits' in form:
                log_text(f"\nApplying preset outfits")
                change_indent(1)
                # Filter and apply outfit parts
                existing_outfits = [f"{outfit[0].name} {outfit[1]}" for outfit in get_sim_outfits(self.furry_sim_info.base_sim_info)]

                # When doing strict, make sure to reset outfits not in the preset
                target_outfits = form['outfits'].copy()
                if not is_compatible:
                    for outfit_name in default_appearance[form_key]["outfits"].keys():
                        if outfit_name not in target_outfits:
                            target_outfits[outfit_name] = {}

                for outfit_name, outfit in target_outfits.items():
                    log_text(f"\nApplying preset to {outfit_name}")
                    outfit_category = OutfitCategory[outfit_name.split()[0].upper()]
                    outfit_slot = int(outfit_name.split()[1])

                    parts, delete_slots = self.filter_parts_sections(outfit)
                    if not is_compatible and outfit_name in default_appearance[form_key]["outfits"]:
                        parts = add_default_parts(parts, delete_slots, default_appearance[form_key]["outfits"][outfit_name])

                    # if target_info.has_outfit(outfit_category, outfit_slot):
                    target_outfit = target_info.get_outfit(outfit_category, outfit_slot)

                    # If didn't previously exist, clear all existing parts
                    if f"{outfit_category.name} {outfit_slot}" not in existing_outfits:
                        log_text("Outfit did not previously exist, creating...")
                        delete_slots = FurryPartApplier.non_genetic_body_types
                    # Or if parts are being added and the outfit doesn't exist by default, clear all existing parts
                    elif default_appearance and outfit_name not in default_appearance[form_key]["outfits"]:
                        log_text("Sim usually doesn't have outfit, clearing...")
                        delete_slots = FurryPartApplier.non_genetic_body_types
                    # Or if strict, clear all existing parts
                    elif overwrite or not is_compatible:
                        delete_slots = FurryPartApplier.non_genetic_body_types

                    self.set_parts(parts, force_clear=delete_slots, update_genetics=False, target_outfits=[target_outfit.outfit_id], use_special_parts=False, clear_old=overwrite)
                change_indent(-1)
            change_indent(-1)

        self.resend_appearances()

    def filter_parts_sections(self, parts_sections: dict) -> ([int], [int]):
        new_parts = []
        delete_slots = []
        for section_condition, section in parts_sections.items():
            if section_condition.passes(self.furry_sim_info.tags):
                for part in section:
                    if part > 0:
                        new_parts.append(part)
                    else:
                        delete_slots.append(get_caspart_bodytype(abs(part)))

        log_text(f"Adding new parts: {[int_to_hex(part) for part in new_parts]}")
        log_text(f"Force clearing: {delete_slots}")
        return new_parts, delete_slots

    def invalid_parts_warning(self, invalid_parts: [int]):
        warning = f"The Sim Furrifier attempted to apply some parts to {get_sim_name(self.furry_sim_info.base_sim_info)} that don't exist, aren't correctly installed, or are otherwise invalid.\n\n"

        vanilla_parts = []
        furry_parts = []
        other_parts = []

        for part in invalid_parts:
            label = get_label_from_id(part)
            if label:
                furry_parts.append(label)
            elif part < 0x0000000100000000:
                vanilla_parts.append(int_to_hex(part))
            else:
                other_parts.append(int_to_hex(part))

        if furry_parts:
            warning += f"Unrecognized furry parts (probably due to missing required CC): {', '.join(part for part in furry_parts)}\n"
        if vanilla_parts:
            warning += f"Unrecognized unmodded parts (probably due to DLC overlap, let FellowFur know about this!): {', '.join(part for part in vanilla_parts)}\n"
        if other_parts:
            warning += f"Unrecognized parts: {', '.join(part for part in other_parts)}"

        show_notification(warning, "Unknown CAS Parts")

    def clean_outfit(self, outfit_parts: dict):
        checked_slots = set()
        duplicate_parts = []

        for i in range(len(outfit_parts['part_ids'])-1, -1, -1):
            slot = (outfit_parts['body_types'][i], outfit_parts['layer_ids'][i])

            if slot in checked_slots:
                duplicate_parts.append(i)
            else:
                checked_slots.add(slot)

        for index in duplicate_parts:
            log_text(f"{get_outfit_slot_str(outfit_parts, index)}: Duplicate part on layer {outfit_parts['layer_ids'][index]}, removing...")
            self.delete_outfit_part(outfit_parts, index, do_subs=False)

    def add_outfit_part(self, outfit_parts: dict, body_type: int, part_id: int, color_shift=0x4000000000000000, object_id=0x0000000000000000, layer_id=0x00000000, outfit_logic=True):
        log_text(f"{BodyType(int(body_type)).name}: Part doesn't exist, adding {int_to_hex(part_id)}")

        bisect.insort(outfit_parts['body_types'], body_type)

        outfit_part_index = outfit_parts['body_types'].index(body_type)

        outfit_parts['part_ids'].insert(outfit_part_index, part_id)
        outfit_parts['color_shifts'].insert(outfit_part_index, color_shift)
        outfit_parts['object_ids'].insert(outfit_part_index, object_id)
        outfit_parts['layer_ids'].insert(outfit_part_index, layer_id)

        if outfit_logic:
            # If adding top or bottom, and full body part exists, fully delete full body and add sub for other
            if body_type in (BodyType.UPPER_BODY, BodyType.LOWER_BODY) and BodyType.FULL_BODY in outfit_parts['body_types']:
                log_text(f"Adding half body outfit, cleaning up full body outfit...")
                change_indent(1)
                full_body_index = outfit_parts['body_types'].index(BodyType.FULL_BODY)
                self.delete_outfit_part(outfit_parts, full_body_index, do_subs=False)

                if body_type == BodyType.UPPER_BODY:
                    del_part_bottom = self.data_manager.get_deletion_part(int(BodyType.LOWER_BODY))
                    if del_part_bottom is not None:
                        self.add_outfit_part(outfit_parts, BodyType.LOWER_BODY, del_part_bottom)
                elif body_type == BodyType.LOWER_BODY:
                    del_part_top = self.data_manager.get_deletion_part(int(BodyType.UPPER_BODY))
                    if del_part_top is not None:
                        self.add_outfit_part(outfit_parts, BodyType.UPPER_BODY, del_part_top)
                change_indent(-1)

            # If adding full body, fully remove top and bottom
            elif body_type == BodyType.FULL_BODY:
                log_text(f"Adding full body outfit, cleaning up half body outfits...")
                change_indent(1)
                if BodyType.UPPER_BODY in outfit_parts['body_types']:
                    upper_body_index = outfit_parts['body_types'].index(BodyType.UPPER_BODY)
                    self.delete_outfit_part(outfit_parts, upper_body_index, do_subs=False)
                if BodyType.LOWER_BODY in outfit_parts['body_types']:
                    lower_body_index = outfit_parts['body_types'].index(BodyType.LOWER_BODY)
                    self.delete_outfit_part(outfit_parts, lower_body_index, do_subs=False)
                change_indent(-1)

    def delete_outfit_part(self, outfit_parts: dict, index: int, do_subs=True):
        body_type = outfit_parts['body_types'][index]
        current_part_str = get_part_str(outfit_parts['part_ids'][index])

        if do_subs and body_type != BodyType.FULL_BODY:
            del_part = self.data_manager.get_deletion_part(int(body_type))
            if del_part is not None:
                replace_outfit_part(outfit_parts, index, del_part, rep_type='del', layer_id=outfit_parts["layer_ids"][index])
                return

        log_text(f"{get_outfit_slot_str(outfit_parts, index)}: Part is being deleted, id was {current_part_str}")

        del outfit_parts['body_types'][index]
        del outfit_parts['part_ids'][index]
        del outfit_parts['color_shifts'][index]
        del outfit_parts['object_ids'][index]
        del outfit_parts['layer_ids'][index]

        if do_subs and body_type == BodyType.FULL_BODY:
            del_part_top = self.data_manager.get_deletion_part(int(BodyType.UPPER_BODY))
            del_part_bottom = self.data_manager.get_deletion_part(int(BodyType.LOWER_BODY))

            if del_part_top is not None and del_part_bottom is not None:
                log_text(f"Deleting full body outfit, substituting half body outfits...")
                change_indent(1)
                self.add_outfit_part(outfit_parts, BodyType.UPPER_BODY, del_part_top, outfit_logic=False)
                self.add_outfit_part(outfit_parts, BodyType.LOWER_BODY, del_part_bottom, outfit_logic=False)
                change_indent(-1)


def find_outfit_part_indices(outfit_parts: dict, body_type: int):
    indices = []
    for i in range(len(outfit_parts['part_ids'])-1, -1, -1):
        if outfit_parts['body_types'][i] == body_type:
            indices.append(i)

    return indices


def replace_outfit_part(outfit_parts: dict, index: int, part_id: int, color_shift=0x4000000000000000, object_id=0x0000000000000000, layer_id=0x00000000, rep_type='rep'):
    current_part_id = outfit_parts['part_ids'][index]
    current_part_str = get_part_str(current_part_id)

    if part_id != current_part_id:
        if rep_type == 'sub':
            log_text(f"{get_outfit_slot_str(outfit_parts, index)}: Part has valid substitute, changing id from {current_part_str} to {int_to_hex(part_id)}")
        elif rep_type == 'del':
            log_text(f"{get_outfit_slot_str(outfit_parts, index)}: Part is being deleted with special part, changing id from {current_part_str} to {int_to_hex(part_id)}")
        else:
            log_text(f"{get_outfit_slot_str(outfit_parts, index)}: Part already exists, changing id from {current_part_str} to {int_to_hex(part_id)}")

        outfit_parts['part_ids'][index] = part_id
        outfit_parts['color_shifts'][index] = color_shift
        outfit_parts['object_ids'][index] = object_id
        outfit_parts['layer_ids'][index] = layer_id
    else:
        log_text(f"{get_outfit_slot_str(outfit_parts, index)}: Replacing part with itself, id still {current_part_str}")


def clean_genetics(genetic_parts: list):
    checked_slots = set()
    duplicate_parts = []

    for i in range(len(genetic_parts)-1, -1, -1):
        slot = (genetic_parts[i].body_type, genetic_parts[i].layer_id)

        if slot in checked_slots:
            duplicate_parts.append(i)
        else:
            checked_slots.add(slot)

    for i in duplicate_parts:
        log_text(f"{get_genetic_slot_str(genetic_parts[i])}: Duplicate part on layer {genetic_parts[i].layer_id}, removing...")
        log_text(f"{get_genetic_slot_str(genetic_parts[i])}: Part is being deleted, id was {get_part_str(genetic_parts[i].id)}")
        del genetic_parts[i]


def find_genetic_indices(genetic_parts: list, body_type: int):
    indices = []
    for i in range(len(genetic_parts)-1, -1, -1):
        if genetic_parts[i].body_type == body_type:
            indices.append(i)

    return indices


def add_genetic_part(genetic_parts: list, body_type: int, part_id: int, color_shift=0x4000000000000000, object_id=0x0000000000000000, layer_id=0x00000000):
    log_text(f"{BodyType(body_type).name}: Part doesn't exist, adding {int_to_hex(part_id)}")

    insert_part_data = Outfits_pb2.PartData()
    insert_part_data.body_type = body_type
    insert_part_data.id = part_id
    insert_part_data.color_shift = color_shift
    insert_part_data.object_id = object_id
    insert_part_data.layer_id = layer_id

    genetic_parts.append(insert_part_data)


def replace_genetic_part(genetic_part, part_id: int, color_shift=0x4000000000000000, object_id=0x0000000000000000, layer_id=0x00000000, rep_type='rep'):
    current_part_id = genetic_part.id
    current_part_str = get_part_str(current_part_id)

    if part_id != current_part_id:
        if rep_type == 'sub':
            log_text(f"{get_genetic_slot_str(genetic_part)}: Part has valid substitute, changing id from {current_part_str} to {int_to_hex(part_id)}")
        elif rep_type == 'del':
            log_text(f"{get_genetic_slot_str(genetic_part)}: Part is being deleted with special part, changing id from {current_part_str} to {int_to_hex(part_id)}")
        else:
            log_text(f"{get_genetic_slot_str(genetic_part)}: Part already exists, changing id from {current_part_str} to {int_to_hex(part_id)}")

        genetic_part.id = part_id
        genetic_part.color_shift = color_shift
        genetic_part.object_id = object_id
        genetic_part.layer_id = layer_id
    else:
        log_text(f"{get_genetic_slot_str(genetic_part)}: Replacing part with itself, id still {current_part_str}")


def get_part_str(part_id: int) -> str:
    if part_id:
        return int_to_hex(part_id)
    else:
        return "UNKNOWN"


def get_outfit_slot_str(outfit_parts, index: int) -> str:
    body_type = outfit_parts['body_types'][index]
    layer = outfit_parts['layer_ids'][index]
    return f"{BodyType(body_type).name}{f' (Layer {layer})' if layer != 0 else ''}"


def get_genetic_slot_str(genetic_part) -> str:
    return f"{BodyType(genetic_part.body_type).name}{f' (Layer {genetic_part.layer_id})' if genetic_part.layer_id != 0 else ''}"


def add_default_parts(parts, delete_slots, default_parts):
    usable_defaults = []

    body_types = [get_caspart_bodytype(part) for part in parts]

    for part in default_parts:
        body_type = get_caspart_bodytype(part)
        if body_type not in body_types and body_type not in delete_slots:
            usable_defaults.append(part)

    log_text(f"Adding in default parts: {[int_to_hex(part) for part in usable_defaults]}")

    parts.extend(usable_defaults)

    return parts


def add_default_sculpts(sculpts, delete_sculpts, default_sculpts):
    final_sculpts = copy(sculpts)
    sculpt_categories = get_register_sculpts().keys()

    # Loop through all sculpt categories
    for sculpt_category in sculpt_categories:
        all_category_sculpts = get_registered_sculpts([sculpt_category], furry_only=False)

        # Only apply a default from a category if there are no new from that category
        if len(set(sculpts) & all_category_sculpts) == 0:
            possible_sculpts = set(default_sculpts) & set(all_category_sculpts)
            for sculpt in possible_sculpts:
                if sculpt not in delete_sculpts:
                    final_sculpts.append(sculpt)

    return final_sculpts


def add_default_sliders(sliders, default_sliders):
    final_sliders = copy(sliders)

    for slider_key, slider_value in default_sliders.items():
        if hex_to_int(slider_key) not in sliders:
            final_sliders[hex_to_int(slider_key)] = slider_value

    return final_sliders

