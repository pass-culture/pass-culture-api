from unittest.mock import patch

import pytest

from pcapi.model_creators.generic_creators import create_iris
from pcapi.model_creators.generic_creators import create_iris_venue
from pcapi.model_creators.generic_creators import create_mediation
from pcapi.model_creators.generic_creators import create_offerer
from pcapi.model_creators.generic_creators import create_user
from pcapi.model_creators.generic_creators import create_venue
from pcapi.model_creators.specific_creators import create_offer_with_thing_product
from pcapi.model_creators.specific_creators import create_stock_from_offer
from pcapi.recommendations_engine.recommendations import create_recommendations_for_discovery_v3
from pcapi.repository import discovery_view_v3_queries
from pcapi.repository import repository
from pcapi.utils.human_ids import humanize

from tests.test_utils import POLYGON_TEST


class CreateRecommendationsForDiscoveryTest:
    @pytest.mark.usefixtures("db_session")
    def test_does_not_put_mediation_ids_of_inactive_mediations(self, app):
        # Given
        sent_offers_ids = []
        user = create_user()
        offerer = create_offerer()
        venue = create_venue(offerer)
        offer1 = create_offer_with_thing_product(venue)
        stock1 = create_stock_from_offer(offer1, price=0)
        mediation1 = create_mediation(offer1, is_active=False)
        offer2 = create_offer_with_thing_product(venue)
        stock2 = create_stock_from_offer(offer2, price=0)
        mediation2 = create_mediation(offer2, is_active=False)
        mediation3 = create_mediation(offer2, is_active=True)

        iris = create_iris(POLYGON_TEST)
        repository.save(user, stock1, mediation1, stock2, mediation2, mediation3)
        iris_venue = create_iris_venue(iris, venue)
        repository.save(iris_venue)

        discovery_view_v3_queries.refresh(concurrently=False)

        # When
        recommendations = create_recommendations_for_discovery_v3(
            user=user, user_iris_id=iris.id, sent_offers_ids=sent_offers_ids
        )

        # Then
        mediations = list(map(lambda x: x.mediationId, recommendations))
        assert len(recommendations) == 1
        assert mediation3.id in mediations
        assert humanize(mediation2.id) not in mediations
        assert humanize(mediation1.id) not in mediations

    @patch("pcapi.recommendations_engine.recommendations.get_offers_for_recommendation_v3")
    def test_requests_offers_with_same_criteria(self, mock_get_offers_for_recommendation_v3):
        # Given
        user = create_user()

        # When
        create_recommendations_for_discovery_v3(
            user, user_iris_id=1, user_is_geolocated=True, sent_offers_ids=[], limit=30
        )

        # Then
        mock_get_offers_for_recommendation_v3.assert_called_once_with(
            user=user, user_iris_id=1, user_is_geolocated=True, limit=30, sent_offers_ids=[]
        )
