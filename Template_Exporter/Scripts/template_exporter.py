import json
import os
import services
import traceback
from math import isclose
from pathlib import Path

from furrifier_sim_data_manager import is_furry, get_furry_parts, get_sim_species_from_parts, get_sim_outfits
from furrifier_utils_basics import get_sim_name, int_to_hex
from furrifier_configs_register_parser import substitutions
from furrifier_res_premades import premades_data
from furrifier_part_applier import FurryPartApplier

import sims4.commands
from cas.cas import get_caspart_bodytype
from sims4.resources import Types
from protocolbuffers import PersistenceBlobs_pb2
from sims.outfits.outfit_enums import BodyType, OutfitCategory
from sims.occult.occult_enums import OccultType
from sims.sim_info_types import Species, Age

log_location = os.path.join(Path(__file__).resolve().parent.parent, "template_log.log")
export_location = os.path.join(Path(__file__).resolve().parent.parent, "exported_templates.json")
export_compact_location = os.path.join(Path(__file__).resolve().parent.parent, "exported_templates_compact.json")


def log_text(text: str):
    with open(log_location, 'a') as f:
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


@sims4.commands.Command('export_templates', command_type=sims4.commands.CommandType.Live)
def export_templates(_connection=None):
    output = sims4.commands.CheatOutput(_connection)
    output("Starting...")
    try:
        with open(log_location, 'w') as f:
            f.write(f"Starting...\n")

        # Save all sim's appearances
        output("Saving appearances data...")
        appearances = save_appearances(convert=True)
        log_text("\n\n\nRe-exporting for compact")
        compact_appearances = save_appearances(convert=False)

        # Print
        output("Exporting...")
        with open(export_location, 'w') as export_file:
            export_file.write('{"version": 9,\n "presets": ' + substitutions(json.dumps(appearances, indent=4)) + '}')
        with open(export_compact_location, 'w') as export_file:
            export_file.write('{"version": 9, "presets": ' + json.dumps(compact_appearances) + '}')
    except (Exception,):
        log_text(f"Export failed sim due to {traceback.format_exc()}")

    output("Done.")


@sims4.commands.Command('update_export', command_type=sims4.commands.CommandType.Live)
def update_exports(_connection=None):
    output = sims4.commands.CheatOutput(_connection)
    output("Starting...")
    try:
        with open(log_location, 'w') as f:
            f.write(f"Starting...\n")

        # Get sims we already have appearances for
        with open(export_location, 'r') as f:
            existing_appearances = json.load(f)["presets"]
        with open(export_compact_location, 'r') as f:
            existing_compact_appearances = json.load(f)["presets"]

        # Save all sim's appearances
        output("Saving appearances data...")
        appearances = save_appearances(existing_appearances, convert=True)
        log_text("\n\n\nRe-exporting for compact")
        compact_appearances = save_appearances(existing_compact_appearances, convert=False)

        # Print
        output("Exporting...")
        with open(export_location, 'w') as export_file:
            export_file.write('{"version": 9,\n "presets": ' + substitutions(json.dumps(appearances, indent=4)) + '}')
        with open(export_compact_location, 'w') as export_file:
            export_file.write('{"version": 9, "presets": ' + json.dumps(compact_appearances) + '}')
    except (Exception,):
        log_text(f"Export failed sim due to {traceback.format_exc()}")

    output("Done.")


