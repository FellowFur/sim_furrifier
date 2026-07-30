from furrifier_res_premades import premades_data
from furrifier_sim_info import FurrySimInfo
from furrifier_sim_data_manager import FurrySimDataManager
from furrifier_sim_species_manager import FurrySimSpeciesManager
from furrifier_sim_trait_manager import FurrySimTraitManager
from furrifier_sim_gene_manager import FurrySimGenesManager
from furrifier_part_applier import FurryPartApplier
from furrifier_part_picker import FurryPartPicker
from furrifier_part_alternatives import get_alternatives_label_lists
from furrifier_utils_notifier import show_notification
from furrifier_utils_logger import start_log, close_log, log_text, log_tags, change_indent, change_log_operation, is_log_open, is_log_for_sim, change_log_disguise, use_log
from furrifier_utils_enums import FurryTag
from furrifier_utils_weights import weighted_choice
from furrifier_utils_basics import get_sim_name
from furrifier_configs_settings_handler import get_preferences
from furrifier_configs_register_handler import get_register_presets, get_clearable_body_types

from sims.sim_info_types import Age, Gender
from sims.global_gender_preference_tuning import GlobalGenderPreferenceTuning
from sims4.resources import Types
from cas.cas import get_caspart_bodytype
import services


class FurrySimWrapper:
    data_manager = None

    def __init__(self, sim_info, is_auto=False):
        start_log(sim_info, f"Loaded sim {sim_info.first_name} {sim_info.last_name}")

        # Create basic info
        self.furry_sim_info = FurrySimInfo(sim_info, False, is_auto)

        # Initialize wrapper components
        self.species_manager = FurrySimSpeciesManager(self.furry_sim_info)
        self.trait_manager = FurrySimTraitManager(self.furry_sim_info)
        self.data_manager = FurrySimDataManager(self.furry_sim_info)

        self.part_picker = FurryPartPicker(self.furry_sim_info, self.data_manager)
        self.part_applier = FurryPartApplier(self.furry_sim_info, self.data_manager)

        self.gene_manager = FurrySimGenesManager(self.furry_sim_info, self.trait_manager, self.species_manager, self.data_manager, self.part_picker, self.part_applier)

    def __del__(self):
        log_text("\nSim wrapper is being deleted...")
        if is_log_open() and is_log_for_sim(self.furry_sim_info.base_sim_info):
            log_text("\nSim tags used:")
            change_indent(1)
            log_tags(self.furry_sim_info.tags)
            change_indent(-1)

            close_log("Successfully finished operations")
        else:
            log_text("Finished checking sim")

    """
    ===== INITIALIZATION FUNCTIONS =====================================================================================
    """
    def initialize_log(self):
        if is_log_open():
            log_text("\nWARNING: New log is being initialized, probably an error...")
            log_text("\nSim tags used:")
            change_indent(1)
            log_tags(self.furry_sim_info.tags)
            change_indent(-1)

            close_log("Successfully finished operations")
            start_log(self.furry_sim_info.base_sim_info, f"Loaded sim {get_sim_name(self.furry_sim_info.base_sim_info)}")

        use_log()

    def initialize_info(self, is_disguise=False, include_current_parts=False, include_current_species=False):
        # Fill Sim_info with initial tags and infos
        self.furry_sim_info.is_disguise = is_disguise
        if is_log_open():
            change_log_disguise(is_disguise)
        self.populate_tags_and_infos(include_current_parts, include_current_species)

    """
    ===== FURRIFICATION FUNCTIONS ======================================================================================
    """

    def furrify(self, species):
        change_log_operation("furrify")
        log_text(f"Furrifying to species {species}")

        # Check premade possibilities
        if species == 'default':
            # Check if identifiable premade, or if non-premade with preset
            preset_options = get_register_presets()
            log_text(f"Checking sim presets:")
            change_indent(1)

            preset_name = ""
            if self.furry_sim_info.premade_identification is not None and self.furry_sim_info.premade_identification in preset_options:
                preset_name = weighted_choice(preset_options[self.furry_sim_info.premade_identification], self.furry_sim_info.tags)
            elif self.furry_sim_info.name not in premades_data and self.furry_sim_info.name in preset_options:
                preset_name = weighted_choice(preset_options[self.furry_sim_info.name], self.furry_sim_info.tags)

            if preset_name:
                species = f"preset_{preset_name}"
                log_text(f"Selected preset {species}")
            else:
                log_text(f"Failed to pick valid preset!")
            change_indent(-1)

            if species == 'default':
                species = 'genetic'

        if not self.species_manager.has_valid_species() and not species.startswith("preset_"):
            log_text("Sim does not currently have any valid species options")
            self.trait_manager.mark_potential_furry()
            return
        else:
            log_text("Sim has valid species options")

        if species == 'random':
            species = self.species_manager.pick_random_species()

        if species == 'human':
            if self.data_manager.is_furry():
                self.furry_sim_info.tags.update(self.species_manager.get_tags_for_species(species))
                self.part_applier.unfurrify()
        elif species.startswith("preset_"):
            self.part_applier.apply_preset(species[7:])
        else:
            if species != 'genetic':
                # Select species and get tags for them
                self.furry_sim_info.tags.update(self.species_manager.get_tags_for_species(species))

                # Decide parts
                parts, cleared_categories = self.part_picker.choose_parts()
            else:
                parts, cleared_categories = self.gene_manager.choose_parts_from_genes()
                # If a furrification has to be aborted, return now
                if parts is None:
                    return

            # Decide Sculpts and Skintone
            sculpts = self.part_picker.choose_sculpts()
            skintone = self.part_picker.choose_skintone()

            # Set custom skin tone, sculpts, and parts
            self.part_applier.set_parts(parts, clear_old=True, force_clear=cleared_categories)
            self.part_applier.set_sculpts(sculpts, clear_old=True)
            self.part_applier.set_skin(skintone)
            self.part_applier.resend_appearances()

        # Update traits with changes
        self.trait_manager.update_furrifier_traits()

    def furrify_age_up(self, age_up_species, age_up_parts, old_tags):
        change_log_operation("age_up")
        log_text("Aging up furry sim")
        self.furry_sim_info.is_age_up = True
        self.furry_sim_info.tags.add(FurryTag.OPERATION_AGE_UP)

        # Decide parts, sculpts, and skintones
        self.furry_sim_info.tags.update(self.species_manager.get_tags_for_species(age_up_species))
        parts, cleared_categories = self.gene_manager.choose_age_up_parts(age_up_parts, age_up_species, old_tags)

        if parts:
            sculpts = self.part_picker.choose_sculpts()
            skintone = self.part_picker.choose_skintone()

            # Set custom skin tone, sculpts, and parts
            self.part_applier.set_parts(parts, clear_old=True, force_clear=cleared_categories)
            self.part_applier.set_sculpts(sculpts, clear_old=True)
            self.part_applier.set_skin(skintone)
            self.part_applier.resend_appearances()

            # Update traits with changes
            self.trait_manager.update_furrifier_traits()
        else:
            log_text("Sim required no age up changes!")

    def update_preferences(self):
        change_log_operation("update")
        log_text("Updating preferences")
        self.furry_sim_info.tags.add(FurryTag.OPERATION_UPDATE_PREFS)

        # If sim has issues, cannot refurrify
        if not self.furry_sim_info.is_recognized_furry:
            show_notification(f"Sim {get_sim_name(self.furry_sim_info.base_sim_info)} is not a recognized furry and cannot have preferences applied")
            return

        # Decide new parts
        current_part_ids = self.data_manager.get_furry_parts()
        invalid_parts, invalid_categories = self.data_manager.get_invalid_parts_and_categories(current_part_ids, preferred_only=True)
        alternatives_lists = get_alternatives_label_lists(invalid_parts, [], self.furry_sim_info.tags)
        alternatives_lists['label'] = 'Alternatives to Invalid Parts'
        missing_categories = self.data_manager.get_missing_body_types(current_part_ids, preferred_only=True)
        missing_categories = set(missing_categories) & {"39", "44", "2", "72"}
        needed_categories = {str(body_type) for body_type in set(invalid_categories) | missing_categories | get_clearable_body_types()}
        parts, cleared_categories = self.part_picker.choose_parts(part_categories=needed_categories, primary_preferred_parts_lists=alternatives_lists)

        # Check chosen parts to see if they fulfill all invalid categories, and delete any parts that are still invalid
        part_categories = []
        for part in parts:
            body_type = get_caspart_bodytype(part)
            part_categories.append(body_type)
        invalid_categories = set(invalid_categories) - set(part_categories)
        invalid_categories = {int(body_type) for body_type in invalid_categories}

        # Set new parts
        self.part_applier.set_parts(parts, clear_old=False, force_clear=(invalid_categories | cleared_categories))
        self.part_applier.resend_appearances()

        # Update traits with changes
        self.trait_manager.update_furrifier_traits()

    def randomize_fur_patterns(self):
        change_log_operation("randomize")
        log_text("Randomizing fur...")
        self.furry_sim_info.tags.add(FurryTag.OPERATION_RANDOMIZE_FUR)

        if not self.furry_sim_info.is_recognized_furry:
            show_notification(f"Sim {get_sim_name(self.furry_sim_info.base_sim_info)} is not a recognized furry yet and cannot have fur pattern randomized. Furrify the sim before using this.")
            return

        # Randomize the parts
        random_parts, cleared_categories = self.part_picker.randomize_parts()
        self.part_applier.set_parts(random_parts, clear_old=True, use_special_parts=False, force_clear=cleared_categories)
        self.part_applier.resend_appearances()

        # Cycle plant sims to make changes appear
        self.trait_manager.cycle_plant_sim()

    def reset_sculpts(self):
        change_log_operation("reset")
        log_text("Resetting Sculpts...")

        self.furry_sim_info.tags.add(FurryTag.OPERATION_RESET_SCULPTS)

        # If sim has issues, cannot reset
        if not self.furry_sim_info.is_recognized_furry and not self.furry_sim_info.is_auto:
            show_notification(f"Sim {get_sim_name(self.furry_sim_info.base_sim_info)} is not a recognized furry and cannot have sculpts reset")
            return

        # First, check if there are any missing sculpts that the sim should have but doesn't
        sim_sculpts = self.data_manager.get_current_sculpts()
        missing_categories = self.data_manager.get_missing_sculpt_categories(sim_sculpts)

        sculpts = self.part_picker.choose_sculpts(sculpt_categories=missing_categories)
        self.part_applier.set_sculpts(sculpts, clear_old=False)

    """
    ===== TAG FUNCTIONS ================================================================================================
    """

    def populate_tags_and_infos(self, include_current_parts=False, include_current_species=False):
        # Add tags from preferences
        self.furry_sim_info.tags.update(get_preferences())

        # Add tags based on sim's info
        self.furry_sim_info.tags.update(self.get_intrinsic_tags())

        # Add occult tags
        self.furry_sim_info.tags.update(self.furry_sim_info.form_infos.occult_tags)

        # If including parts (including species), add tags
        if include_current_parts:
            part_tags = self.data_manager.get_sim_existing_tags()
            if part_tags:
                self.furry_sim_info.tags.update(part_tags)
            else:
                # Part tags are needed to properly recognize a furry sim
                self.furry_sim_info.is_recognized_furry = False

        # If only including species, add tags
        elif include_current_species:
            species_tags = self.data_manager.get_sim_species_tags()

            if species_tags:
                self.furry_sim_info.tags.update(species_tags)
            else:
                # Species tags are needed to properly recognize a furry sim
                self.furry_sim_info.is_recognized_furry = False

        # Add furrifiable tag if there are species options
        if self.species_manager.has_valid_species():
            self.furry_sim_info.tags.add(FurryTag.MISC_FURRIFIABLE)

    def get_intrinsic_tags(self) -> {int}:
        intrinsic_tags = set()

        # Add age to tags
        intrinsic_tags.update(self.get_age_tags())

        # Add sim's gender, frame and style info to tags
        intrinsic_tags.update(self.get_gender_tags())

        # Add hair tags
        intrinsic_tags.update(self.get_hair_tags())

        # Add flat chest tag if sim currently has flat chest
        if FurryTag.GENDER_FEMALE in intrinsic_tags and FurryTag.AGE_GROUP_TEEN_UP in intrinsic_tags and 17872053180827599982 in self.data_manager.get_furry_parts():
            intrinsic_tags.add(FurryTag.BODY_FLAT_CHEST)

        # Add any other tags
        intrinsic_tags.update(self.get_other_tags())

        return intrinsic_tags

    def get_age_tags(self) -> {int}:
        age_translator = {
            Age.BABY: FurryTag.AGE_BABY,
            Age.INFANT: FurryTag.AGE_INFANT,
            Age.TODDLER: FurryTag.AGE_TODDLER,
            Age.CHILD: FurryTag.AGE_CHILD,
            Age.TEEN: FurryTag.AGE_TEEN,
            Age.YOUNGADULT: FurryTag.AGE_YOUNG_ADULT,
            Age.ADULT: FurryTag.AGE_ADULT,
            Age.ELDER: FurryTag.AGE_ELDER
        }

        if self.furry_sim_info.base_sim_info.age >= Age.TEEN:
            return {age_translator[self.furry_sim_info.base_sim_info.age], FurryTag.AGE_GROUP_TEEN_UP}
        else:
            return {age_translator[self.furry_sim_info.base_sim_info.age]}

    def get_gender_tags(self) -> {int}:
        # With help from Scumbumbo's 'Change Sim Name or Gender' mod
        trait_manager = services.get_instance_manager(Types.TRAIT)
        masculine_frame = trait_manager.get(136877)

        # Check if sim's gender is male or female
        if self.furry_sim_info.base_sim_info.gender == Gender.MALE:
            gender = FurryTag.GENDER_MALE
        else:
            gender = FurryTag.GENDER_FEMALE

        # Check if Sim's Frame is masculine or feminine
        if self.furry_sim_info.base_sim_info.has_trait(masculine_frame):
            frame = FurryTag.FRAME_MASCULINE
        else:
            frame = FurryTag.FRAME_FEMININE

        # Check if Sim's Style Preference is masculine or feminine
        if self.furry_sim_info.base_sim_info.has_trait(GlobalGenderPreferenceTuning.MALE_CLOTHING_PREFERENCE_TRAIT):
            style = FurryTag.STYLE_MASCULINE
        else:
            style = FurryTag.STYLE_FEMININE

        return {gender, frame, style}

    def get_hair_tags(self) -> {int}:
        hair_color_index = self.data_manager.get_hair_color_index()
        hair_color_tags = [FurryTag.HAIR_NEUTRAL_BLACK, FurryTag.HAIR_BLACK, FurryTag.HAIR_DARK_BROWN, FurryTag.HAIR_WARM_BROWN, FurryTag.HAIR_BROWN, FurryTag.HAIR_LIGHT_BROWN, FurryTag.HAIR_RED, FurryTag.HAIR_AUBURN, FurryTag.HAIR_ORANGE, FurryTag.HAIR_NEUTRAL_BLONDE, FurryTag.HAIR_LIGHT_BLONDE, FurryTag.HAIR_BLONDE, FurryTag.HAIR_DIRTY_BLONDE, FurryTag.HAIR_PLATINUM, FurryTag.HAIR_WHITE, FurryTag.HAIR_WHITE_BLONDE, FurryTag.HAIR_GRAY, FurryTag.HAIR_PURPLE_PASTEL, FurryTag.HAIR_HOT_PINK, FurryTag.HAIR_DARK_BLUE, FurryTag.HAIR_TURQUOISE, FurryTag.HAIR_GREEN, FurryTag.HAIR_BLACK_SALT_AND_PEPPER, FurryTag.HAIR_BROWN_SALT_AND_PEPPER]

        if self.data_manager.is_bald():
            return {FurryTag.HAIR_BALD, hair_color_tags[hair_color_index]}
        else:
            return {hair_color_tags[hair_color_index]}

    def get_other_tags(self) -> {int}:
        trait_manager = services.get_instance_manager(Types.TRAIT)
        tags = set()

        # Firefighter easter egg
        if self.furry_sim_info.base_sim_info.has_trait(trait_manager.get(237784)):
            tags.add(FurryTag.CAREER_FIREFIGHTER)

        # Mailman easter egg
        if self.furry_sim_info.base_sim_info.has_trait(trait_manager.get(16853)):
            tags.add(FurryTag.CAREER_MAILMAN)

        return tags
