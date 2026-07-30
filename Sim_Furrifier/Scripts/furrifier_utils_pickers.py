from furrifier_res_premades import premades_data
from interactions.base.picker_interaction import PickerSuperInteraction
from sims4.localization import LocalizationHelperTuning, _create_localized_string
from sims4.resources import get_resource_key, Types
from sims4.tuning.tunable import Tunable
from sims4.utils import flexmethod
from ui.ui_dialog_picker import ObjectPickerRow

from furrifier_configs_register_handler import get_register_species_categories, get_register_presets
from furrifier_configs_settings_detector import get_sets_status, hidden_sets, get_status_index
from furrifier_sim_species_manager import get_species_icon
from furrifier_sim_wrapper import FurrySimWrapper
from furrifier_utils_basics import run_interaction
from furrifier_utils_notifier import show_notification
from furrifier_utils_logger import log_exception
from furrifier_api import furrify

# Keep track of categories and data when moving from Category Picker to Species Picker
picked_category = None
furry_sim = None
target_setting = None


class SpeciesCategoryPickerSuperInteraction(PickerSuperInteraction):
    INSTANCE_TUNABLES = {'is_disguise': Tunable(description='\n                If this interaction is targeting an alien\n                sim\'s disguise', tunable_type=bool, default=False)}

    def _run_interaction_gen(self, timeline):
        global furry_sim
        furry_sim = FurrySimWrapper(self.target.sim_info)
        furry_sim.initialize_info(self.is_disguise)

        self._show_picker_dialog(self.sim, target_sim=self.target)
        return True

    @classmethod
    def _preset_selection_gen(cls, target):
        presets = get_register_presets()

        target_name = ""
        if furry_sim.furry_sim_info.premade_identification is not None and furry_sim.furry_sim_info.premade_identification in presets:
            target_name = furry_sim.furry_sim_info.premade_identification
        elif furry_sim.furry_sim_info.name not in premades_data and furry_sim.furry_sim_info.name in presets:
            target_name = furry_sim.furry_sim_info.name

        if target_name:
            for preset_name, preset in presets[target_name].items():
                if 'requires' not in preset or preset['requires'].passes(furry_sim.furry_sim_info.tags):
                    if 'species' in preset:
                        yield preset_name, get_species_icon(preset['species'])
                    else:
                        yield preset_name, 0x25eea5cdba6a6fd6

    @classmethod
    def _category_selection_gen(cls, target):
        categories = get_register_species_categories()

        for category_name, category_value in categories.items():
            if any(('requires' not in species or species['requires'].passes(furry_sim.furry_sim_info.tags)) for species in category_value['species'].values()):
                yield category_name, category_value

    @flexmethod
    def picker_rows_gen(cls, inst, target, context, **kwargs):
        try:
            # First generate from presets
            for preset_name, preset_icon in cls._preset_selection_gen(target):
                localized_name = LocalizationHelperTuning.get_raw_text(preset_name.replace("_", " "))
                icon = get_resource_key(preset_icon, Types.PNG)
                row = ObjectPickerRow(name=localized_name, icon=icon, tag=f"preset_{preset_name}")
                yield row

            # Then next two rows are hard coded
            yield ObjectPickerRow(name=_create_localized_string(0x7C990BE2, *()), icon=get_resource_key(0x6016FEA4CE34B5F2, Types.PNG), tag="&genetic")
            yield ObjectPickerRow(name=_create_localized_string(0xFC4A0A31, *()), icon=get_resource_key(0x94bd5a6ddae17f80, Types.PNG), tag="&random")

            # Rest are generated from categories
            for category_name, category_value in cls._category_selection_gen(target):
                # Use localized name if exists
                if 'localized_name_id' in category_value and category_value['localized_name_id']:
                    localized_name = _create_localized_string(category_value['localized_name_id'], *())
                else:
                    localized_name = LocalizationHelperTuning.get_raw_text(category_name)

                # Use custom icon if exists
                if 'icon_id' in category_value and category_value['icon_id']:
                    icon = get_resource_key(category_value['icon_id'], Types.PNG)
                else:
                    icon = get_resource_key(0xC20CDF8B9BBB3413, Types.PNG)

                row = ObjectPickerRow(name=localized_name, icon=icon, tag=category_name)
                yield row

            # Last is generic presets, if they exist
            presets_data = get_register_presets()
            if "GENERIC" in presets_data and any(('requires' not in preset or preset['requires'].passes(furry_sim.furry_sim_info.tags)) for preset in presets_data['GENERIC'].values()):
                yield ObjectPickerRow(name=_create_localized_string(0x8A76B377, *()), icon=get_resource_key(0x5A0E4DA0DF3E7F12, Types.PNG), tag="&generic")

        except (Exception,):
            log_exception(furry_sim.furry_sim_info.base_sim_info)

    def on_choice_selected(self, choice_tag, **kwargs):
        if choice_tag == '&random':
            furrify(self.target.sim_id, 'random', self.is_disguise)
        elif choice_tag == '&genetic':
            furrify(self.target.sim_id, 'genetic', self.is_disguise)
        elif choice_tag.startswith('preset_'):
            furrify(self.target.sim_id, choice_tag, self.is_disguise)
        elif choice_tag:
            global picked_category
            picked_category = choice_tag

            run_interaction(15912097529793873142, self.target)


