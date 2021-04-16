import pytest
from shapely.geometry import Polygon

import pcapi.core.bookings.factories as bookings_factories
from pcapi.core.bookings.models import Booking
import pcapi.core.offerers.factories as offerers_factories
from pcapi.core.offerers.models import Offerer
from pcapi.core.offerers.models import Venue
import pcapi.core.offers.factories as offers_factories
from pcapi.core.offers.models import Mediation
from pcapi.core.offers.models import Offer
from pcapi.core.offers.models import Stock
import pcapi.core.users.factories as users_factories
from pcapi.core.users.models import Favorite
from pcapi.core.users.models import User
from pcapi.model_creators.generic_creators import create_iris
from pcapi.model_creators.generic_creators import create_iris_venue
from pcapi.models import AllocineVenueProvider
from pcapi.models import AllocineVenueProviderPriceRule
from pcapi.models import ApiKey
from pcapi.models import BankInformation
from pcapi.models import Criterion
from pcapi.models import IrisFrance
from pcapi.models import IrisVenues
from pcapi.models import OfferCriterion
from pcapi.models import Product
from pcapi.models import Provider
from pcapi.models import UserOfferer
from pcapi.models import VenueProvider
from pcapi.repository import repository
from pcapi.scripts.offerer.delete_cascade_offerer_by_id import delete_cascade_offerer_by_id


@pytest.mark.usefixtures("db_session")
def test_delete_cascade_offerer_should_abort_when_offerer_has_any_bookings():
    # Given
    offerer_to_delete = offers_factories.OffererFactory()
    offers_factories.OfferFactory(venue__managingOfferer=offerer_to_delete)
    bookings_factories.BookingFactory(stock__offer__venue__managingOfferer=offerer_to_delete)

    # When
    with pytest.raises(AttributeError) as exception:
        delete_cascade_offerer_by_id(offerer_to_delete.id)

    # Then
    assert "Structure juridique non supprimable car elle contient des réservations" in str(exception)
    assert Offerer.query.count() == 1
    assert Venue.query.count() == 2
    assert Offer.query.count() == 2
    assert Stock.query.count() == 1
    assert Booking.query.count() == 1


@pytest.mark.usefixtures("db_session")
def test_delete_cascade_offerer_should_remove_managed_venues_offers_and_stocks():
    # Given
    offerer_to_delete = offers_factories.OffererFactory()
    offers_factories.OfferFactory(venue__managingOfferer=offerer_to_delete)
    offers_factories.StockFactory(offer__venue__managingOfferer=offerer_to_delete)
    offers_factories.StockFactory()

    # When
    delete_cascade_offerer_by_id(offerer_to_delete.id)

    # Then
    assert Offerer.query.count() == 1
    assert Venue.query.count() == 1
    assert Offer.query.count() == 1
    assert Stock.query.count() == 1


@pytest.mark.usefixtures("db_session")
def test_delete_cascade_offerer_should_remove_all_user_attachments_to_deleted_offerer():
    # Given
    user = users_factories.UserFactory()
    offerer_to_delete = offers_factories.OffererFactory()
    offers_factories.UserOffererFactory(user=user, offerer=offerer_to_delete)
    offers_factories.UserOffererFactory(user=user)

    # When
    delete_cascade_offerer_by_id(offerer_to_delete.id)

    # Then
    assert Offerer.query.count() == 1
    assert UserOfferer.query.count() == 1
    assert User.query.count() == 1


@pytest.mark.usefixtures("db_session")
def test_delete_cascade_offerer_should_remove_api_key_of_offerer():
    # Given
    offerer_to_delete = offers_factories.OffererFactory()
    offers_factories.ApiKeyFactory(offerer=offerer_to_delete)
    offers_factories.ApiKeyFactory()

    # When
    delete_cascade_offerer_by_id(offerer_to_delete.id)

    # Then
    assert Offerer.query.count() == 1
    assert ApiKey.query.count() == 1


@pytest.mark.usefixtures("db_session")
def test_delete_cascade_offerer_should_remove_products_owned_by_offerer():
    # Given
    offerer_to_delete = offers_factories.OffererFactory()
    offers_factories.ProductFactory(owningOfferer=offerer_to_delete)
    offers_factories.ProductFactory()

    # When
    delete_cascade_offerer_by_id(offerer_to_delete.id)

    # Then
    assert Offerer.query.count() == 0
    assert Product.query.count() == 1


@pytest.mark.usefixtures("db_session")
def test_delete_cascade_offerer_should_remove_bank_informations_of_offerer():
    # Given
    offerer_to_delete = offers_factories.OffererFactory()
    offers_factories.BankInformationFactory(offerer=offerer_to_delete)
    offers_factories.BankInformationFactory()

    # When
    delete_cascade_offerer_by_id(offerer_to_delete.id)

    # Then
    assert Offerer.query.count() == 0
    assert BankInformation.query.count() == 1


