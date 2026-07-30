import json
import os
import services
import traceback
from pathlib import Path

from furrifier_sim_data_manager import get_furry_parts, get_sim_species_from_parts, get_sim_outfits
from furrifier_utils_basics import get_sim_name, int_to_hex
from furrifier_configs_register_parser import substitutions
from furrifier_res_premades import premades_data
from furrifier_part_applier import FurryPartApplier
from furrifier_utils_enums import expected_json_version

import sims4.commands
from cas.cas import get_caspart_bodytype
from sims4.resources import Types
from protocolbuffers import PersistenceBlobs_pb2
from sims.outfits.outfit_enums import BodyType, OutfitCategory
from sims.occult.occult_enums import OccultType
from sims.sim_info_types import Species, Age

log_path = os.path.join(Path(__file__).resolve().parent.parent, "preset_export_log.log")
export_location = Path(__file__).resolve().parent.parent


def log_text(text: str):
    with open(log_path, 'a') as f:
        f.write(f"{text}\n")


age_translator = {
    Age.BABY: "AGE_BABY",
    Age.INFANT: "AGE_INFANT",
    Age.TODDLER: "AGE_TODDLER",
    Age.CHILD: "AGE_CHILD",
    Age.TEEN: "AGE_GROUP_TEEN_UP",
    Age.YOUNGADULT: "AGE_GROUP_TEEN_UP",
    Age.ADULT: "AGE_GROUP_TEEN_UP",
    Age.ELDER: "AGE_GROUP_TEEN_UP"
}


@sims4.commands.Command('create_preset', command_type=sims4.commands.CommandType.Live)
def create_preset(*args, _connection=None):
    output = sims4.commands.CheatOutput(_connection)
    try:
        # Process input
        if len(args) == 0:
            output("Please provide a a name for the sim's preset")
            return
        elif len(args) == 1:
            client = services.client_manager().get_first_client()
            sim_info = client.active_sim.sim_info
            preset_name = args[0]
        elif len(args) == 2:
            output("Input invalid. Please provide either just a preset name (surrounded by \") or a sim name, then the preset name.")
            return
        elif len(args) == 3:
            first_name = args[1]
            last_name = args[2]
            sim_info = services.sim_info_manager().get_sim_info_by_name(first_name, last_name)
            preset_name = args[0]
        else:
            output("Input invalid. Please provide either just a preset name (surrounded by \") or a sim name, then the preset name.")
            return

        if sim_info is None:
            output("Target sim not found")
            return
        elif get_sim_name(sim_info) not in set(premades_data.keys()):
            output("Sim isn't a recognized premade sim, they might not be premade or just new sims that haven't be registered yet")
            output("A preset will still be generated, but may lack some features")

        with open(log_path, 'w') as f:
            f.write(f"Starting...\n")

        output("Starting...")

        # Save all sim's appearance
        output("Saving appearance data...")
        preset = save_preset(sim_info, preset_name, False)

        # Print
        output("Exporting to file...")
        file_name = export_location/(preset_name.replace(' ', '_') + '.ffa')
        with open(file_name, 'w') as export_file:
            export_file.write('{"version": ' + str(expected_json_version) + ',\n "presets": ' + substitutions(json.dumps(preset, indent=4)) + '}')

        output(f"Done, file created at {file_name}")
    except (Exception,):
        output(f"Export failed sim, check logs...")
        log_text(f"Export failed sim due to {traceback.format_exc()}")


@sims4.commands.Command('create_generic_preset', command_type=sims4.commands.CommandType.Live)
def create_generic_preset(*args, _connection=None):
    output = sims4.commands.CheatOutput(_connection)
    try:
        # Process input
        if len(args) == 0:
            output("Please provide a a name for the preset")
            return
        elif len(args) == 1:
            client = services.client_manager().get_first_client()
            sim_info = client.active_sim.sim_info
            preset_name = args[0]
        elif len(args) == 2:
            output("Input invalid. Please provide either just a preset name (surrounded by \") or a sim name, then the preset name.")
            return
        elif len(args) == 3:
            first_name = args[1]
            last_name = args[2]
            sim_info = services.sim_info_manager().get_sim_info_by_name(first_name, last_name)
            preset_name = args[0]
        else:
            output("Input invalid. Please provide either just a preset name (surrounded by \") or a sim name, then the preset name.")
            return

        if sim_info is None:
            output("Target sim not found")
            return

        with open(log_path, 'w') as f:
            f.write(f"Starting...\n")

        output("Starting...")

        # Save all sim's appearance
        output("Saving appearance data...")
        preset = save_preset(sim_info, preset_name, True)

        # Print
        output("Exporting to file...")
        file_name = export_location/(preset_name.replace(' ', '_') + '.ffa')
        with open(file_name, 'w') as export_file:
            export_file.write('{"version": ' + str(expected_json_version) + ',\n "presets": ' + substitutions(json.dumps(preset, indent=4)) + '}')

        output(f"Done, file created at {file_name}")
    except (Exception,):
        output(f"Export failed sim, check logs...")
        log_text(f"Export failed sim due to {traceback.format_exc()}")