class SpeciesPickerSuperInteraction(PickerSuperInteraction):
    INSTANCE_TUNABLES = {}

    def _run_interaction_gen(self, timeline):
        self._show_picker_dialog(self.sim, target_sim=self.target)
        return True

    @classmethod
    def _species_selection_gen(cls, target):
        species = get_register_species_categories()[picked_category]['species']

        for species_name, species_value in species.items():
            if 'requires' not in species_value or species_value['requires'].passes(furry_sim.furry_sim_info.tags):
                yield species_name, species_value

    @classmethod
    def _preset_selection_gen(cls, target):
        presets = get_register_presets()["GENERIC"]

        for preset_name, preset in presets.items():
            if 'requires' not in preset or preset['requires'].passes(furry_sim.furry_sim_info.tags):
                if 'species' in preset:
                    yield preset_name, get_species_icon(preset['species'])
                else:
                    yield preset_name, 0x25eea5cdba6a6fd6

    @flexmethod
    def picker_rows_gen(cls, inst, target, context, **kwargs):
        if picked_category != "&generic":
            for species_name, species_value in cls._species_selection_gen(target):
                # Use localized name if exists
                if 'localized_name_id' in species_value and species_value['localized_name_id']:
                    localized_name = _create_localized_string(species_value['localized_name_id'], *())
                else:
                    species_name_formatted = ' '.join([word.capitalize() for word in species_name.split('_')])
                    localized_name = LocalizationHelperTuning.get_raw_text(species_name_formatted)

                # Use custom icon if exists
                icon = get_resource_key(get_species_icon(species_name), Types.PNG)

                row = ObjectPickerRow(name=localized_name, icon=icon, tag=species_name)
                yield row
        else:
            for preset_name, preset_icon in cls._preset_selection_gen(target):
                localized_name = LocalizationHelperTuning.get_raw_text(preset_name.replace("_", " "))
                icon = get_resource_key(preset_icon, Types.PNG)
                row = ObjectPickerRow(name=localized_name, icon=icon, tag=f"preset_{preset_name}")
                yield row
        # Also yield a return option
        yield ObjectPickerRow(name=_create_localized_string(0x91BC5100, *()), icon=get_resource_key(0x60C405032F673ABD, Types.PNG), tag="&back")

    def on_choice_selected(self, choice_tag, **kwargs):
        if choice_tag == '&back':
            if furry_sim.furry_sim_info.is_disguise:
                run_interaction(17650273949800915701, self.target)
            else:
                run_interaction(15391867170294818878, self.target)
        elif choice_tag:
            furrify(self.target.sim_id, choice_tag, furry_sim.furry_sim_info.is_disguise)