@pytest.mark.usefixtures("db_session")
def test_delete_cascade_offerer_should_remove_bank_informations_of_managed_venue():
    # Given
    venue = offers_factories.VenueFactory()
    offerer_to_delete = venue.managingOfferer
    offers_factories.BankInformationFactory(venue=venue)
    offers_factories.BankInformationFactory()

    # When
    delete_cascade_offerer_by_id(offerer_to_delete.id)

    # Then
    assert Offerer.query.count() == 0
    assert Venue.query.count() == 0
    assert BankInformation.query.count() == 1


@pytest.mark.usefixtures("db_session")
def test_delete_cascade_offerer_should_remove_iris_of_managed_venue():
    # Given
    venue = offers_factories.VenueFactory()
    other_venue = offers_factories.VenueFactory()
    offerer_to_delete = venue.managingOfferer

    polygon = Polygon([(0.1, 0.1), (0.1, 0.2), (0.2, 0.2), (0.2, 0.1)])
    iris = create_iris(polygon)
    iris_venue = create_iris_venue(iris, venue)
    other_iris_venue = create_iris_venue(iris, other_venue)
    repository.save(iris_venue, other_iris_venue)

    # When
    delete_cascade_offerer_by_id(offerer_to_delete.id)

    # Then
    assert Offerer.query.count() == 1
    assert Venue.query.count() == 1
    assert IrisVenues.query.count() == 1
    assert IrisFrance.query.count() == 1


@pytest.mark.usefixtures("db_session")
def test_delete_cascade_offerer_should_remove_mediations_of_managed_offers():
    # Given
    offerer_to_delete = offers_factories.OffererFactory()
    offers_factories.MediationFactory(offer__venue__managingOfferer=offerer_to_delete)
    offers_factories.MediationFactory()

    # When
    delete_cascade_offerer_by_id(offerer_to_delete.id)

    # Then
    assert Offerer.query.count() == 1
    assert Venue.query.count() == 1
    assert Offer.query.count() == 1
    assert Mediation.query.count() == 1


@pytest.mark.usefixtures("db_session")
def test_delete_cascade_offerer_should_remove_favorites_of_managed_offers():
    # Given
    offerer_to_delete = offers_factories.OffererFactory()
    users_factories.FavoriteFactory(offer__venue__managingOfferer=offerer_to_delete)
    users_factories.FavoriteFactory()

    # When
    delete_cascade_offerer_by_id(offerer_to_delete.id)

    # Then
    assert Offerer.query.count() == 1
    assert Venue.query.count() == 1
    assert Offer.query.count() == 1
    assert Favorite.query.count() == 1


@pytest.mark.usefixtures("db_session")
def test_delete_cascade_offerer_should_remove_criterion_attachment_of_managed_offers():
    # Given
    offerer_to_delete = offers_factories.OffererFactory()
    offers_factories.OfferCriterionFactory(offer__venue__managingOfferer=offerer_to_delete)
    offers_factories.OfferCriterionFactory()

    # When
    delete_cascade_offerer_by_id(offerer_to_delete.id)

    # Then
    assert Offerer.query.count() == 1
    assert Venue.query.count() == 1
    assert Offer.query.count() == 1
    assert OfferCriterion.query.count() == 1
    assert Criterion.query.count() == 2


@pytest.mark.usefixtures("db_session")
def test_delete_cascade_offerer_should_remove_venue_synchronization_to_provider():
    # Given
    offerer_to_delete = offers_factories.OffererFactory()
    offerers_factories.VenueProviderFactory(venue__managingOfferer=offerer_to_delete)
    offerers_factories.VenueProviderFactory()

    # When
    delete_cascade_offerer_by_id(offerer_to_delete.id)

    # Then
    assert Offerer.query.count() == 1
    assert Venue.query.count() == 1
    assert VenueProvider.query.count() == 1
    assert Provider.query.count() > 0


@pytest.mark.usefixtures("db_session")
def test_delete_cascade_offerer_should_remove_venue_synchronization_to_allocine_provider():
    # Given
    offerer_to_delete = offers_factories.OffererFactory()
    offerers_factories.AllocineVenueProviderPriceRuleFactory(
        allocineVenueProvider__venue__managingOfferer=offerer_to_delete
    )
    offerers_factories.AllocineVenueProviderPriceRuleFactory()
    AllocineVenueProvider.query.all()

    # When
    delete_cascade_offerer_by_id(offerer_to_delete.id)

    # Then
    assert Offerer.query.count() == 1
    assert Venue.query.count() == 1
    assert VenueProvider.query.count() == 1
    assert AllocineVenueProvider.query.count() == 1
    assert AllocineVenueProviderPriceRule.query.count() == 1
    assert Provider.query.count() > 0
