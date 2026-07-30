import enum
from furrifier_utils_basics import get_sim_name
from furrifier_utils_logger import log_text
from furrifier_utils_enums import FurryTag
from furrifier_res_premades import premades_data, premade_ids, premade_first_names

from sims.occult.occult_enums import OccultType
from sims.sim_info import SimInfo
from sims.sim_spawner_enums import SimInfoCreationSource


class FurrySimCategory(enum.Int):
    PLAYER = 0
    PREMADE = 1
    RANDOM = 2


class FurrySimInfo:

    def __init__(self, sim_info: SimInfo, is_disguise: bool, is_auto=False):
        self.base_sim_info = sim_info
        self.primary_sim_info = get_primary_info(sim_info, is_disguise)
        self.form_infos = FormInfoCollection(sim_info, is_disguise)
        self.tags = {FurryTag.MISC_VALID}

        self.is_disguise = is_disguise
        self.is_auto = is_auto
        self.is_age_up = False

        self.is_recognized_furry = True

        self.name = get_sim_name(sim_info)
        self.sim_category = get_sim_category(sim_info)
        self.premade_identification = get_premade_identification(sim_info)


def get_primary_info(sim_info: SimInfo, is_disguise: bool):
    # Get the sim_info of the target form for getting current appearances
    if not is_disguise and sim_info.occult_tracker.get_occult_sim_info(OccultType.ALIEN) is not None:
        log_text("Targeting alien true form")
        return sim_info.occult_tracker.get_occult_sim_info(OccultType.ALIEN)
    elif is_disguise and sim_info.occult_tracker.get_occult_sim_info(OccultType.HUMAN) is not None:
        log_text("Targeting alien disguise form")
        return sim_info.occult_tracker.get_occult_sim_info(OccultType.HUMAN)
    else:
        log_text("Targeting non-alien")
        return sim_info


def get_true_form(sim_info: SimInfo):
    if sim_info.occult_tracker.has_occult_type(OccultType.ALIEN) and sim_info.occult_tracker.get_occult_sim_info(OccultType.ALIEN) is not None:
        return sim_info.occult_tracker.get_occult_sim_info(OccultType.ALIEN)
    elif sim_info.occult_tracker.get_occult_sim_info(OccultType.HUMAN) is not None:
        return sim_info.occult_tracker.get_occult_sim_info(OccultType.HUMAN)
    else:
        return sim_info


def get_disguise(sim_info: SimInfo):
    return sim_info.occult_tracker.get_occult_sim_info(OccultType.HUMAN)


def get_premade_identification(sim_info: SimInfo):
    # Returns the name associated with the premade sim, if exists
    sim_name = get_sim_name(sim_info)

    # First do id check
    if sim_info.sim_template_id != 0 and sim_info.sim_template_id in premade_ids:
        premade_index = premade_ids.index(sim_info.sim_template_id)
        premade_name = list(premades_data.keys())[premade_index]
        log_text(f"Identified premade sim {premade_name} by template id {sim_info.sim_template_id}")
        return premade_name

    # Use creation source for backup name checks
    try:
        creation_source = int(sim_info.creation_source)
    except TypeError:
        creation_source = 0

    # Next do backup name check
    if sim_name in premades_data and premades_data[sim_name]['creation_source'] == creation_source:
        log_text(f"Identified premade sim {sim_name} by name")
        return sim_name
    # One last backup check for married names
    if sim_name.split(maxsplit=1) in premade_first_names:
        premade_index = premade_first_names.index(sim_name.split(maxsplit=1))
        premade_name = list(premades_data.keys())[premade_index]
        if premades_data[premade_name]['creation_source'] == creation_source:
            log_text(f"Identified premade sim {premade_name} as {sim_name} by first name")
            return premade_name

    return None


def get_sim_category(sim_info: SimInfo) -> int:
    if sim_info.is_played_sim:
        return FurrySimCategory.PLAYER
    elif get_premade_identification(sim_info) is not None:
        return FurrySimCategory.PREMADE
    elif sim_info.creation_source in (SimInfoCreationSource.CAS_INITIAL, SimInfoCreationSource.CAS_REENTRY, SimInfoCreationSource.CLONED, SimInfoCreationSource.GALLERY):
        return FurrySimCategory.PLAYER
    elif sim_info.creation_source in (SimInfoCreationSource.PRE_MADE, SimInfoCreationSource.HOUSEHOLD_TEMPLATE):
        return FurrySimCategory.PREMADE
    else:
        return FurrySimCategory.RANDOM


