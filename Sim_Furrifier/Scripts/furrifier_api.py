# This file contains all commands that can be directly called by the game
import services

from furrifier_sim_wrapper import FurrySimWrapper
from furrifier_sim_info import get_primary_info
from furrifier_configs_register_handler import reload_json, get_register_parts, get_label_from_id
from furrifier_configs_register_parser import print_register_str
from furrifier_configs_settings_handler import update_setting
from furrifier_sim_data_manager import can_be_furrified, is_disguised, get_furry_parts, has_disguise, \
    get_sim_species_from_parts, is_furry, should_stay_human
from furrifier_sim_trait_manager import mark_exempt
from furrifier_utils_notifier import show_notification
from furrifier_utils_logger import log_exception
from furrifier_utils_basics import run_interaction, get_body_type, int_to_hex

import sims4.commands
from sims4.resources import Types, get_resource_key


@sims4.commands.Command('FellowFur.Furrififer', command_type=sims4.commands.CommandType.Live)
def furrify(sim_id: int, species: str, is_disguise=False, _connection=None):
    try:
        # Get info of target sim
        target_sim = services.object_manager().get(sim_id)
        sim_info = target_sim.sim_info

        can_furrify, reason = can_be_furrified(sim_info, is_disguise=is_disguise)
        if can_furrify:
            # Furrify the sim
            furry_sim = FurrySimWrapper(sim_info)
            furry_sim.initialize_log()
            furry_sim.initialize_info(is_disguise)
            furry_sim.furrify(species)
        else:
            show_notification(f"Selected sim is not a valid target for furrification. Reason: {reason}")

    except (Exception,):
        log_exception()


@sims4.commands.Command('furrify', command_type=sims4.commands.CommandType.Live)
def furrify_manual(*args, _connection=None):
    output = sims4.commands.CheatOutput(_connection)
    try:
        # Process input
        if len(args) == 0:
            client = services.client_manager().get_first_client()
            sim_info = client.active_sim.sim_info
            species = 'default'
        elif len(args) == 1:
            client = services.client_manager().get_first_client()
            sim_info = client.active_sim.sim_info
            species = args[0]
        elif len(args) == 2:
            first_name = args[0]
            last_name = args[1]
            sim_info = services.sim_info_manager().get_sim_info_by_name(first_name, last_name)
            species = 'default'
        elif len(args) == 3:
            first_name = args[1]
            last_name = args[2]
            sim_info = services.sim_info_manager().get_sim_info_by_name(first_name, last_name)
            species = args[0]
        else:
            output("Input invalid.\nIf not input, make current sim a random species.\nIf 1 input, it must specify the species to make the current sim.\nIf 2 inputs, it must be first and last name of a sim to give a random species.\nIf 3 inputs, it must be a species, followed by a sim's first and last name.")
            return

        if sim_info is None:
            output("Target sim not found")
        else:
            can_furrify, reason = can_be_furrified(sim_info, is_disguise=is_disguised(sim_info))
            if can_furrify:
                output(f"Furrifying sim...")
                furry_sim = FurrySimWrapper(sim_info)
                furry_sim.initialize_log()
                furry_sim.initialize_info(furry_sim.data_manager.is_disguised())
                furry_sim.furrify(species)
                output(f"Done")
            else:
                output(f"Selected sim is not a valid target for furrification. Reason: {reason}")
    except ValueError as e:
        output(str(e))
    except (Exception,) as e:
        output(f"Furrification failed, see logs.")
        output(str(e))
        log_exception()


@sims4.commands.Command('furrify_world', command_type=sims4.commands.CommandType.Live)
def furrify_world(_connection=None):
    for sim_info in services.sim_info_manager().get_all():
        try:
            if not is_furry(sim_info):
                if can_be_furrified(sim_info, is_auto=True)[0]:
                    furry_sim = FurrySimWrapper(sim_info, is_auto=True)
                    furry_sim.initialize_log()
                    furry_sim.initialize_info()

                    if not should_stay_human():
                        furry_sim.furrify('default')
                    else:
                        mark_exempt(sim_info)

                    del furry_sim

                # Also do disguise too, if applicable
                if has_disguise(sim_info) and can_be_furrified(sim_info, is_auto=True, is_disguise=True)[0]:
                    furry_sim = FurrySimWrapper(sim_info, is_auto=True)
                    furry_sim.initialize_log()
                    furry_sim.initialize_info(True)

                    if not should_stay_human():
                        furry_sim.furrify('default')
                    else:
                        mark_exempt(sim_info)

                    del furry_sim
        except (Exception,):
            log_exception(sim_info)


@sims4.commands.Command('FellowFur.Debug_Eyes', command_type=sims4.commands.CommandType.Live)
def debug_eyes(sim_id: int, _connection=None):
    # Get info of target sim
    target_sim = services.object_manager().get(sim_id)
    sim_info = target_sim.sim_info

    try:
        # If they are furry, keep eyes fixed
        furry_sim = FurrySimWrapper(sim_info, is_auto=True)
        furry_sim.initialize_log()
        furry_sim.initialize_info(include_current_species=True, include_current_parts=True)
        furry_sim.reset_sculpts()
    except (Exception,):
        log_exception(sim_info)

    # Also do disguise too, if applicable
    if has_disguise(sim_info):
        try:
            furry_sim = FurrySimWrapper(sim_info, is_auto=True)
            furry_sim.initialize_log()
            furry_sim.initialize_info(include_current_species=True, include_current_parts=True, is_disguise=True)
            furry_sim.reset_sculpts()
        except (Exception,):
            log_exception(sim_info)


