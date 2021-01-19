import uuid

import factory

from pcapi.core.offers.factories import VenueFactory
from pcapi.core.testing import BaseFactory
from pcapi.models.provider import Provider
from pcapi.models.venue_provider import VenueProvider


class ProviderFactory(BaseFactory):
    class Meta:
        model = Provider
        sqlalchemy_get_or_create = ["localClass"]

    name = factory.Sequence("Provider {}".format)
    localClass = None
    apiKey = factory.LazyFunction(lambda: str(uuid.uuid4()).replace("-", ""))

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # See check_provider_has_localclass_or_apikey constraint.
        if kwargs.get("localClass"):
            kwargs["apiKey"] = None
        return super()._create(model_class, *args, **kwargs)


class VenueProviderFactory(BaseFactory):
    class Meta:
        model = VenueProvider

    venue = factory.SubFactory(VenueFactory)
    provider = factory.SubFactory(ProviderFactory)
