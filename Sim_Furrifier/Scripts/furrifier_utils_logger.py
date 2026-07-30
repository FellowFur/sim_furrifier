import os
import traceback
from pathlib import Path
from typing import List, Dict
from datetime import datetime as dt

from furrifier_configs_register_handler import get_label_from_id, get_register_parts, get_custom_tags
from furrifier_configs_register_parser import get_used_addons, get_problems
from furrifier_configs_settings_handler import get_setting_value, get_settings_str
from furrifier_utils_notifier import show_notification
from furrifier_utils_basics import get_body_type, filter_none, format_exception, int_to_hex, get_game_version, get_mod_dir
from furrifier_utils_enums import FurryTag, mod_version

from sims.outfits.outfit_enums import BodyType
from sims.sim_info import SimInfo


class LogMessage:
    def __init__(self, target):
        self.indent_lvl = 0
        self.timestamp = dt.now().strftime("%H-%M-%S--%y-%m-%d")
        self.target = target
        self.operation = 'furrify'
        self.is_disguise = False
        self.entries = []
        self.initialized = True
        self.logging = False
        self.exception = False


base_directory = Path(__file__).resolve().parent.parent
log_directory = os.path.join(base_directory, 'Furrifier Logs')

game_version = get_game_version()

# Keep track of the current log
log = LogMessage(None)
log.initialized = False


# Keep track of indent level
indent_lvl = 0

# Store CC status
cc_status = ""


def log_exception(sim_info=None):
    text = traceback.format_exc()
    exception = format_exception(text)
    try:
        # If a log is initialized, mark exception and close
        if log.initialized:
            log.exception = True
            close_log(exception)

        # Otherwise create new log just for exception
        else:
            # Make the log directory if it doesn't exist
            if not os.path.exists(log_directory):
                os.makedirs(log_directory)

            start_time = dt.now()
            formatted_time = start_time.strftime("%H-%M-%S--%y-%m-%d")
            name = f"exception_root--{formatted_time}.log"

            try:
                if sim_info and sim_info.first_name:
                    exception += f"\nProblem Sim: {sim_info.first_name} {sim_info.last_name}"
                elif log.target and log.target.first_name:
                    exception += f"\nProblem Sim: {log.target.first_name} {log.target.last_name}"
                else:
                    exception += f"\nProblem Sim: Unknown"
            except (Exception,):
                exception += f"\nProblem Sim: Unknown"

            exception += f"\nFurrifier Version {mod_version}"
            exception += f"\nGame version {get_game_version()}"
            exception += f"\nCurrent Furrifier Settings:\n{get_settings_str()}"

            delete_oldest_log()
            location = os.path.join(log_directory, name)
            with open(location, 'w') as f:
                f.write(exception)

            message = f"Sorry, but something went wrong. It was recorded in the file '{name}' created in the 'Furrifier Log' folder, which is in the same place you installed the furrifier's mod files. Please send the file to FellowFur on Nexus or Discord for assistance."
            show_notification(message, notif_type="exception", title="Furrifier Error")
    except (Exception,) as e:
        message = f"Sorry, but something went very wrong. Please send this message to FellowFur on Nexus or Discord for assistance:\nPrimary issue: {exception}\n\nSecondary Issue: {format_exception(str(e))}"
        show_notification(message, notif_type="exception", title="Furrifier Error")


def start_log(sim_info, text: str):
    global log
    # If log already open for same sim, continue but note it
    if log.initialized:
        if log.target == sim_info:
            log.entries.append(f"WARNING: Log reopened for sim")
            log.entries.append(f"{text}\n")
            return
        else:
            close_log(f"WARNING: Log suddenly opened for different sim?")

    # Make the log directory if it doesn't exist
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Reset log data
    log = LogMessage(sim_info)

    log.entries.append(f"{text}\n")
    log.entries.append(f"Furrifier Version: {mod_version}")
    log.entries.append(f"Game version: {game_version}\n")
    log.entries.append(f"Current Furrifier Settings:\n{get_settings_str()}")
    log.entries.append(f"CC Installed: \n{cc_status}")
    log.entries.append(f"Addons loaded: {get_used_addons()}\n")
    if get_problems():
        log.entries.append(f"Addons Problems: {get_problems()}\n")


