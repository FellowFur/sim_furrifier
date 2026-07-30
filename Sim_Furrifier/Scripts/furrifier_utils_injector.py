import copy
from functools import wraps
import services

import sims4.resources
from sims4.tuning.instance_manager import InstanceManager
from sims4.resources import Types
from sims.sim import Sim
from clock import GameClock
from sims.sim_info import SimInfo
from zone import Zone

from furrifier_api import furrify_world
from furrifier_sim_info import get_true_form, get_disguise
from furrifier_sim_wrapper import FurrySimWrapper
from furrifier_sim_data_manager import can_be_furrified, is_furry, has_disguise, get_furry_parts, \
    get_sim_species_from_parts, should_stay_human
from furrifier_sim_trait_manager import mark_exempt, is_exempt, has_furrifier_traits
from furrifier_configs_settings_handler import is_automatic, is_eye_fixing, is_setting_on, are_genetics_furry
from furrifier_utils_notifier import print_saved_messages, show_notification
from furrifier_utils_logger import log_exception, start_log, close_log


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


# Runs the automatic furrifier on all sims
@inject_to(Sim, 'on_add')
def on_sim_instanced(original, self, *args, **kwargs):
    result = original(self, *args, **kwargs)
    try:
        if (is_automatic() and not is_furry(self.sim_info) and not is_exempt(self.sim_info)) and can_be_furrified(self.sim_info, is_auto=True)[0]:
            furry_sim = FurrySimWrapper(self.sim_info, is_auto=True)
            furry_sim.initialize_log()
            furry_sim.initialize_info()

            if not should_stay_human():
                furry_sim.furrify('default')
            else:
                mark_exempt(self.sim_info)

            # Also do disguise too, if applicable
            if has_disguise(self.sim_info):
                furry_sim.initialize_log()
                furry_sim.initialize_info(is_disguise=True)

                if not should_stay_human():
                    furry_sim.furrify('default')
                else:
                    mark_exempt(self.sim_info)

        if is_eye_fixing() and is_furry(self.sim_info):
            furry_sim = FurrySimWrapper(self.sim_info, is_auto=True)
            furry_sim.initialize_info(include_current_species=True, include_current_parts=True)
            furry_sim.reset_sculpts()

            # Also do disguise too, if applicable
            if has_disguise(self.sim_info):
                furry_sim.initialize_info(include_current_species=True, include_current_parts=True, is_disguise=True)
                furry_sim.reset_sculpts()
    except (Exception,):
        log_exception(self.sim_info)
    return result


# When the game loads, print any issues that happened during the loading screen
@inject_to(Zone, 'on_loading_screen_animation_finished')
def on_loading_screen(original, self, *args, **kwargs):
    try:
        # If the game is brand new, furrify world
        if is_automatic() and (int(services.game_clock_service().now()) - int(GameClock.NEW_GAME_START_TIME().absolute_ticks()) < 1000):
            furrify_world()
    except (Exception,):
        pass
    result = original(self, *args, **kwargs)
    try:
        print_saved_messages()
    except (Exception,):
        pass
    return result


