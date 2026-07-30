import services
from functools import wraps

from ui.ui_dialog_notification import UiDialogNotification
from sims4.localization import LocalizationHelperTuning
from zone import Zone


# Track messages to display when the game loads
saved_messages = []


def notify_missing_requirements(text: str, title:str):
    # From Scumbumbo's tutorial: https://modthesims.info/t/544445
    try:
        client = services.client_manager().get_first_client()
    except (Exception,):
        saved_messages.append((text, title))
        return

    localized_title = lambda **_: LocalizationHelperTuning.get_raw_text(title)
    localized_text = lambda **_: LocalizationHelperTuning.get_raw_text(text)

    urgency = UiDialogNotification.UiDialogNotificationUrgency.URGENT
    information_level = UiDialogNotification.UiDialogNotificationLevel.PLAYER
    visual_type = UiDialogNotification.UiDialogNotificationVisualType.INFORMATION

    # Prepare and show the notification.
    notification = UiDialogNotification.TunableFactory().default(client.active_sim, text=localized_text, title=localized_title, urgency=urgency, information_level=information_level, visual_type=visual_type)
    notification.show_dialog()


# Code from https://frankkmods.medium.com/automatically-assign-traits-to-sims-sims-4-script-modding-60f8eeb2a08c
def inject(target_function, new_function):
    @wraps(target_function)
    def _inject(*args, **kwargs):
        return new_function(target_function, *args, **kwargs)

    return _inject


def inject_to(target_object, target_function_name):
    def _inject_to(new_function):
        target_function = getattr(target_object, target_function_name)
        setattr(target_object, target_function_name, inject(target_function, new_function))
        return new_function

    return _inject_to


# When the game loads, print any issues that happened during the loading screen
@inject_to(Zone, 'on_loading_screen_animation_finished')
def on_loading_screen(original, self, *args, **kwargs):
    result = original(self, *args, **kwargs)
    try:
        global saved_messages
        for message in saved_messages:
            notify_missing_requirements(message[0], message[1])
        saved_messages = []
    except (Exception,):
        pass
    return result
