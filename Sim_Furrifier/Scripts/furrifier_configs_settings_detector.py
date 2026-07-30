from furrifier_utils_enums import FurryFlag
from furrifier_configs_register_handler import get_register_parts, get_register_substitutes, get_register_special_deletions
from furrifier_utils_basics import is_part_installed, first_real
from furrifier_utils_logger import log_exception, cache_status
from furrifier_utils_notifier import show_notification

# Installed / Partial / Uninstalled
sets = {
    "SET_SAVESTATE": {
        "name": "SaveState's Furry Mod",
        "names": [0xF3CFC48D, 0x935924E9, 0x1B3FBF07],
        "icons": [0x637A5D56132F3C01, 0x29FFA08309CC8487, 0xCEF22606FDC14962],
        "description": 0xF839C9B3
    },
    "SET_SPRINGROLL_NATURAL": {
        "name": "Springroll's Natural Recolors",
        "names": [0xE8A1E996, 0x705F5DFE, 0xBD25B899],
        "icons": [0x3C1E9854C7268467, 0xC376CFF094CDC1A6, 0x855109C93AD4114B],
        "description": 0x5F240276
    },
    "SET_SPRINGROLL_SORBET": {
        "name": "SaveState's Sorbet Recolors Mod",
        "names": [0xB871C768, 0x48490BFC, 0xACFE1401],
        "icons": [0x3C1E9854C7268467, 0xC376CFF094CDC1A6, 0x855109C93AD4114B],
        "description": 0xFAC73EED
    },
    "SET_SORAFOXYTEILS": {
        "name": "SoraFoxyTeil's Furry CC",
        "names": [0xB5A3A547, 0x45CFA4C0, 0x4B10002E],
        "icons": [0xD4C0A0069F37E131, 0xC00355220308DACD, 0xFFF9F3F89B37B3AB],
        "description": 0x2486BC51
    },
    "SET_SPRINGROLL_EXTRA": {
        "name": "Springroll's Extras",
        "names": [0x1B3D00D5, 0x61EDE9A1, 0x8BEDC295],
        "icons": [0x3C1E9854C7268467, 0xC376CFF094CDC1A6, 0x855109C93AD4114B],
        "description": 0xF07F375C
    },
    "SET_CYANGEOM_KIDS": {
        "name": "Cyangeom's Furry Kids",
        "names": [0xED3B1FA9, 0xF632A38E, 0x8A4B5428],
        "icons": [0x8563128D8C73BEAF, 0xB569491D9DF45861, 0xF8AC37A4E84D16E0],
        "description": 0x5C4E5306
    },
    "SET_BERNISE": {
        "name": "Berni's Collection",
        "names": [0x99C5A309, 0x188158E5, 0x12788F8F],
        "icons": [0x47E733B7695D730E, 0x6AB852DBE387A2D9, 0x14DB0650401C2545],
        "description": 0x72B53F5C
    },
    "SET_TOMJJ_1": {
        "name": "Tomjj's Extra Furry Mods #1",
        "names": [0x6F65C99C, 0xA0CC6B00, 0x6357C94F],
        "icons": [0x5C96AEA8FB325DE8, 0x448142E93CFB7D22, 0x56782C56C28A34FA],
        "description": 0xA313594F
    },
    "SET_TOMJJ_2": {
        "name": "Tomjj's Extra Furry Mods #2",
        "names": [0xE9852BBE, 0x49A7B02F, 0x08B307FF],
        "icons": [0x5C96AEA8FB325DE8, 0x448142E93CFB7D22, 0x56782C56C28A34FA],
        "description": 0xB41ED3E0
    },
    "SET_LELJAS_HEADS": {
        "name": "Lelja's SaveState Addons",
        "names": [0xB96DA2E3, 0x8F3EB22C, 0xA785D395],
        "icons": [0x1B056546A4F81980, 0x1FFFD33D01BD81E7, 0xCB50E183592CCC9D],
        "description": 0x82F0F791
    },
    "SET_ANIMATED_TAILS": {
        "name": "SDMSims' Animated Tails",
        "names": [0xD62917AB, 0xEB1D9385, 0x63A321D8],
        "icons": [0x853333333166B2BC, 0x25F563B39BA8A0B8, 0x4DE477B35D9E3CAA],
        "description": 0xDFA1744D
    },
    "SET_INVISIBLE_CLOTHES": {
        "name": "Simply Invisible Clothes",
        "names": [0x6D4802C3, 0x251B467C, 0xDAA7206F],
        "icons": [0x64581048C03C6391, 0xF0EFBDF7837B9695, 0x057EBA3E12DBE441],
        "description": 0x6148566E
    }
}
hidden_sets = {"SET_INVISIBLE_CLOTHES", "SET_BERNISE"}
status_indices = ["Installed", "Partially Installed", "Uninstalled"]


