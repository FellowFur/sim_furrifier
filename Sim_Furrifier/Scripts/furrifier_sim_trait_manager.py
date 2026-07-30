import services

from furrifier_sim_info import FurrySimInfo, get_sim_category, FurrySimCategory
from furrifier_configs_settings_handler import get_setting_value
from furrifier_utils_logger import log_text, change_indent
from furrifier_utils_enums import FurryTag
from furrifier_utils_basics import are_equal

from sims.sim_info import SimInfo
from sims4.resources import Types


class FurrySimTraitManager:
    def __init__(self, furry_sim_info: FurrySimInfo):
        self.furry_sim_info = furry_sim_info

    def update_furrifier_traits(self):
        # Add the traits
        log_text("\nManaging Sim Traits:")
        change_indent(1)
        if not self.furry_sim_info.is_disguise:
            self.update_furry_traits()

            # Disable hair growth and/or lactation if enabled
            if FurryTag.FURRYTYPE_HUMAN not in self.furry_sim_info.tags:
                self.update_hair_growth()
                self.update_lactation()

        # Cycle plant sims to make changes appear
        self.cycle_plant_sim()

        change_indent(-1)

    def update_furry_traits(self):
        update_furry_traits(self.furry_sim_info.base_sim_info, self.furry_sim_info.tags)

    def clear_furrifier_traits(self):
        trait_manager = services.get_instance_manager(Types.TRAIT)
        trait_ids = [16979007351164161671, 10841828803585111305, 11960148769534105407, 12283065628421974891, 16710384910426247548, 16653425920695034766, 9619142357741996824, 18365742668114966688]
        traits = [trait_manager.get(trait_id) for trait_id in trait_ids]

        for trait in traits:
            if self.furry_sim_info.base_sim_info.has_trait(trait):
                self.furry_sim_info.base_sim_info.remove_trait(trait)

        log_text("Cleared all furry traits")

    def update_hair_growth(self):
        disable_facial = get_setting_value('autoremovals', 'facial_hair')
        disable_body = get_setting_value('autoremovals', 'body_hair')

        trait_manager = services.get_instance_manager(Types.TRAIT)
        no_body_hair_scaly_trait = trait_manager.get(16653425920695034766)
        no_body_hair_furry_trait = trait_manager.get(9619142357741996824)
        no_facial_hair_trait = trait_manager.get(18365742668114966688)

        # First remove any existing traits
        if self.furry_sim_info.base_sim_info.has_trait(no_facial_hair_trait):
            self.furry_sim_info.base_sim_info.remove_trait(no_facial_hair_trait)
            log_text("Enabled Facial Hair")

        if self.furry_sim_info.base_sim_info.has_trait(no_body_hair_furry_trait):
            self.furry_sim_info.base_sim_info.remove_trait(no_body_hair_furry_trait)
            log_text("Enabled Body Hair")
        if self.furry_sim_info.base_sim_info.has_trait(no_body_hair_scaly_trait):
            self.furry_sim_info.base_sim_info.remove_trait(no_body_hair_scaly_trait)
            log_text("Enabled Body Hair")

        # Then add in new traits
        if are_equal(disable_facial, 'True'):
            self.furry_sim_info.base_sim_info.add_trait(no_facial_hair_trait)
            log_text("Disabled Facial Hair")

        if are_equal(disable_body, 'True') or are_equal(disable_body, 'scaly'):
            if FurryTag.FURRYTYPE_SCALY in self.furry_sim_info.tags or FurryTag.FURRYTYPE_FEATHERY in self.furry_sim_info.tags:
                self.furry_sim_info.base_sim_info.add_trait(no_body_hair_scaly_trait)
                log_text("Disabled Body Hair")
            elif disable_body == 'True':
                self.furry_sim_info.base_sim_info.add_trait(no_body_hair_furry_trait)
                log_text("Disabled Body Hair")

    def update_lactation(self):
        is_disabled = are_equal('True', get_setting_value('autoremovals', 'breasts'))

        if FurryTag.GENDER_FEMALE in self.furry_sim_info.tags and FurryTag.AGE_GROUP_TEEN_UP in self.furry_sim_info.tags:
            trait_manager = services.get_instance_manager(Types.TRAIT)
            can_lactate_trait = trait_manager.get(274985)
            cannot_lactate_trait = trait_manager.get(275052)

            can_lactate = self.furry_sim_info.base_sim_info.has_trait(can_lactate_trait)

            # If we are disabling lacation for scalies/featheries, and the sim is a scaly/etc., disable it
            if is_disabled and can_lactate and (FurryTag.FURRYTYPE_SCALY in self.furry_sim_info.tags or FurryTag.FURRYTYPE_FEATHERY in self.furry_sim_info.tags):
                self.furry_sim_info.base_sim_info.remove_trait(can_lactate_trait)
                self.furry_sim_info.base_sim_info.add_trait(cannot_lactate_trait)
                log_text("Disabled Lactation")
            # If the sim is not a scaly, but started flat-chested, and it is disabled, enable it
            elif (FurryTag.BODY_FLAT_CHEST in self.furry_sim_info.tags and not can_lactate) and (FurryTag.FURRYTYPE_SCALY not in self.furry_sim_info.tags and FurryTag.FURRYTYPE_FEATHERY not in self.furry_sim_info.tags):
                self.furry_sim_info.base_sim_info.remove_trait(cannot_lactate_trait)
                self.furry_sim_info.base_sim_info.add_trait(can_lactate_trait)
                log_text("Enabled Lactation")
            # Or, is the setting is off and the sim is flat chested and lactation is disabled, enable it
            elif not is_disabled and (FurryTag.BODY_FLAT_CHEST in self.furry_sim_info.tags and not can_lactate):
                self.furry_sim_info.base_sim_info.remove_trait(cannot_lactate_trait)
                self.furry_sim_info.base_sim_info.add_trait(can_lactate_trait)
                log_text("Enabled Lactation")

    def cycle_plant_sim(self):
        if FurryTag.OCCULT_PLANTSIM in self.furry_sim_info.tags:
            trait_manager = services.get_instance_manager(Types.TRAIT)
            plantsim_trait = trait_manager.get(162668)
            self.furry_sim_info.base_sim_info.remove_trait(plantsim_trait)
            self.furry_sim_info.base_sim_info.add_trait(plantsim_trait)
            log_text("Cycled plant sim")

    def mark_potential_furry(self):
        mark_potential_furry(self.furry_sim_info.base_sim_info)

    def mark_exempt(self):
        mark_exempt(self.furry_sim_info.base_sim_info)

    def is_exempt(self) -> bool:
        return is_exempt(self.furry_sim_info.base_sim_info)


