from furrifier_utils_basics import get_game_version, is_game_version_valid
from furrifier_utils_enums import expected_game_version, expected_update_date, expected_update_name
from furrifier_utils_notifier import show_notification

# Validate game version
game_version = get_game_version()

if not game_version:
    pass
    # I don't care anymore
    # show_notification(f"The Furrifier could not check your game version. The version you are using may not be compatible with the Furrifier, which could cause major issues. The Furrifier expects at least game version {expected_game_version} from the {expected_update_name} update on {expected_update_date}.", notif_type="exception", title="Unknown game version")
else:
    try:
        game_valid = is_game_version_valid(expected_game_version, game_version)

        if not game_valid:
            show_notification(f"The Furrifier is not compatible with your game version and will encounter major issues. You are using game version {game_version}, but the Furrifier expects at least game version {expected_game_version} from the {expected_update_name} update on {expected_update_date}.", notif_type="exception", title="Unknown game version")
    except ValueError:
        pass
