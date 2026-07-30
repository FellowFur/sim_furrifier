import services

from distributor.shared_messages import IconInfoData
from ui.ui_dialog_notification import UiDialogNotification
from sims4.localization import LocalizationHelperTuning
from sims4.resources import Types, get_resource_key


# Track messages to display when the game loads
saved_messages = []


def show_notification(text: str, notif_type='confirm', title=None):
    """
    Displays a notification

    Args:
        text (str): The notification's text
        notif_type (str): The type of the notification
        title (str): The title of the notification
    """
    # Make string if not already
    text = str(text)

    # From Scumbumbo's tutorial: https://modthesims.info/t/544445
    try:
        client = services.client_manager().get_first_client()
    except (Exception,):
        saved_messages.append((text, notif_type, title))
        return

    if title is None:
        localized_title = lambda **_: LocalizationHelperTuning.get_raw_text("Furrifier Notification")
    else:
        localized_title = lambda **_: LocalizationHelperTuning.get_raw_text(title)

    localized_text = lambda **_: LocalizationHelperTuning.get_raw_text(text)

    if notif_type == 'exception':
        icon_key = get_resource_key(0x5C0C49DC69C2B652, Types.PNG)
    else:
        icon_key = get_resource_key(0xC20CDF8B9BBB3413, Types.PNG)
    icon = lambda _: IconInfoData(icon_resource=icon_key)

    if notif_type == 'confirm':
        urgency = UiDialogNotification.UiDialogNotificationUrgency.DEFAULT
        information_level = UiDialogNotification.UiDialogNotificationLevel.SIM
        visual_type = UiDialogNotification.UiDialogNotificationVisualType.INFORMATION
    elif notif_type == 'exception':
        urgency = UiDialogNotification.UiDialogNotificationUrgency.URGENT
        information_level = UiDialogNotification.UiDialogNotificationLevel.PLAYER
        visual_type = UiDialogNotification.UiDialogNotificationVisualType.INFORMATION
    else:
        urgency = UiDialogNotification.UiDialogNotificationUrgency.DEFAULT
        information_level = UiDialogNotification.UiDialogNotificationLevel.PLAYER
        visual_type = UiDialogNotification.UiDialogNotificationVisualType.INFORMATION

    # Prepare and show the notification.
    notification = UiDialogNotification.TunableFactory().default(client.active_sim, text=localized_text,
                                                                 title=localized_title, icon=icon, urgency=urgency,
                                                                 information_level=information_level,
                                                                 visual_type=visual_type)
    notification.show_dialog()


def print_saved_messages():
    """
    Prints all messages that would have been displayed during a loading screen
    """
    global saved_messages
    for message in saved_messages:
        show_notification(message[0], message[1], message[2])
    saved_messages = []
