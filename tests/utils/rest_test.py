import pytest
from sqlalchemy import func

from models import Offer, PcObject, Venue, ApiErrors
from tests.conftest import clean_database
from tests.test_utils import create_venue, create_offerer
from utils.human_ids import humanize
from utils.rest import check_order_by, load_or_raise_error


@pytest.mark.standalone
class TestLoadOrRaiseErrorTest:
    @clean_database
    def test_returns_object_if_found(self, app):
        # Given
        id = humanize(1)

        # When
        with pytest.raises(ApiErrors) as error:
            load_or_raise_error(Venue, id)

        assert error.value.errors['global'] == [
            'Aucun objet ne correspond à cet identifiant dans notre base de données']

    @clean_database
    def test_raises_api_error_if_no_object(self, app):
        # Given
        offerer = create_offerer()
        venue = create_venue(offerer)
        PcObject.save(venue)

        # When
        try:
            load_or_raise_error(Venue, humanize(venue.id))

        except:
            assert False


@pytest.mark.standalone
class TestCheckOrderByTest:
    def test_check_order_by_raises_no_exception_when_given_sqlalchemy_column(self, app):
        # When
        try:
            check_order_by(Offer.id)
        except ApiErrors:
            # Then
            assert pytest.fail("Should not fail with valid params")

    def test_check_order_by_raises_no_exception_when_given_sqlalchemy_column_list(self, app):
        # When
        try:
            check_order_by([Offer.id, Offer.venueId])
        except ApiErrors:
            # Then
            assert pytest.fail("Should not fail with valid params")

    def test_check_order_by_raises_no_exception_when_given_sqlalchemy_desc_expression(self, app):
        # When
        try:
            check_order_by(Offer.id.desc())
        except ApiErrors:
            # Then
            assert pytest.fail("Should not fail with valid params")

    def test_check_order_by_raises_no_exception_when_given_sqlalchemy_func_random_expression(self, app):
        # When
        try:
            check_order_by(func.random())
        except ApiErrors:
            # Then
            assert pytest.fail("Should not fail with valid params")

    def test_check_order_by_raises_no_exception_when_given_mixed_list(self, app):
        # When
        try:
            check_order_by([Offer.id, Offer.venueId.desc(), func.random(), 'id'])
        except ApiErrors:
            # Then
            assert pytest.fail("Should not fail with valid params")

    def test_check_order_by_raises_no_exception_when_given_colum_name_as_string(self, app):
        # When
        try:
            check_order_by('venueId')
        except ApiErrors:
            # Then
            assert pytest.fail("Should not fail with valid params")


    def test_check_order_by_raises_no_exception_when_given_colum_name_as_string_with_quotes(self, app):
        # When
        try:
            check_order_by('"venueId"')
        except ApiErrors:
            # Then
            assert pytest.fail("Should not fail with valid params")

    def test_check_order_by_raises_no_exception_when_given_colum_name_as_string_with_quotes_and_desc(self, app):
        # When
        try:
            check_order_by('"venueId" DESC')
        except ApiErrors:
            # Then
            assert pytest.fail("Should not fail with valid params")

    def test_check_order_by_raises_no_exception_when_given_colum_name_as_string_with_quotes_and_table_name(self, app):
        # When
        try:
            check_order_by('Offer."venueId" DESC')
        except ApiErrors:
            # Then
            assert pytest.fail("Should not fail with valid params")

    def test_check_order_by_raises_no_exception_when_given_colum_name_as_string_with_quotes_and_table_name_with_quotes(self, app):
        # When
        try:
            check_order_by('"Offer"."venueId" DESC')
        except ApiErrors:
            # Then
            assert pytest.fail("Should not fail with valid params")

    def test_check_order_by_raises_no_exception_when_given_comma_separated_list_in_string(self, app):
        # When
        try:
            check_order_by('"Offer"."venueId" DESC, id ASC')
        except ApiErrors:
            # Then
            assert pytest.fail("Should not fail with valid params")

    def test_check_order_by_raises_no_exception_when_given_coalesce_expression_in_string(self, app):
        # When
        try:
            check_order_by('COALESCE("Offer"."venueId" , id) ASC')
        except ApiErrors:
            # Then
            assert pytest.fail("Should not fail with valid params")

    def test_check_order_by_raises_an_exception_when_given_list_containing_invalid_part(self, app):
        # When
        with pytest.raises(ApiErrors) as e:
            check_order_by([Offer.id, func.random(), 'select * from toto'])

        # Then
        assert 'order_by' in e.value.errors

    def test_check_order_by_raises_an_exception_when_given_select_statement(self, app):
        # When
        with pytest.raises(ApiErrors) as e:
            check_order_by('select plop from offer')

        # Then
        assert 'order_by' in e.value.errors