@sims4.commands.Command('FellowFur.Randomize_Fur', command_type=sims4.commands.CommandType.Live)
def randomize_fur(sim_id: int, _connection=None):
    try:
        # Get info of target sim
        target_sim = services.object_manager().get(sim_id)
        sim_info = target_sim.sim_info

        furry_sim = FurrySimWrapper(sim_info, is_auto=True)
        furry_sim.initialize_log()
        furry_sim.initialize_info(furry_sim.data_manager.is_disguised(), include_current_species=True)
        furry_sim.randomize_fur_patterns()

    except (Exception,):
        log_exception()


@sims4.commands.Command('FellowFur.Push_Preferences_To_Sim', command_type=sims4.commands.CommandType.Live)
def push_preferences_to_sim(sim_id: int, _connection=None):
    try:
        target_sim = services.object_manager().get(sim_id)
        sim_info = target_sim.sim_info
        furry_sim = FurrySimWrapper(sim_info, is_auto=True)
        furry_sim.initialize_log()
        furry_sim.initialize_info(include_current_parts=True, include_current_species=True)
        furry_sim.update_preferences()

        # Also do disguise too, if applicable
        if has_disguise(sim_info):
            furry_sim.initialize_log()
            furry_sim.initialize_info(is_disguise=True, include_current_parts=True, include_current_species=True)
            furry_sim.update_preferences()
    except (Exception,):
        log_exception()


@sims4.commands.Command('FellowFur.Push_Preferences_To_World', command_type=sims4.commands.CommandType.Live)
def push_preferences_to_world(_connection=None):
    try:
        for sim_info in services.sim_info_manager().get_all():
            try:
                if is_furry(sim_info):
                    if can_be_furrified(sim_info, is_auto=True)[0]:
                        furry_sim = FurrySimWrapper(sim_info, is_auto=True)
                        furry_sim.initialize_log()
                        furry_sim.initialize_info(include_current_parts=True, include_current_species=True)
                        furry_sim.update_preferences()
                        del furry_sim

                    # Also do disguise too, if applicable
                    if has_disguise(sim_info) and can_be_furrified(sim_info, is_auto=True, is_disguise=True)[0]:
                        furry_sim = FurrySimWrapper(sim_info, is_auto=True)
                        furry_sim.initialize_log()
                        furry_sim.initialize_info(is_disguise=True, include_current_parts=True, include_current_species=True)
                        furry_sim.update_preferences()
                        del furry_sim
            except (Exception,):
                log_exception(sim_info)
    except (Exception,):
        log_exception()


@sims4.commands.Command('FellowFur.Show_Parts', command_type=sims4.commands.CommandType.Live)
def show_parts(sim_id: int, _connection=None):
    try:
        # Get info of target sim
        target_sim = services.object_manager().get(sim_id)
        sim_info = target_sim.sim_info

        # Determine what parts are still equipped
        part_ids = get_furry_parts(get_primary_info(sim_info, is_disguised(sim_info)))
        # Also determine the apparent species
        species = get_sim_species_from_parts(part_ids)

        parts_data = get_register_parts()
        parts_message = ""

        for target_part_id in part_ids:
            label = get_label_from_id(target_part_id)
            part_category = get_body_type(target_part_id)

            if label is not None:
                parts_message += f"{parts_data[part_category]['label']}: {label} ({int_to_hex(target_part_id)})\n\n"

        parts_message += f"\nProbable species: {species}"

        show_notification(parts_message, title="Current Furry Parts")
    except (Exception,):
        log_exception()


# Changes settings
@sims4.commands.Command('FellowFur.Change_Setting', command_type=sims4.commands.CommandType.Live)
def change_setting(category: str, setting: str, value: str, message="", title="Furrifier Settings", _connection=None):
    try:
        update_setting(category, setting, value, message, title)
        # If the setting changing is enabling auto mode, furrify every loaded sim
        if setting == 'automatic_furrifier' and value == "True":
            furrify_world()
    except (Exception,):
        log_exception()


# Changes setting and then re-opens the specified menu
@sims4.commands.Command('FellowFur.Change_Setting_Via_Menu', command_type=sims4.commands.CommandType.Live)
def change_setting_via_menu(category: str, setting: str, value: str, sim_id: int, continuation: str, _connection=None):
    try:
        change_setting(category, setting, value)
        target_sim = services.object_manager().get(sim_id)
        run_interaction(int(continuation), target_sim)
    except (Exception,):
        log_exception()


@sims4.commands.Command('furrifier_reload', command_type=sims4.commands.CommandType.Live)
def reload_register(_connection=None):
    output = sims4.commands.CheatOutput(_connection)
    output("Reloading furrifier register...")
    reload_json()
    output("Reloaded!")


@sims4.commands.Command('furrifier_print', command_type=sims4.commands.CommandType.Live)
def print_register(*args, _connection=None):
    try:
        if len(args) == 0:
            print_register_str()
        else:
            print_register_str(args[0])
    except (Exception,):
        log_exception()


# TODO: unofficial update idea: fix spine layers
# Add sprinroll recolors for spine


# PROPASL: Track default appearances in furrifier itself, built in
# Use that appearance for human species, if possible
# SO do we save the new sim's full appearances, or just the changes from the baseline?
# Changes from baseline would need negative changes as well... Two objects
# But no redundancies. I tihnk we save full appearance in each case. Should not be much worse, I think
# What to do about legs/feet? Need to be saved so correct option can be picked. Probably just swap out at run time honestly
# But that makes it less flexible for supporting custom outfits.
# ADD CUSTOMIZATION LATER - Or refine later?
# Proposition - Conditions section?
# Applies to whole sim, not specific outfits
# Apply part only if condition is met -
# We'll figure customization out later. Just track all the sim's parts, and apply all the sim's parts, all at once.
