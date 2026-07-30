from event_testing.test_base import BaseTest
from event_testing.results import TestResult
from event_testing.test_events import TestEvent
from caches import cached_test
from interactions import ParticipantTypeSingle
from sims4.tuning.tunable import HasTunableSingletonFactory, AutoFactoryInit, Tunable, TunableEnumEntry
from furrifier_configs_settings_handler import get_setting_value
from furrifier_configs_settings_detector import get_set_status
from furrifier_sim_data_manager import can_be_furrified
from furrifier_utils_logger import log_exception
from furrifier_utils_basics import are_equal
from furrifier_sim_wrapper import FurrySimWrapper
from event_testing.tests import _TunableTestSetBase, TunableTestVariant
from event_testing.tests import TestSetInstance


# credit to https://frankkmods.medium.com/custom-tuning-tests-sims-4-script-modding-3837e214fb68
class FurrifierSettingsTest(HasTunableSingletonFactory, AutoFactoryInit, BaseTest):
    """
    A test to check the value of a setting in the furrifier
    """

    FACTORY_TUNABLES = {
        'setting': Tunable(
            description="The setting to test.",
            tunable_type=str,
            default=False),
        'value': Tunable(
            description="The value to check if the setting is set to",
            tunable_type=str,
            default='true'),
        'invert': Tunable(
            description="If true, the result of the test will be inverted.",
            tunable_type=bool,
            default=False),
    }

    __slots__ = ('setting', 'value', 'invert')

    test_events = (TestEvent.InteractionComplete, )

    def get_expected_args(self):
        pass

    @cached_test
    def __call__(self, **kwargs):
        try:
            category, setting = tuple(self.setting.split('.'))
            current_value = get_setting_value(category, setting)

            matches = are_equal(current_value, self.value)

            if matches != self.invert:
                return TestResult.TRUE
            else:
                return TestResult(False, f"Test failed, expected setting: {self.value}, actual setting: {current_value}", tooltip=self.tooltip)
        except (Exception, ):
            log_exception()


class FurrifierSetTest(HasTunableSingletonFactory, AutoFactoryInit, BaseTest):
    """
    A test to check the status of a set in the furrifier
    """

    FACTORY_TUNABLES = {
        'set': Tunable(
            description="The set to test.",
            tunable_type=str,
            default=False),
        'status': Tunable(
            description="The installation status to check for",
            tunable_type=str,
            default='Installed'),
        'invert': Tunable(
            description="If true, the result of the test will be inverted.",
            tunable_type=bool,
            default=False),
    }

    __slots__ = ('set', 'status', 'invert')

    test_events = (TestEvent.InteractionComplete, )

    def get_expected_args(self):
        pass

    @cached_test
    def __call__(self, **kwargs):
        try:
            current_status = get_set_status(self.set)

            matches = (current_status.casefold() == self.status.casefold())

            if matches != self.invert:
                return TestResult.TRUE
            else:
                return TestResult(False, f"Test failed, expected status: {self.status}, actual setting: {current_status}", tooltip=self.tooltip)
        except (Exception, ):
            log_exception()


class FurrifierOptionTest(HasTunableSingletonFactory, AutoFactoryInit, BaseTest):
    """
    A test to check if a sim has any species options
    """

    FACTORY_TUNABLES = {
        'subject': TunableEnumEntry(
            description='The subject of the test.',
            tunable_type=ParticipantTypeSingle,
            default=ParticipantTypeSingle.Actor),
        'is_disguise': Tunable(
            description="If true, checks a sim's disguise instead",
            tunable_type=bool,
            default=False),
        'invert': Tunable(
            description="If true, the result of the test will be inverted.",
            tunable_type=bool,
            default=False),
    }

    __slots__ = ('subject', 'is_disguise', 'invert')

    test_events = (TestEvent.InteractionComplete, )

    def get_expected_args(self):
        return {'subjects': self.subject}

    @cached_test
    def __call__(self, subjects=None, **kwargs):
        try:
            subject = next(iter(subjects))
            if subject is not None and subject.is_sim and subject.get_sim_instance():
                sim_info = subject.get_sim_instance().sim_info
                can_furrify, reason = can_be_furrified(sim_info, is_disguise=self.is_disguise)
                if can_furrify:
                    furry_sim = FurrySimWrapper(sim_info, is_auto=True)
                    furry_sim.initialize_info(is_disguise=self.is_disguise)
                    furry_sim.species_manager.has_valid_species()
                    if furry_sim.species_manager.has_valid_species() != self.invert:
                        return TestResult.TRUE
                    else:
                        return TestResult(False, f"Test failed, sim has no valid species", tooltip=self.tooltip)
                else:
                    return TestResult(False, f"Test failed, sim cannot be furrified, {reason}", tooltip=self.tooltip)
            else:
                return TestResult(False, f"Test failed, sim is not valid", tooltip=self.tooltip)
        except (Exception, ):
            log_exception()
            return TestResult(False, f"Test failed, exception was thrown!", tooltip=self.tooltip)


class FurrifierTest(_TunableTestSetBase, is_fragment=True):
    """
    The tunable test set class that can parse your custom tests.
    """

    MY_TEST_VARIANTS = {
        'furrifier_setting': FurrifierSettingsTest,
        'furrifier_set': FurrifierSetTest,
        'furrifier_option': FurrifierOptionTest
    }

    def __init__(self, **kwargs):
        for test_name, test in self.MY_TEST_VARIANTS.items():
            TunableTestVariant.TEST_VARIANTS[test_name] = test.TunableFactory
        super().__init__(test_locked_args={}, **kwargs)


class FurrifierTestInstance(TestSetInstance):
    """
    A subclass of the TestSetInstance that replaces the standard test set with MyTestSet.
    """

    # IMPORTANT: Do NOT change the key 'test', or else you will have to override a million things in the
    # test set base. It's not worth it, just leave it as 'test'.
    INSTANCE_TUNABLES = {'test': FurrifierTest()}

