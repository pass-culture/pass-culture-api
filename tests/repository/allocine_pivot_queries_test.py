import pytest

from pcapi.model_creators.generic_creators import create_allocine_pivot
from pcapi.model_creators.generic_creators import create_offerer
from pcapi.model_creators.generic_creators import create_venue
from pcapi.repository import repository
from pcapi.repository.allocine_pivot_queries import get_allocine_theaterId_for_venue
from pcapi.repository.allocine_pivot_queries import has_allocine_pivot_for_venue


class HasAllocinePivotForVenueTest:
    @pytest.mark.usefixtures("db_session")
    def test_should_return_false_when_venue_has_no_siret(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, siret=None, comment="En attente de siret")
        allocine_pivot = create_allocine_pivot(siret="12345678912345")
        repository.save(venue, allocine_pivot)

        # When
        has_allocine_pivot = has_allocine_pivot_for_venue(venue)

        # Then
        assert not has_allocine_pivot


class GetAllocineTheaterIdForVenueTest:
    @pytest.mark.usefixtures("db_session")
    def test_should_not_return_value_when_not_matching_in_allocine_pivot(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, siret=None, comment="En attente de siret")
        allocine_pivot = create_allocine_pivot(siret="12345678912345")
        repository.save(venue, allocine_pivot)

        # When
        allocine_theater_id = get_allocine_theaterId_for_venue(venue)

        # Then
        assert allocine_theater_id is None

    @pytest.mark.usefixtures("db_session")
    def test_should_return_theaterId_when_siret_is_present_in_allocine_pivot(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer, siret="12345678912345", comment="En attente de siret")
        allocine_pivot = create_allocine_pivot(siret="12345678912345", theater_id="XXXXXXXXXXXXXXXXXX==")
        repository.save(venue, allocine_pivot)

        # When
        allocine_theater_id = get_allocine_theaterId_for_venue(venue)

        # Then
        assert allocine_theater_id == "XXXXXXXXXXXXXXXXXX=="