def save_appearances(existing_appearances=None, convert=True):
    non_furry_sims = []
    expected_sims = set(premades_data.keys())
    unexpected_sims = []

    if existing_appearances is None:
        sim_appearances = {}
    else:
        sim_appearances = existing_appearances
        expected_sims = expected_sims - sim_appearances.keys()

    for sim_info in services.sim_info_manager().get_all():
        try:
            if sim_info.species == Species.HUMAN:
                sim_name = get_sim_name(sim_info)

                if sim_name not in sim_appearances.keys():
                    if sim_name in expected_sims:
                        expected_sims.remove(sim_name)

                        forms = {}

                        if is_furry(sim_info, False):
                            base_occult_type = sim_info.occult_tracker.get_current_occult_types()
                            # Check if in non-human form, if so save that as alt and human as main
                            # Else save human as main and alt as alt
                            if base_occult_type is OccultType.VAMPIRE:
                                forms["VAMPIRE"] = save_form_appearance(sim_info, OccultType.VAMPIRE, compare_with_default=True, convert=convert)
                                forms["HUMAN"] = save_form_appearance(sim_info.occult_tracker.get_occult_sim_info(OccultType.HUMAN), OccultType.HUMAN, compare_with_default=True, convert=convert)
                            elif base_occult_type is OccultType.MERMAID:
                                forms["MERMAID"] = save_form_appearance(sim_info, OccultType.MERMAID, compare_with_default=True, convert=convert)
                                forms["HUMAN"] = save_form_appearance(sim_info.occult_tracker.get_occult_sim_info(OccultType.HUMAN), OccultType.HUMAN, compare_with_default=True, convert=convert)
                            elif base_occult_type is OccultType.WEREWOLF:
                                forms["HUMAN"] = save_form_appearance(sim_info.occult_tracker.get_occult_sim_info(OccultType.HUMAN), OccultType.HUMAN, compare_with_default=True, convert=convert)

                            elif sim_info.occult_tracker.has_occult_type(OccultType.VAMPIRE):
                                forms["HUMAN"] = save_form_appearance(sim_info, OccultType.HUMAN, compare_with_default=True, convert=convert)
                                forms["VAMPIRE"] = save_form_appearance(sim_info.occult_tracker.get_occult_sim_info(OccultType.VAMPIRE), OccultType.VAMPIRE, compare_with_default=True, convert=convert)
                            elif sim_info.occult_tracker.has_occult_type(OccultType.MERMAID):
                                forms["HUMAN"] = save_form_appearance(sim_info, OccultType.HUMAN, compare_with_default=True, convert=convert)
                                forms["MERMAID"] = save_form_appearance(sim_info.occult_tracker.get_occult_sim_info(OccultType.MERMAID), OccultType.MERMAID, compare_with_default=True, convert=convert)
                            else:
                                forms["HUMAN"] = save_form_appearance(sim_info, OccultType.HUMAN, compare_with_default=True, convert=convert)

                            trait_manager = services.get_instance_manager(Types.TRAIT)

                            if sim_info.age >= Age.TEEN:
                                if sim_info.has_trait(trait_manager.get(136877)):
                                    frame = "FRAME_MASCULINE"
                                else:
                                    frame = "FRAME_FEMININE"

                                requires = f"{age_translator[sim_info.age]} & {frame}"
                            else:
                                requires = f"{age_translator[sim_info.age]}"

                            species = get_sim_species_from_parts(get_furry_parts(sim_info))
                            preset_name = f"Premade_Furry_{sim_name.replace(' ', '_')}_({species.capitalize()})"
                            sim_appearances[sim_name] = {}
                            sim_appearances[sim_name][preset_name] = {
                                "requires": requires,
                                "weights": {"": 1},
                                "species": species,
                                "appearance": forms
                            }
                        else:
                            non_furry_sims.append(sim_name)
                    else:
                        unexpected_sims.append(sim_name)
        except NameError as e:
            log_text(f"Failed on sim due to {e}")
        except (Exception,):
            log_text(f"Failed on sim due to {traceback.format_exc()}")

    text = '\n\t'.join(non_furry_sims)
    log_text(f"Sims expected and found but not furry:\n\t{text}\n")
    text = '\n\t'.join(expected_sims)
    log_text(f"Sims expected but not found:\n\t{text}\n")
    text = '\n\t'.join(unexpected_sims)
    log_text(f"Sims not expected but found:\n\t{text}\n")

    # Sort sims
    keys = sorted(list(sim_appearances.keys()))
    sorted_sim_appearances = {key: sim_appearances[key] for key in keys}

    return sorted_sim_appearances