def save_preset(target_sim_info, preset_name, is_generic):
    if target_sim_info.species != Species.HUMAN:
        raise Exception("Sim isn't a human!")

    sim_name = get_sim_name(target_sim_info)

    forms = {}

    base_occult_type = target_sim_info.occult_tracker.get_current_occult_types()
    # Check if in non-human form, if so save that as alt and human as main
    # Else save human as main and alt as alt
    if base_occult_type is OccultType.VAMPIRE:
        forms["VAMPIRE"] = save_form_appearance(target_sim_info, OccultType.VAMPIRE)
        forms["HUMAN"] = save_form_appearance(target_sim_info.occult_tracker.get_occult_sim_info(OccultType.HUMAN), OccultType.HUMAN)
    elif base_occult_type is OccultType.MERMAID:
        forms["MERMAID"] = save_form_appearance(target_sim_info, OccultType.MERMAID)
        forms["HUMAN"] = save_form_appearance(target_sim_info.occult_tracker.get_occult_sim_info(OccultType.HUMAN), OccultType.HUMAN)
    elif base_occult_type is OccultType.WEREWOLF:
        forms["HUMAN"] = save_form_appearance(target_sim_info.occult_tracker.get_occult_sim_info(OccultType.HUMAN), OccultType.HUMAN)

    elif target_sim_info.occult_tracker.has_occult_type(OccultType.VAMPIRE):
        forms["HUMAN"] = save_form_appearance(target_sim_info, OccultType.HUMAN)
        forms["VAMPIRE"] = save_form_appearance(target_sim_info.occult_tracker.get_occult_sim_info(OccultType.VAMPIRE), OccultType.VAMPIRE)
    elif target_sim_info.occult_tracker.has_occult_type(OccultType.MERMAID):
        forms["HUMAN"] = save_form_appearance(target_sim_info, OccultType.HUMAN)
        forms["MERMAID"] = save_form_appearance(target_sim_info.occult_tracker.get_occult_sim_info(OccultType.MERMAID), OccultType.MERMAID)
    elif target_sim_info.occult_tracker.has_occult_type(OccultType.FAIRY):
        forms["HUMAN"] = save_form_appearance(target_sim_info, OccultType.HUMAN)
        forms["FAIRY"] = save_form_appearance(target_sim_info.occult_tracker.get_occult_sim_info(OccultType.FAIRY), OccultType.FAIRY)
    else:
        forms["HUMAN"] = save_form_appearance(target_sim_info, OccultType.HUMAN)

    trait_manager = services.get_instance_manager(Types.TRAIT)

    if target_sim_info.age >= Age.TEEN:
        if target_sim_info.has_trait(trait_manager.get(136877)):
            frame = "FRAME_MASCULINE"
        else:
            frame = "FRAME_FEMININE"

        requires = f"{age_translator[target_sim_info.age]} & {frame}"
    else:
        requires = f"{age_translator[target_sim_info.age]}"

    species = get_sim_species_from_parts(get_furry_parts(target_sim_info))

    preset_category = sim_name
    if is_generic:
        preset_category = 'GENERIC'

    presets_base = dict()
    presets_base[preset_category] = {}
    presets_base[preset_category][preset_name.replace(' ', '_')] = {
        "requires": requires,
        "species": species,
        "appearance": forms
    }
    if not is_generic:
        presets_base[preset_category][preset_name.replace(' ', '_')]["weights"] = {"": 9999999}

    return presets_base


def save_form_appearance(sim_info, form_type_enum) -> dict:
    # Get defaults if needed and possible
    sim_name = get_sim_name(sim_info)
    form_type = OccultType(form_type_enum).name

    # Get the skintone
    sim_skintone = int_to_hex(sim_info.skin_tone)
    sim_skintone_val_shift = sim_info.skin_tone_val_shift

    # Get all outfit parts
    processed_sim_outfits = {}
    genetic_parts = []

    for outfit_category, outfit_slot, outfit in get_sim_outfits(sim_info):
        if outfit_category in (OutfitCategory.BATHING, OutfitCategory.SITUATION, OutfitCategory.SPECIAL):
            continue

        outfit_name = f"{outfit_category.name.capitalize()} {outfit_slot}"

        parts = []
        used_body_types = set()
        for part_id in outfit.parts.ids:
            body_type = get_caspart_bodytype(part_id)
            if body_type in FurryPartApplier.non_genetic_body_types and part_id not in parts:
                parts.append(part_id)

                if body_type in used_body_types:
                    log_text(f"WARNING: {sim_name} has duplicates on {body_type}!")
                used_body_types.add(body_type)

        processed_sim_outfits[outfit_name] = {"": [int_to_hex(part) for part in parts]}

        # Get Genes from first outfit
        used_body_types = set()
        if not genetic_parts:
            for part_id in outfit.parts.ids:
                body_type = get_caspart_bodytype(part_id)
                if body_type > 0 and (body_type == BodyType.HAIR or (body_type not in FurryPartApplier.non_genetic_body_types and body_type not in FurryPartApplier.ignored_body_types)) and part_id not in genetic_parts:
                    genetic_parts.append(part_id)

                    if body_type in used_body_types:
                        log_text(f"WARNING: {sim_name} has duplicates on {body_type}!")
                    used_body_types.add(body_type)

    # Get sculpts and sliders
    appearance_attributes = PersistenceBlobs_pb2.BlobSimFacialCustomizationData()
    appearance_attributes.ParseFromString(sim_info.facial_attributes)

    sliders = {int_to_hex(modifier.key): modifier.amount for modifier in appearance_attributes.face_modifiers}
    body_sliders = {int_to_hex(modifier.key): modifier.amount for modifier in appearance_attributes.body_modifiers}
    genetic_conditional_parts = {"": [int_to_hex(part) for part in genetic_parts]}
    sculpts = list(appearance_attributes.sculpts)

    temp = {
        "outfits": processed_sim_outfits,
        "genetics": {
            "parts": genetic_conditional_parts,
            "sculpts": [int_to_hex(sculpt) for sculpt in sculpts],
            "sliders": sliders,
            "body_sliders": body_sliders,
            "skin_tone": sim_skintone,
            "skin_tone_val_shift": sim_skintone_val_shift
        }
    }

    try:
        temp["genetics"]["fit"] = sim_info.fit
        temp["genetics"]["fat"] = sim_info.fat
    except (Exception,):
        pass

    return temp
