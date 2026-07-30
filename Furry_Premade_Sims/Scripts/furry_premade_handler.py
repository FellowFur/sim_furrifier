from furry_premade_notifier import notify_missing_requirements
from furry_premade_data import get_premade_addon

is_valid = False

# Make sure the furrifier v2.1 and required CC are installed
try:
    from furrifier_configs_settings_detector import sets
    from furrifier_utils_enums import mod_version, expected_json_version

    expected_sora_parts = {"SoraFoxyTeils_Loona Heluva boss Back.package", "Loona Heluva boss mask.package", "SoraFoxyTeils_Loona Heluva boss stockings gloves.package", "SoraFoxyTeils_Nose piercing2.package"}
    missing_sora_parts = sets['SET_SORAFOXYTEILS']["missing_files"] & expected_sora_parts

    mod_version_segments = mod_version.split('.')
    if int(mod_version_segments[0]) < 2 or int(mod_version_segments[1]) < 1:
        notify_missing_requirements(
            "'Furry Premade Sims' requires at least v2.1 of the 'Sim Furrifier' mod to function, and your version is outdated. This will cause more exceptions if ignored. Please update the Sim Furrifier (link on mod page).",
            "Furrifier Outdated")
    elif get_premade_addon()['version'] > expected_json_version:
        notify_missing_requirements(
            "'Furry Premade Sims' requires a newer version of the 'Sim Furrifier' mod to function, and your version is outdated. This will cause more exceptions if ignored. Please update the Sim Furrifier (link on mod page).",
            "Furrifier Outdated")
    elif get_premade_addon()['version'] < expected_json_version:
        notify_missing_requirements(
            "Your version of the 'Sim Furrifier' mod is too new for your version of 'Furry Premade Sims'. This will cause more exceptions if ignored. Please update Furry Premade Sims (link on mod page).",
            "Furry Premade Sims Outdated")
    elif sets['SET_SAVESTATE']["status"] != "Installed":
        notify_missing_requirements(
            "'Furry Premade Sims' requires all of 'SaveState's Furry Mod' and other furry CC, but can't find them. This will cause more exceptions if ignored. Please ensure you have it installed and enabled (link on mod page).",
            "Furry Premade Sims Missing CC")
    elif sets['SET_SPRINGROLL_NATURAL']["status"] != "Installed" or sets['SET_SPRINGROLL_SORBET']["status"] != "Installed":
        notify_missing_requirements(
            "'Furry Premade Sims' requires all of 'ssSpringroll's Furry Recolors', but can't find them. This will cause more exceptions if ignored. Please ensure you have them installed and enabled (link on mod page).",
            "Furry Premade Sims Missing CC")
    elif sets['SET_SORAFOXYTEILS']["status"] == "Uninstalled":
        notify_missing_requirements(
            "'Furry Premade Sims' requires some of 'SoraFoxyTeils Furry CC', but can't find it. This will cause more exceptions if ignored. Please ensure you have it installed and enabled (link on mod page).",
            "Furry Premade Sims Missing CC")
    elif len(missing_sora_parts) > 0:
        notify_missing_requirements(
            f"'Furry Premade Sims' requires some of 'SoraFoxyTeils Furry CC', including (but not limited to) {', '.join(missing_sora_parts)}. This will cause more exceptions if ignored. Please reinstall the mod and make sure you have these parts.",
            "Furry Premade Sims Missing CC")
    elif sets['SET_CYANGEOM_KIDS']["status"] == "Uninstalled":
        notify_missing_requirements(
            "'Furry Premade Sims' requires some of 'Cyangeom's Furry Kids', but can't find it. This will cause more exceptions if ignored. Please ensure you have it installed and enabled (link on mod page).",
            "Furry Premade Sims Missing CC")
    else:
        is_valid = True
except ImportError as e:
    notify_missing_requirements(f"The 'Sim Furrifier' mod is required for 'Furry Premade Sims', but the furrifier cannot be found. Please ensure you have it installed and enabled (link on mod page).", "'Furry Premade Sims' Missing 'Sim Furrifier'")
except (Exception,) as e:
    pass


def can_load():
    return is_valid
