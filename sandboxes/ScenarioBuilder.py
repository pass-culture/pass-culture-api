from tests.test_utils import create_user, create_offerer, create_user_offerer, create_venue, \
    create_offer_with_thing_product


class ScenarioBuilder:
    def __init__(self):
        self.user = None
        self.current_object = None

    def with_user_pro(self, first_name, last_name):
        pro_email = "pctest.pro.titelive@btmx.fr"

        self.user = create_user(
            first_name=first_name,
            last_name=last_name,
            email=pro_email,
            can_book_free_offers=False
        )

        self._set_current_object(self.user)

        return self

    def with_offerer(self, offerer_name, siren):
        self.offerer = create_offerer(name=offerer_name, siren=siren)
        self._set_current_object(self.offerer)
        if self.user:
            user_offerer = create_user_offerer(self.user, self.offerer)
        return self

    def with_venue(self, venue_name):
        self.venue = create_venue(self.offerer, name=venue_name)
        self._set_current_object(self.venue)
        return self


    def with_offer(self):
        offer = create_offer_with_thing_product(
            self.venue
        )

        self._set_current_object(offer)
        return self

    def detail(self, field_to_update, value):
        setattr(self.current_object, field_to_update, value)
        return self

    def build(self):
        return self.user or self.offerer

    def _set_current_object(self, obj):
        self.current_object = obj
        return self
