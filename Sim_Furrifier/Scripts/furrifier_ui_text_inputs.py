from interactions.base.immediate_interaction import ImmediateSuperInteraction
from sims4.tuning.tunable import Tunable
from ui.ui_dialog_generic import UiDialogTextInputOkCancel
from sims4.localization import _create_localized_string, TunableLocalizedStringFactory, LocalizationHelperTuning
from furrifier_configs_settings_handler import update_setting, get_setting_value
from furrifier_utils_notifier import show_notification
from furrifier_utils_basics import run_interaction

lazy_value_passthrough = ''


class FurrifierTextInput(UiDialogTextInputOkCancel):
    def build_msg(self, text_input_overrides=None, additional_tokens=(), **kwargs):
        msg = super().build_msg(additional_tokens=additional_tokens, **kwargs)

        my_text_input_msg = msg.text_input.add()
        my_text_input_msg.text_input_name = 'setting_value'
        my_text_input_msg.initial_value = LocalizationHelperTuning.get_raw_text(lazy_value_passthrough)

        return msg

    def on_text_input(self, text_input_name='', text_input=''):
        self.text_input_responses[text_input_name] = text_input
        return True


class FurrifierNumInputInteraction(ImmediateSuperInteraction):
    INSTANCE_TUNABLES = {
        'title': TunableLocalizedStringFactory(description="The input's title"),
        'text': TunableLocalizedStringFactory(description="The input's title"),
        'category': Tunable(
            description="The category to input the value for",
            tunable_type=str,
            default=""),
        'setting': Tunable(
            description="The setting to input the value for",
            tunable_type=str,
            default=""),
        'min': Tunable(
            description="The minimum number input",
            tunable_type=int,
            default=0),
        'max': Tunable(
            description="The maximum number input",
            tunable_type=int,
            default=100),
        'continuation': Tunable(
            description="The interaction to run once finished",
            tunable_type=int,
            default=0)
    }

    def _run_interaction_gen(self, timeline):
        global lazy_value_passthrough
        lazy_value_passthrough = get_setting_value(self.category, self.setting)

        input_dialog = FurrifierTextInput.TunableFactory().default(
            self.target,
            title=self.title,
            text=self.text,
            text_ok=lambda *_, **__: _create_localized_string(0xC42DA253, *()),
            text_cancel=lambda *_, **__: _create_localized_string(0x91BC5100, *()),
        )

        def input_callback_func(dialog):
            if dialog is not None:
                output = dialog.text_input_responses.get('setting_value')
                try:
                    if self.min <= int(output) <= self.max:
                        update_setting(self.category, self.setting, str(output))
                    else:
                        show_notification(f"Input out of valid range ({self.min}, {self.max})")

                except (Exception, ):
                    show_notification("Input is not a number")

            run_interaction(int(self.continuation), self.target)

        input_dialog.add_listener(input_callback_func)
        input_dialog.show_dialog()