def update_furry_traits(sim_info: SimInfo, tags: {int}):
    trait_manager = services.get_instance_manager(Types.TRAIT)
    furry_trait = trait_manager.get(16979007351164161671)
    scaly_trait = trait_manager.get(10841828803585111305)
    feathery_trait = trait_manager.get(11960148769534105407)
    exempt_trait = trait_manager.get(16710384910426247548)
    potential_trait = trait_manager.get(12283065628421974891)

    # Remove traits if they already exist
    if sim_info.has_trait(furry_trait):
        sim_info.remove_trait(furry_trait)
        log_text("Removed Furry Trait")
    elif sim_info.has_trait(scaly_trait):
        sim_info.remove_trait(scaly_trait)
        log_text("Removed Scaly Trait")
    elif sim_info.has_trait(feathery_trait):
        sim_info.remove_trait(feathery_trait)
        log_text("Removed Feathery Trait")

    # Add the traits
    if FurryTag.FURRYTYPE_FURRY in tags:
        sim_info.add_trait(furry_trait)
        log_text("Added Furry Trait")
    elif FurryTag.FURRYTYPE_SCALY in tags:
        sim_info.add_trait(scaly_trait)
        log_text("Added Scaly Trait")
    elif FurryTag.FURRYTYPE_FEATHERY in tags:
        sim_info.add_trait(feathery_trait)
        log_text("Added Feathery Trait")
    elif FurryTag.FURRYTYPE_HUMAN in tags and not sim_info.has_trait(potential_trait):
        sim_info.add_trait(exempt_trait)
        log_text("Added Exempt Trait")

    # Un-exempt if furrified
    if sim_info.has_trait(exempt_trait) and (FurryTag.FURRYTYPE_FURRY in tags or FurryTag.FURRYTYPE_SCALY in tags or FurryTag.FURRYTYPE_FEATHERY in tags):
        sim_info.remove_trait(exempt_trait)
        log_text("Removed Exempt Trait")
    # Un-potential if furrified
    if sim_info.has_trait(potential_trait) and (FurryTag.FURRYTYPE_FURRY in tags or FurryTag.FURRYTYPE_SCALY in tags or FurryTag.FURRYTYPE_FEATHERY in tags):
        sim_info.remove_trait(potential_trait)
        log_text("Removed Potential Trait")


def mark_potential_furry(sim_info: SimInfo):
    trait_manager = services.get_instance_manager(Types.TRAIT)
    potential_trait = trait_manager.get(12283065628421974891)
    if not sim_info.has_trait(potential_trait):
        sim_info.add_trait(potential_trait)
    log_text("Marked potential furry")


def mark_exempt(sim_info: SimInfo):
    trait_manager = services.get_instance_manager(Types.TRAIT)
    exempt_trait = trait_manager.get(16710384910426247548)
    if not sim_info.has_trait(exempt_trait):
        sim_info.add_trait(exempt_trait)
    log_text("Marked exempt from furrification")


def is_exempt(sim_info: SimInfo) -> bool:
    trait_manager = services.get_instance_manager(Types.TRAIT)
    exempt_trait = trait_manager.get(16710384910426247548)
    if sim_info.has_trait(exempt_trait):
        return True

    valid_targets = get_setting_value('settings', 'automatic_targets')
    sim_category = get_sim_category(sim_info)
    return (sim_category == FurrySimCategory.PLAYER) \
        or (are_equal(valid_targets, 'Randoms') and sim_category == FurrySimCategory.PREMADE) \
        or (are_equal(valid_targets, 'Premades') and sim_category == FurrySimCategory.RANDOM)


def has_furrifier_traits(sim_info: SimInfo) -> bool:
    trait_manager = services.get_instance_manager(Types.TRAIT)
    trait_ids = [16979007351164161671, 10841828803585111305, 11960148769534105407, 12283065628421974891, 16710384910426247548, 16653425920695034766, 9619142357741996824, 18365742668114966688]
    traits = [trait_manager.get(trait_id) for trait_id in trait_ids]

    for trait in traits:
        if sim_info.has_trait(trait):
            return True

    return False