def save_form_appearance(sim_info, form_type_enum, compare_with_default=False, convert=True) -> dict:
    # Get defaults if needed and possible
    sim_name = get_sim_name(sim_info)
    if compare_with_default and sim_name not in premades_data:
        raise NameError(f"No recorded defaults for {sim_name}")

    form_type = OccultType(form_type_enum).name

    # Get the skintone
    sim_skintone = int_to_hex(sim_info.skin_tone) if convert else sim_info.skin_tone
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

        if compare_with_default:
            default_parts = next((outfit_parts for default_category, outfit_parts in premades_data[sim_name]["appearance"][form_type]['outfits'].items() if default_category == outfit_name), None)
            conditional_parts = get_part_conditions(parts, default_parts, convert=convert)  # Dict

            if not (len(conditional_parts) == 1 and len(conditional_parts[""]) == 0):
                processed_sim_outfits[outfit_name] = conditional_parts
        else:
            conditional_parts = [int_to_hex(part) for part in parts] if convert else parts  # Just a list

            processed_sim_outfits[outfit_name] = conditional_parts

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

    # Get genetic hair
    # genetic_msg = Outfits_pb2.GeneticData()
    # noinspection PyProtectedMember
    # genetic_msg.ParseFromString(sim_info._base.genetic_data)

    # # Only get hair from genetics. Get everything else from outfits, to avoid glitchy corruptions
    # for part in genetic_msg.parts_list.parts:
    #     genetic_parts.append(part.id)

    # Get sculpts and sliders
    appearance_attributes = PersistenceBlobs_pb2.BlobSimFacialCustomizationData()
    appearance_attributes.ParseFromString(sim_info.facial_attributes)

    sliders = {int_to_hex(modifier.key): modifier.amount for modifier in appearance_attributes.face_modifiers}
    body_sliders = {int_to_hex(modifier.key): modifier.amount for modifier in appearance_attributes.body_modifiers}
    if compare_with_default:
        genetic_defaults = premades_data[sim_name]["appearance"][form_type]['genetics']
        genetic_conditional_parts = get_part_conditions(genetic_parts, genetic_defaults['parts'], True, convert=convert)

        sculpts = get_different_sculpts(list(appearance_attributes.sculpts), genetic_defaults['sculpts'])
        sliders = get_different_sliders(sliders, genetic_defaults['sliders'])
        body_sliders = get_different_sliders(body_sliders, genetic_defaults['body_sliders'])
    else:
        genetic_conditional_parts = [int_to_hex(part) for part in genetic_parts] if convert else genetic_parts  # Just a list
        sculpts = list(appearance_attributes.sculpts)

    temp = {
        "outfits": processed_sim_outfits,
        "genetics": {
            "parts": genetic_conditional_parts,
            "sculpts": [int_to_hex(sculpt) for sculpt in sculpts] if convert else sculpts,
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


def get_part_conditions(furry_parts, default_parts, include_genetics=False, convert=True) -> dict:
    part_conditions = {
        "": []
    }
    included_body_types = []

    for part_id in furry_parts:
        part_id_str = int_to_hex(part_id)
        insertable_id = part_id_str if convert else part_id

        # If the part is a default part, ignore it
        if default_parts is not None and part_id_str not in [int_to_hex(part) for part in default_parts]:
            # NOTE: Only both with destructive prefs that pref the destruction on the premades
            body_type = get_caspart_bodytype(part_id)
            included_body_types.append(body_type)
            # If the part is legs, add tags and digi alt
            if body_type == BodyType.SKINDETAIL_FRECKLES:
                # If part is digi, add tag and appropriate planti
                if part_id_str in ("F015398928D69D6B", "F00A6397E1991A05", "A7BE6AA56B814F78"):  # Male Digi
                    part_conditions.setdefault("LEG_DIGITIGRADE", []).append(insertable_id)
                    part_conditions.setdefault("LEG_PLANTIGRADE & NOT LEG_DIGITIGRADE", []).append("A86099389D47FBCF")
                elif part_id_str == "E2615F6F74BAA05E":  # Female Digi
                    part_conditions.setdefault("LEG_DIGITIGRADE", []).append(insertable_id)
                    part_conditions.setdefault("LEG_PLANTIGRADE & NOT LEG_DIGITIGRADE", []).append("DCB20998D7653C0C")
                elif part_id_str in ("E2615F6F74BAA05E", "83387FDBF14AC4CC", "92F40F78B5299808", "AA242D0BF9C4D5FA"):  # Sora Female Digi
                    part_conditions.setdefault("LEG_DIGITIGRADE", []).append(insertable_id)
                    part_conditions.setdefault("LEG_PLANTIGRADE & NOT LEG_DIGITIGRADE", []).append("80A8F96D1284545B")
                elif part_id_str == "843ACB3D2BBC42CA":  # Child Digi
                    part_conditions.setdefault("LEG_DIGITIGRADE", []).append(insertable_id)
                    part_conditions.setdefault("LEG_PLANTIGRADE & NOT LEG_DIGITIGRADE", []).append("FCF07B5B80DE71E4")
                elif part_id_str == "95119E1453CDB171":  # Toddler Digi
                    part_conditions.setdefault("LEG_DIGITIGRADE", []).append(insertable_id)
                    part_conditions.setdefault("LEG_PLANTIGRADE & NOT LEG_DIGITIGRADE", []).append("EB9DD19342E33B22")
                elif part_id_str == "C329ACD325E169E3":  # Infant Digi
                    part_conditions.setdefault("LEG_DIGITIGRADE", []).append(insertable_id)
                    part_conditions.setdefault("LEG_PLANTIGRADE & NOT LEG_DIGITIGRADE", []).append("C9963CE4C5685037")

                # If part is planti, add tag
                elif part_id_str in ("A86099389D47FBCF", "80A8F96D1284545B", "843ACB3D2BBC42CA", "FCF07B5B80DE71E4", "EB9DD19342E33B22", "C9963CE4C5685037"):
                    part_conditions.setdefault("LEG_DIGITIGRADE | LEG_PLANTIGRADE", []).append(insertable_id)
            # If pants/shirt or full body, only add if digi
            elif body_type in (BodyType.UPPER_BODY, BodyType.LOWER_BODY, BodyType.FULL_BODY):
                part_conditions.setdefault("LEG_DIGITIGRADE", []).append(insertable_id)
            # If shoes, socks, or tights, replace if either
            elif body_type in (BodyType.SHOES, BodyType.SOCKS, BodyType.TIGHTS):
                part_conditions.setdefault("LEG_DIGITIGRADE | LEG_PLANTIGRADE", []).append(insertable_id)

            # If part is optional, add tags and alternatives
            elif part_id_str in ["BC0228A8FF32A021", "9363B6D71D71F057", "F2C976253E80265B", "E99CD135E04039F9", "DF8794238ABA67EA", "C251021041310565", "A7578F88D99573D8", "F119BBA8A1DEAF5E", "B0BD7AA718D3F281", "ED8586F9B1EEAF24", "E6DE5C20FEC82F23", "F428420F13B1DCFB", "D6A97FD48CE05594", "9319CFB35624B953", "8E41AD27E676BFD8", "C1D86BCF295C2CF7", "D1EA8BC24EEAB6DE", "942F67869C6867A1", "DE9CB6BFB07F76E6", "D80CD4BA6787645F", "A18BB1973CDB66CF", "CB62226FF1A52B01", "EFE2124A2F8EFB15", "EF173D28D5F9BAA5", "D44813414AB59C5D", "F1AFEAB718BB97FC", "E76E949CDC25FC96", "9363F5A5C9FD6ED5", "CA492F88E7626CDE", "BDD649AC34C04FF6", "98C0329A758929B1", "DA52D34FED5AF0A5", "CFD798AC0F005C0F", "ACA6D4D5E0A1E2CA", "FCB481C65F2D0665", "FAD62B7324845362", "E8D410B3EF343FB7", "F9C18CC55A3E8FCD", "916CF9DDA3316013", "EAE84168FA4C10E9", "F8690B21546CB2BC",  "C2106F30E45CE558", "E26F8700801C6612"]:  # Fox Mark
                part_conditions.setdefault("P'Sora Fox Mark'", []).append(insertable_id)
            elif part_id_str == "DF03DF9E9DE26ECD":  # Sora Dragon Male 2 Head
                part_conditions.setdefault("P'Sora Male Dragon 2 Head'", []).append(insertable_id)
                part_conditions.setdefault("NOT P'Sora Male Dragon 2 Head'", []).append("9A3A97043C4BD65F")
            elif part_id_str == "FD4E9AC3F42588BE":  # Sora Female Dragon 1 Head
                part_conditions.setdefault("P'Sora Female Dragon 1 Head'", []).append(insertable_id)
                part_conditions.setdefault("NOT P'Sora Female Dragon 1 Head'", []).append("E094475858465DEE")
            elif part_id_str == "B4EAA36A38C3E7CC":  # Sora Female Dragon 2 Head
                part_conditions.setdefault("P'Sora Female Dragon 2 Head'", []).append(insertable_id)
                part_conditions.setdefault("NOT P'Sora Female Dragon 2 Head'", []).append("E094475858465DEE")
            elif part_id_str == "A0542C39E10410C8":  # Dragon Wings
                part_conditions.setdefault("P'Springroll Wings'", []).append(insertable_id)
            elif part_id_str == "9E841B5C32FDC7BD":  # Dragon Horns
                part_conditions.setdefault("P'Springroll Horns'", []).append(insertable_id)
            elif part_id_str in ["9757FE36771C2FF8", "9757FE36771C2FF8", "99C08618BF0627D9", "99C08618BF0627D9", "C639566AD4C72CC1", "C639566AD4C72CC1", "8652AA8AFF7D37C1", "AF2A7E7AECA38C95", "EBF44FDDAFA01822", "8C9200F7701759D7", "8C9200F7701759D7", "9B20520FB3BFDC7B", "9B20520FB3BFDC7B", "EEA07BD219160AE9", "9C894A26C6D1278D", "9C894A26C6D1278D", "A9784BC9355412F4", "82643D7D500A6423", "B624515C146115B3", "C3F4E63B54A8ECB0", "E062A759F229B6B5", "90E70B36B9A0A562", "FC2C732795D185BA", "969FF60D6C180811"]:  # Dragon Tail
                part_conditions.setdefault("P'Springroll Tufted Tail'", []).append(insertable_id)
                part_conditions.setdefault("NOT P'Springroll Tufted Tail' AND NOT PREF_USE_ANIMATED_TAILS", []).append("89677FD18556B78A")
                part_conditions.setdefault("NOT P'Springroll Tufted Tail' AND PREF_USE_ANIMATED_TAILS", []).append("97FE32543E28AA62")
            elif part_id_str in ["E886A5165541DAD7", "855A0D5D04395E52", "88CEBD39B1ABB215", "AA4AD69EF14DEDF2", "EA28B8CE4CC5932E", "CF0F90953A5C5F80", "BD93FC076349C942", "D4059C26C4F67B3B", "AE4F83DAE0D60FE2", "8B4D08F091B4BCFF", "F65C87F720165CB8", "C3460160C23E256D", "A6756CFDFBA88CDE", "C09812DCB197DBCB", "C42DD9FCD0C39594"]:  # Antelope Horns
                part_conditions.setdefault("P'Springroll Antelope Horns'", []).append(insertable_id)
            elif part_id_str in ["A7EF5B006F8C0B4A", "BA1C34318F144283", "FA137A4BDFE2F261", "C25EEB3C5A4AB01C", "82E808BBB55DB685", "D0D415176B30D239"]:  # Unicorn Horn
                part_conditions.setdefault("P'Springroll Unicorn Horn'", []).append(insertable_id)

            # Otherwise just add to default list
            else:
                part_conditions[""].append(insertable_id)
        elif default_parts is None:
            # Use every part if no defaults
            part_conditions[""].append(insertable_id)

    # Any parts in the template but not the outfit, add in as negatives
    if default_parts is not None:
        for default_part in default_parts:
            if default_part not in furry_parts:
                body_type = get_caspart_bodytype(default_part)
                # Only do parts that aren't replaced, and genetic parts only if doing genetics
                if body_type not in included_body_types and (include_genetics or body_type in FurryPartApplier.non_genetic_body_types):
                    part_id_str = int_to_hex(default_part)
                    insertable_id = f"-{part_id_str}" if convert else -default_part
                    # If pants or full body, only remove if digi
                    if body_type in (BodyType.LOWER_BODY, BodyType.FULL_BODY):
                        part_conditions.setdefault("LEG_DIGITIGRADE", []).append(insertable_id)
                    # If shoes, socks, or tights, remove if either
                    elif body_type in (BodyType.SHOES, BodyType.SOCKS, BodyType.TIGHTS):
                        part_conditions.setdefault("LEG_DIGITIGRADE | LEG_PLANTIGRADE", []).append(insertable_id)
                    else:
                        part_conditions[""].append(insertable_id)

    # log_text(str(part_conditions))
    return part_conditions


def get_different_sculpts(furry_sculpts, default_sculpts):
    different_sculpts = []
    for sculpt in furry_sculpts:
        if sculpt not in default_sculpts:
            different_sculpts.append(sculpt)

    for sculpt in default_sculpts:
        if sculpt not in furry_sculpts:
            different_sculpts.append(-sculpt)

    return different_sculpts


def get_different_sliders(furry_sliders, default_sliders):
    different_sliders = {}
    for key, amount in furry_sliders.items():
        if key not in default_sliders or not isclose(default_sliders[key], furry_sliders[key], abs_tol=0.01):
            different_sliders[key] = furry_sliders[key]

    # This catches a bunch of unknown sliders, probably not important
    # for key, amount in default_sliders.items():
    #     if key not in furry_sliders:
    #         different_sliders[f"-{key}"] = 0

    return different_sliders
