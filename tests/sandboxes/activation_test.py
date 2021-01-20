import pytest

from pcapi.core.bookings.models import Booking
from pcapi.core.offers.models import Mediation
from pcapi.core.offers.models import Offer
from pcapi.core.offers.models import Stock
from pcapi.core.users.models import User
from pcapi.models.offerer import Offerer
from pcapi.models.product import Product
from pcapi.sandboxes.scripts.save_sandbox import save_sandbox


@pytest.mark.usefixtures("db_session")
def test_save_activation_sandbox(app):
    # given
    save_sandbox("activation")

    # then
    assert Booking.query.count() == 0
    assert Mediation.query.count() == 0
    assert Offer.query.count() == 1
    assert Offerer.query.count() == 1
    assert Product.query.count() == 1
    assert Stock.query.count() == 1
    assert User.query.count() == 0

    assert Stock.query.one().quantity == 10000