# when a sim ages up, furrify them instantly or copy parts
@inject_to(SimInfo, 'change_age')
def on_sim_aged(original, self, new_age, current_age, *args, **kwargs):
    old_true_parts, old_disguise_parts = [], []
    old_true_tags, old_disguise_tags = [], []
    old_true_species, old_disguise_species = "", ""
    is_sim_furry = None

    try:
        is_sim_furry = is_furry(self)

        # # If a sim is younger than teen and ages into anything older, copy parts over if that setting is on
        if is_sim_furry and is_setting_on("settings", "auto_aging") and (new_age > current_age):
            start_log(self, "Attempting to age up sim")
            old_true_parts = get_furry_parts(get_true_form(self))
            temp_wrapper = FurrySimWrapper(self.sim_info, is_auto=True)
            if has_disguise(self):
                old_disguise_parts = get_furry_parts(get_disguise(self))

            if old_true_parts:
                old_true_species = get_sim_species_from_parts(old_true_parts)
                temp_wrapper.initialize_info(include_current_species=True)
                old_true_tags = copy.copy(temp_wrapper.furry_sim_info.tags)
            if old_disguise_parts:
                old_disguise_species = get_sim_species_from_parts(old_disguise_parts)
                temp_wrapper.initialize_info(is_disguise=True, include_current_species=True)
                old_disguise_tags = copy.copy(temp_wrapper.furry_sim_info.tags)

    except (Exception,):
        log_exception(self)

    # Do the aging
    result = original(self, new_age, current_age, *args, **kwargs)

    try:
        # Re-apply new parts to aged young sims
        if old_true_species or old_disguise_species:
            if old_true_species:
                furry_sim = FurrySimWrapper(self.sim_info, is_auto=True)
                furry_sim.initialize_log()
                furry_sim.initialize_info()
                furry_sim.furrify_age_up(age_up_species=old_true_species, age_up_parts=old_true_parts, old_tags=old_true_tags)

            # Also do disguise too, if applicable
            if old_disguise_species:
                furry_sim_disguise = FurrySimWrapper(self.sim_info, is_auto=True)
                furry_sim_disguise.initialize_log()
                furry_sim_disguise.initialize_info(is_disguise=True)
                furry_sim_disguise.furrify_age_up(age_up_species=old_disguise_species, age_up_parts=old_disguise_parts, old_tags=old_disguise_tags)

        # If a sim is not furry, but has furry parents in genetic mode
        # TODO: Fix this working in wrong situations
        elif are_genetics_furry() and not is_sim_furry:
            if can_be_furrified(self.sim_info, is_auto=True, is_age_up=True)[0]:
                furry_sim = FurrySimWrapper(self.sim_info, is_auto=True)
                furry_sim.initialize_log()
                furry_sim.initialize_info()
                furry_sim.furrify('genetic')
                del furry_sim

            # Also do disguise too, if applicable
            if has_disguise(self.sim_info) and can_be_furrified(self.sim_info, is_auto=True, is_disguise=True, is_age_up=True)[0]:
                furry_sim = FurrySimWrapper(self.sim_info, is_auto=True)
                furry_sim.initialize_log()
                furry_sim.initialize_info(is_disguise=True)
                furry_sim.furrify('genetic')
                del furry_sim

        # Reset sculpts, really only needed if no changes were made to sims
        if is_sim_furry:
            furry_sim = FurrySimWrapper(self.sim_info, is_auto=True)
            furry_sim.initialize_log()
            furry_sim.initialize_info()
            furry_sim.reset_sculpts()
            del furry_sim

            # Also do disguise too, if applicable
            if has_disguise(self.sim_info):
                furry_sim = FurrySimWrapper(self.sim_info, is_auto=True)
                furry_sim.initialize_log()
                furry_sim.initialize_info(is_disguise=True)
                furry_sim.reset_sculpts()
                del furry_sim

        close_log('Finished age up checks')
    except (Exception,):
        log_exception(self)

    return result


# This injects the mod's interactions onto sims using the Tuning Ids
# Conditional interactions are only added if the user has the sets installed
ObjectIds = (14965,)
InteractionIds = (14135278356521161258, 16610431812688285778, 9447994638447255063, 17623645358402758936, 10854913771936126660, 10607654428390850878, 9854099370791759039, 16480155531685599382)


# For storing interactions I'm testing and may not be included long term
# TestInteractionIds = ()
# InteractionIds += TestInteractionIds


@inject_to(InstanceManager, 'load_data_into_class_instances')
def AddInteractions(original, self, *args, **kwargs):
    original(self, *args, **kwargs)

    if self.TYPE == Types.OBJECT:
        affordance_manager = services.affordance_manager()
        sa_list = []
        for sa_id in InteractionIds:
            key = sims4.resources.get_resource_key(sa_id, Types.INTERACTION)
            sa_tuning = affordance_manager.get(key)
            if sa_tuning is not None:
                sa_list.append(sa_tuning)
        sa_tuple = tuple(sa_list)
        for obj_id in ObjectIds:
            key = sims4.resources.get_resource_key(obj_id, Types.OBJECT)
            obj_tuning = self._tuned_classes.get(key)
            if obj_tuning is not None:
                # noinspection PyProtectedMember
                obj_tuning._super_affordances = obj_tuning._super_affordances + sa_tuple