def detect_sets():
    try:
        for cc_set in sets.values():
            cc_set: dict
            cc_set["missing_files"] = set()
            cc_set['found_files'] = set()

        for category in get_register_parts().values():
            if "part_options" in category:
                for part in category["part_options"].values():
                    if 'flags' in part and 'ids' in part and 'file' in part:
                        test_item(part['ids'], part['flags'], part['file'])

        for category in get_register_special_deletions().values():
            for part in category.values():
                if 'flags' in part and 'ids' in part and 'file' in part:
                    test_item(part['ids'], part['flags'], part['file'])

        for category in get_register_substitutes().values():
            for part in category.values():
                if 'flags' in part and 'ids' in part and 'file' in part:
                    test_item([part['ids']], part['flags'], part['file'])

        # Test each set and save the results
        for cc_set in sets.values():
            process_results(cc_set)

        # Send status to logger
        cache_status(get_status_str())

        if get_set_status("SET_SAVESTATE") != "Installed":
            show_notification(
                f"The Furrifier requires SaveState's Furry Mod to be fully installed to run. {get_sets_status()['SET_SAVESTATE']['message']}",
                title="Missing Requirements!", notif_type='exception')

    except (Exception,):
        log_exception()


def test_item(ids, flags, name):
    for flag in flags:
        if flag == FurryFlag.SET_SAVESTATE:
            if not is_part_installed(first_real(ids[0:12])):
                sets["SET_SAVESTATE"]["missing_files"].add(f"{name}.package")
            else:
                sets["SET_SAVESTATE"]["found_files"].add(f"{name}.package")
            if FurryFlag.FORMAT_FULL in flags:
                if not is_part_installed(first_real(ids[13:57])):
                    sets["SET_SPRINGROLL_NATURAL"]["missing_files"].add(f"{name}.package")
                else:
                    sets["SET_SPRINGROLL_NATURAL"]["found_files"].add(f"{name}.package")

                if not is_part_installed(first_real(ids[61:])):
                    sets["SET_SPRINGROLL_SORBET"]["missing_files"].add(f"{name}.package")
                else:
                    sets["SET_SPRINGROLL_SORBET"]["found_files"].add(f"{name}.package")

        elif FurryFlag(flag).name.startswith("SET_"):
            if not is_part_installed(first_real(ids)):
                sets[FurryFlag(flag).name]["missing_files"].add(f"{name}.package")
            else:
                sets[FurryFlag(flag).name]["found_files"].add(f"{name}.package")


def process_results(cc_set: dict):
    max_listed_missing = 10
    max_listed_found = 3

    if len(cc_set['missing_files']) == 0:
        cc_set["status"] = "Installed"
        cc_set["message"] = f"{cc_set['name']} is installed, having all {len(cc_set['found_files'])} supported files."
    elif len(cc_set['found_files']) != 0:
        cc_set["status"] = "Partially Installed"
        cc_set["message"] = f"{cc_set['name']} is missing {', '.join(list(cc_set['missing_files'])[:max_listed_missing])}" + (f" and {len(cc_set['missing_files'])-max_listed_missing} more" if len(cc_set['missing_files']) > max_listed_missing else '')
        cc_set["message"] += f".\n\nHowever, it does have {', '.join(list(cc_set['found_files'])[:max_listed_found])}" + (f" and {len(cc_set['found_files'])-max_listed_found} more" if len(cc_set['found_files']) > max_listed_found else '') + " installed."
    else:
        cc_set["status"] = "Uninstalled"
        cc_set["message"] = f"{cc_set['name']} is missing all {len(cc_set['missing_files'])} supported files."


def get_status_index(status: str):
    return status_indices.index(status)


def get_sets_status():
    return sets


def get_set_status(cc_set):
    return sets[cc_set]['status']


def get_status_str():
    result = ""
    for cc_set in sets.values():
        result += f"{cc_set['name']}: {cc_set['status']} {' (' + cc_set['message'] + ')' if cc_set['status'] == 'Partially Installed' else ''}\n"

    return result


# Always detect the sets when the game loads
detect_sets()