def close_log(text: str):
    if log.initialized:
        if log.logging or log.exception:
            if text:
                log.entries.append(f"{text}")

            log_name = f"{'exception_' if log.exception else ''}{log.operation}_{log.target.first_name}_{log.target.last_name}{'-disguise' if log.is_disguise else ''}--{log.timestamp}.log"

            if log.exception:
                message = f"Sorry, but something went wrong. It was recorded in the file '{log_name}' created in the 'Furrifier Log' folder (located wherever you installed the mod). Please send the file to FellowFur on NexusMods or his Discord Server (link on mod site) for assistance."
                show_notification(message, notif_type="exception", title="Furrifier Error")

            if int(get_setting_value('settings', 'max_logs')) > 0:
                log_location = os.path.join(log_directory, log_name)
                with open(log_location, 'w') as f:
                    f.write("\n".join(log.entries))

            delete_oldest_log()

        log.initialized = False


def log_text(text: str):
    if log:
        log.entries.append(f"{indent()}{text}")


def log_parts(part_ids: List[int]):
    if log:
        parts_str = ""
        parts_data = get_register_parts()
        part_ids = filter_none(part_ids)

        for part_id in part_ids:
            part_category = get_body_type(part_id)
            part_label = get_label_from_id(part_id)
            if part_label is not None:
                parts_str += f"{indent()}{parts_data[part_category]['label']:>12}: {part_label:<30}\t({int_to_hex(part_id)})\n"
            else:
                parts_str += f"{indent()}{BodyType(part_category).name:>12}: ({int_to_hex(part_id)})\n"

        if not part_ids:
            parts_str += f"{indent()}None"

        log.entries.append(f"{parts_str}\n")


def log_options(options: Dict[str, int]):
    if log:
        if options:
            part_options_str = ""

            total_weight = sum(options.values())

            for option_label, option_weight in options.items():
                part_options_str += f"{indent()}{option_weight:3} ({abs(option_weight/total_weight) if total_weight != 0 else 0:5.1%}): {option_label}\n"

            log.entries.append(f"{part_options_str}")
        else:
            log.entries.append(f"{indent()}No valid options.\n")


def log_tags(tags: {int}):
    if log:
        custom_tags = get_custom_tags()
        tags_str = ""

        for tag in sorted(tags):
            if tag in custom_tags.values():
                tags_str += f"{indent()}{list(custom_tags.keys())[list(custom_tags.values()).index(tag)]} ({tag})\n"
            else:
                tags_str += f"{indent()}{FurryTag(tag).name} ({FurryTag(tag).value})\n"

        log.entries.append(f"{tags_str}\n")


def change_indent(level: int):
    if level != 0:
        log.indent_lvl = max(0, log.indent_lvl + level)
    else:
        log.indent_lvl = 0


def indent():
    return "\t" * log.indent_lvl


def delete_oldest_log():
    list_of_files = [os.path.join(log_directory, log_file) for log_file in os.listdir(log_directory)]

    while len(list_of_files) > int(get_setting_value('settings', 'max_logs')):
        oldest_file = min(list_of_files, key=os.path.getctime)
        os.remove(os.path.abspath(oldest_file))
        list_of_files.remove(oldest_file)


def use_log():
    log.logging = True


def is_log_open() -> bool:
    return log.initialized


def is_log_for_sim(sim_info: SimInfo):
    return sim_info == log.target


def change_log_operation(operation: str):
    log.operation = operation


def change_log_disguise(is_disguise: bool):
    log.is_disguise = is_disguise


def quick_log(text: str, log_name="furrifier_log.log"):
    location = os.path.join(log_directory, log_name)
    with open(location, 'w') as f:
        f.write(text)


def cache_status(status: str):
    global cc_status
    cc_status = status
