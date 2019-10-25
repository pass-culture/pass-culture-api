from models import PcObject
from repository.provider_queries import get_enabled_providers_for_pro
from tests.conftest import clean_database
from tests.test_utils import create_provider


class GetEnabledProvidersForProTest:
    @clean_database
    def test_get_enabled_providers_for_pro(self, app):
        # given
        provider1 = create_provider('OpenAgenda', is_active=False, is_enable_for_pro=False)

        provider2 = create_provider('TiteLive', is_active=True, is_enable_for_pro=True)
        PcObject.save(provider1, provider2)

        # when
        enabled_providers = get_enabled_providers_for_pro()

        # then
        assert enabled_providers == [provider2]
