import pytest

from models import ApiErrors, PcObject
from models.venue import TooManyVirtualVenuesException
from tests.conftest import clean_database
from tests.test_utils import create_offerer, create_venue, create_offer_with_thing_product, \
    create_offer_with_event_product, \
    create_bank_information


@clean_database
def test_offerer_cannot_have_address_and_isVirtual(app):
    # Given
    offerer = create_offerer('123456789', '1 rue Test', 'Test city', '93000', 'Test offerer')
    PcObject.save(offerer)

    venue = create_venue(offerer, name='Venue_name', booking_email='booking@email.com', is_virtual=True, siret=None)
    venue.address = '1 test address'

    # When
    with pytest.raises(ApiErrors):
        PcObject.save(venue)


@clean_database
def test_offerer_not_isVirtual_can_have_null_address(app):
    # Given
    offerer = create_offerer('123456789', '1 rue Test', 'Test city', '93000', 'Test offerer')
    PcObject.save(offerer)

    venue = create_venue(offerer, name='Venue_name', booking_email='booking@email.com', address=None, postal_code='75000', city='Paris', departement_code='75', is_virtual=False)

    # When
    try:
        PcObject.save(venue)
    except ApiErrors:
        # Then
        assert pytest.fail("Should not fail with null address and not virtual and postal code, city, departement code are given")


@clean_database
def test_offerer_not_isVirtual_cannot_have_null_postal_code_nor_city_nor_departement_code(app):
    # Given
    offerer = create_offerer('123456789', '1 rue Test', 'Test city', '93000', 'Test offerer')
    PcObject.save(offerer)

    venue = create_venue(offerer, name='Venue_name', booking_email='booking@email.com', address='3 rue de valois', postal_code=None, city=None, departement_code=None, is_virtual=False)

    # When
    with pytest.raises(ApiErrors):
        PcObject.save(venue)


@clean_database
def test_offerer_cannot_create_a_second_virtual_venue(app):
    # Given
    offerer = create_offerer('123456789', '1 rue Test', 'Test city', '93000', 'Test offerer')
    PcObject.save(offerer)

    venue = create_venue(offerer, name='Venue_name', booking_email='booking@email.com', address=None, postal_code=None,
                         city=None, departement_code=None, is_virtual=True, siret=None)
    PcObject.save(venue)

    new_venue = create_venue(offerer, name='Venue_name', booking_email='booking@email.com', address=None,
                             postal_code=None, city=None, departement_code=None, is_virtual=True, siret=None)

    # When
    with pytest.raises(TooManyVirtualVenuesException):
        PcObject.save(new_venue)


@clean_database
def test_offerer_cannot_update_a_second_venue_to_be_virtual(app):
    # Given
    siren = '132547698'
    offerer = create_offerer(siren, '1 rue Test', 'Test city', '93000', 'Test offerer')
    PcObject.save(offerer)

    venue = create_venue(offerer, address=None, postal_code=None, city=None, departement_code=None, is_virtual=True,
                         siret=None)
    PcObject.save(venue)

    new_venue = create_venue(offerer, is_virtual=False, siret=siren + '98765')
    PcObject.save(new_venue)

    # When
    new_venue.isVirtual = True
    new_venue.postalCode = None
    new_venue.address = None
    new_venue.city = None
    new_venue.departementCode = None
    new_venue.siret = None

    # Then
    with pytest.raises(TooManyVirtualVenuesException):
        PcObject.save(new_venue)


@clean_database
def test_venue_raises_exception_when_is_virtual_and_has_siret(app):
    # given
    offerer = create_offerer()
    venue = create_venue(offerer, is_virtual=True, siret='12345678912345')

    # when
    with pytest.raises(ApiErrors):
        PcObject.save(venue)


@clean_database
def test_venue_raises_exception_when_no_siret_and_no_comment(app):
    # given
    offerer = create_offerer()
    venue = create_venue(offerer, siret=None, comment=None)

    # when
    with pytest.raises(ApiErrors):
        PcObject.save(venue)


@clean_database
def test_venue_raises_exception_when_siret_and_comment_but_virtual(app):
    # given
    offerer = create_offerer()
    venue = create_venue(offerer, siret=None, comment="hello I've comment and siret but i'm virtual", is_virtual=True)

    # when
    with pytest.raises(ApiErrors):
        PcObject.save(venue)


@clean_database
def test_venue_should_not_raise_exception_when_siret_and_comment(app):
    # given
    offerer = create_offerer()
    venue = create_venue(offerer, siret="02345678912345", comment="hello I have some comment and siret !", is_virtual=False)

    # when
    try:
        PcObject.save(venue)

    except ApiErrors:
        # Then
        assert pytest.fail("Should not fail with comment and siret but not virtual")


@clean_database
def test_venue_should_not_raise_exception_when_no_siret_but_comment(app):
    # given
    offerer = create_offerer()
    venue = create_venue(offerer, siret=None, comment="hello I have some comment but no siret :(", is_virtual=False)

    # when
    try:
        PcObject.save(venue)

    except ApiErrors:
        # Then
        assert pytest.fail("Should not fail with comment but not virtual nor siret")


@clean_database
def test_nOffers(app):
    offerer = create_offerer()
    venue = create_venue(offerer)
    offer_1 = create_offer_with_thing_product(venue)
    offer_2 = create_offer_with_event_product(venue)
    offer_4 = create_offer_with_event_product(venue)
    offer_5 = create_offer_with_thing_product(venue)
    PcObject.save(offer_1, offer_2, offer_4, offer_5)

    # when
    n_offers = venue.nOffers

    # then
    assert n_offers == 4


class VenueBankInformationTest:
    @clean_database
    def test_bic_property_returns_bank_information_bic_when_venue_has_bank_information(self, app):
        # Given
        offerer = create_offerer(siren='123456789')
        venue = create_venue(offerer, siret='12345678912345')
        bank_information = create_bank_information(bic='BDFEFR2LCCB', id_at_providers='12345678912345', venue=venue)
        PcObject.save(bank_information)

        # When
        bic = venue.bic

        # Then
        assert bic == 'BDFEFR2LCCB'

    @clean_database
    def test_bic_property_returns_none_when_does_not_have_bank_information(self, app):
        # Given
        offerer = create_offerer(siren='123456789')
        venue = create_venue(offerer, siret='12345678912345')
        PcObject.save(venue)

        # When
        bic = venue.bic

        # Then
        assert bic is None

    @clean_database
    def test_iban_property_returns_bank_information_iban_when_venue_has_bank_information(self, app):
        # Given
        offerer = create_offerer(siren='123456789')
        venue = create_venue(offerer, siret='12345678912345')
        bank_information = create_bank_information(iban='FR7630007000111234567890144', id_at_providers='12345678912345',
                                                   venue=venue)
        PcObject.save(bank_information)

        # When
        iban = venue.iban

        # Then
        assert iban == 'FR7630007000111234567890144'

    @clean_database
    def test_iban_property_returns_none_when_venue_has_bank_information(self, app):
        # Given
        offerer = create_offerer(siren='123456789')
        venue = create_venue(offerer, siret='12345678912345')
        PcObject.save(venue)

        # When
        iban = venue.iban

        # Then
        assert iban is None