class CCManagementMenuSuperInteraction(PickerSuperInteraction):
    INSTANCE_TUNABLES = {}

    def _run_interaction_gen(self, timeline):
        self._show_picker_dialog(self.sim, target_sim=self.target)
        return True

    @classmethod
    def _cc_selection_gen(cls, target):
        sets = get_sets_status()

        for set_name, cc_set in sets.items():
            if not (cc_set["status"] == "Uninstalled" and set_name in hidden_sets):
                yield cc_set

    @flexmethod
    def picker_rows_gen(cls, inst, target, context, **kwargs):
        for cc_set in cls._cc_selection_gen(target):
            index = get_status_index(cc_set['status'])
            localized_name = _create_localized_string(cc_set['names'][index], *())
            localized_description = _create_localized_string(cc_set['description'], *())
            icon = get_resource_key(cc_set['icons'][index], Types.PNG)

            row = ObjectPickerRow(name=localized_name, icon=icon, row_description=localized_description, tag=cc_set['message'])
            yield row
        # Also yield a return option
        yield ObjectPickerRow(name=_create_localized_string(0x91BC5100, *()), icon=get_resource_key(0x60C405032F673ABD, Types.PNG), tag="&back")

    def on_choice_selected(self, choice_tag, **kwargs):
        if choice_tag == '&back':
            run_interaction(10083237513987803773, self.target)
        elif choice_tag:
            show_notification(choice_tag, title="CC Installation Status")


# class FurrifierSettingsSuperInteraction(PickerSuperInteraction):
#     INSTANCE_TUNABLES = {'setting': Tunable(description='\n                The initial setting to display', tunable_type=str, default="misc")}
#
#     def _run_interaction_gen(self, timeline):
#         self._show_picker_dialog(self.sim, target_sim=self.target)
#         global target_setting
#         try:
#             if self.setting != "custom":
#                 target_setting = (self.setting, get_setting_layout(self.setting))
#         except ValueError:
#             log_exception()
#         return True
#
#     @classmethod
#     def _setting_selection_gen(cls, target):
#         for setting_name, setting_value in target_setting[1]['contains'].items():
#             yield (cls.setting + setting_name), setting_value
#
#     @flexmethod
#     def picker_rows_gen(cls, inst, target, context, **kwargs):
#         for setting_name, setting_value in cls._setting_selection_gen(target):
#             if 'values' in setting_value:
#                 setting_index = get_current_setting_index(setting_name, setting_value)
#                 localized_name = _create_localized_string(setting_value['names'][setting_index], *())
#                 icon = get_resource_key(setting_value['icons'][setting_index], Types.PNG)
#             else:
#                 localized_name = _create_localized_string(setting_value['name'], *())
#                 icon = get_resource_key(setting_value['icon'], Types.PNG)
#
#             localized_description = _create_localized_string(setting_value['description'], *())
#
#             row = ObjectPickerRow(name=localized_name, icon=icon, row_description=localized_description, tag=setting_name)
#             yield row
#         # Also yield a return option
#         yield ObjectPickerRow(name=_create_localized_string(0x91BC5100, *()), icon=get_resource_key(0x989068A74AA4B221, Types.PNG), tag="&back")
#
#     def on_choice_selected(self, choice_tag, **kwargs):
#         global target_setting
#         if choice_tag == '&back':
#             # Replace target
#             run_interaction(17650273949800915701, self.target)
#         elif choice_tag:
#             choice = get_setting_layout(choice_tag)
#             if choice['type'] == 'toggle':
#                 toggle_setting(choice_tag)
#                 # change to be current interation
#                 run_interaction(17650273949800915701, self.target)
#             elif choice['type'] == 'set':
#                 setting_category, setting = choice['target'].split('.', 1)
#
#                 update_setting(setting_category, setting, choice_tag)
#                 target_setting = (choice['target'], get_setting_layout(choice['target']))
#                 run_interaction(17650273949800915701, self.target)
#             elif choice['type'] == 'category' or choice['type'] == 'hybrid':
#                 target_setting = (choice_tag, choice)
#                 run_interaction(17650273949800915701, self.target)
#             elif choice['type'] == 'action':
#                 run_interaction(choice['interaction'], self.target)
#             else:
#                 raise ValueError(f"Setting {choice_tag} has no valid type")
