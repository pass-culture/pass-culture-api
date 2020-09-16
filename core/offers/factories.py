import factor
import factory.sqlalchemy

from . import models


class BookingFactory(factory.sqlalchemy.SQLAlchemyModelFactory):
    user = factory.SubFactory(UserFactory)
    quantity = 1
    stock = factory.SubFactory(StockFactory)
    isUsed = False

    class Meta:
        model = models.Booking