class FormInfoCollection:
    def __init__(self, sim_info: SimInfo, is_disguise=False):
        self.target_form = None
        self.occult_tags = set()
        self.info_map = {
            OccultType.HUMAN: set(),
            OccultType.ALIEN: set(),
            OccultType.MERMAID: set(),
            OccultType.VAMPIRE: set(),
            OccultType.WEREWOLF: set(),
            OccultType.FAIRY: set()
        }

        self.add_info(sim_info.occult_tracker.get_occult_sim_info(OccultType.HUMAN), OccultType.HUMAN)

        # Add the original sim_info the appropriate category
        base_occult_type = sim_info.occult_tracker.get_current_occult_types()
        self.add_info(sim_info, base_occult_type)

        # Determine occult tags and get infos
        if sim_info.occult_tracker.has_occult_type(OccultType.WITCH):
            self.occult_tags.add(FurryTag.OCCULT_SPELLCASTER)
            log_text("Sim identified as Spellcaster")

        if sim_info.occult_tracker.has_occult_type(OccultType.WEREWOLF):
            self.add_info(sim_info.occult_tracker.get_occult_sim_info(OccultType.WEREWOLF), OccultType.WEREWOLF)
            self.occult_tags.add(FurryTag.OCCULT_WEREWOLF)
            log_text("Sim identified as Werewolf")

        if sim_info.occult_tracker.has_occult_type(OccultType.VAMPIRE):
            self.add_info(sim_info.occult_tracker.get_occult_sim_info(OccultType.VAMPIRE), OccultType.VAMPIRE)
            self.occult_tags.add(FurryTag.OCCULT_VAMPIRE)
            log_text("Sim identified as Vampire")

        if sim_info.occult_tracker.has_occult_type(OccultType.MERMAID):
            self.add_info(sim_info.occult_tracker.get_occult_sim_info(OccultType.MERMAID), OccultType.MERMAID)
            self.occult_tags.add(FurryTag.OCCULT_MERMAID)
            log_text("Sim identified as Mermaid")

        if sim_info.occult_tracker.has_occult_type(OccultType.ALIEN):
            if base_occult_type is OccultType.ALIEN:
                log_text("Sim identified as Alien in Alien Form")
            else:
                log_text("Sim identified as Alien in Disguise")

            self.add_info(sim_info.occult_tracker.get_occult_sim_info(OccultType.ALIEN), OccultType.ALIEN)
            # Only add alien tag if not doing disguise
            if not is_disguise:
                self.occult_tags.add(FurryTag.OCCULT_ALIEN)

        if sim_info.occult_tracker.has_occult_type(OccultType.FAIRY):
            self.add_info(sim_info.occult_tracker.get_occult_sim_info(OccultType.FAIRY), OccultType.FAIRY)
            self.occult_tags.add(FurryTag.OCCULT_FAIRY)
            log_text("Sim identified as Fairy")

        if any(trait.guid64 == 102784 for trait in sim_info.trait_tracker.equipped_traits):
            self.occult_tags.update({FurryTag.OCCULT_HUMAN, FurryTag.OCCULT_ALIEN})
            log_text("Sim identified as Alien Hybrid")

        # Plant sims aren't technically occults, but track anyway for species randomization
        if any(trait.guid64 == 162668 for trait in sim_info.trait_tracker.equipped_traits):
            self.occult_tags.add(FurryTag.OCCULT_PLANTSIM)
            log_text("Sim identified as Plantsim")

        # If no special occults were detected, treat as humans
        if not self.occult_tags:
            self.occult_tags = {FurryTag.OCCULT_HUMAN}
            log_text("Sim identified as Human")

    def add_info(self, info, info_type: OccultType):
        if info is not None:
            self.info_map[info_type].add(info)

    def get_editable_infos(self, is_disguise=False):
        """
        Gets all the sim infos that should be modified

        Args:
            is_disguise (bool): Whether to return disguised infos

        Returns:
            list of SimInfo: The target infos
        """
        if self.target_form is None:
            if not self.info_map[OccultType.ALIEN] or is_disguise:
                return self.info_map[OccultType.HUMAN] | self.info_map[OccultType.MERMAID] | self.info_map[OccultType.VAMPIRE] | self.info_map[OccultType.FAIRY]
            else:
                return self.info_map[OccultType.ALIEN]
        else:
            return self.info_map[self.target_form]

    def set_target_form(self, form_type: OccultType):
        self.target_form = form_type

    def get_all_infos(self):
        """
        Gets all the sim infos

        Returns:
            list of SimInfo: All the sim's infos
        """
        return self.info_map[OccultType.HUMAN] | self.info_map[OccultType.ALIEN] | self.info_map[OccultType.MERMAID] | self.info_map[OccultType.VAMPIRE] | self.info_map[OccultType.WEREWOLF] | self.info_map[OccultType.FAIRY]

    def is_mermaid_info(self, sim_info):
        """
        Checks if a sim info is a mermaid form

        Args:
            sim_info (SimInfo): The info to check

        Returns:
            bool: Whether the info is a mermaid form
        """
        return sim_info in self.info_map[OccultType.MERMAID]
