import datetime
import pathlib

import pytest
import requests

import pcapi.core.offerers.factories as offerers_factories
from pcapi.core.offers import exceptions
from pcapi.core.offers import factories
from pcapi.core.offers import validation
from pcapi.models.api_errors import ApiErrors

import tests


IMAGES_DIR = pathlib.Path(tests.__path__[0]) / "files"


@pytest.mark.usefixtures("db_session")
class CheckOfferIsEditableTest:
    def test_raises_error_when_offer_is_not_editable(self):
        offerer = offerers_factories.ProviderFactory()
        offer = factories.OfferFactory(lastProvider=offerer, idAtProviders="1")

        with pytest.raises(ApiErrors) as error:
            validation.check_offer_is_editable(offer)

        assert error.value.errors["global"] == ["Les offres importées ne sont pas modifiables"]

    def test_does_not_raise_error_when_offer_type_is_editable(self):
        offer = factories.OfferFactory(lastProviderId=None)

        validation.check_offer_is_editable(offer)  # should not raise


@pytest.mark.usefixtures("db_session")
class CheckRequiredDatesForStock:
    def test_thing_offer_must_not_have_beginning(self):
        offer = factories.ThingOfferFactory()

        with pytest.raises(ApiErrors) as error:
            validation.check_required_dates_for_stock(
                offer,
                beginning=datetime.datetime.now(),
                booking_limit_datetime=None,
            )

        assert error.value.errors["global"] == [
            "Impossible de mettre une date de début si l'offre ne porte pas sur un événement"
        ]

    def test_thing_offer_ok_with_booking_limit_datetime(self):
        offer = factories.ThingOfferFactory()

        validation.check_required_dates_for_stock(
            offer,
            beginning=None,
            booking_limit_datetime=datetime.datetime.now(),
        )

    def test_thing_offer_ok_without_booking_limit_datetime(self):
        offer = factories.ThingOfferFactory()

        validation.check_required_dates_for_stock(
            offer,
            beginning=None,
            booking_limit_datetime=None,
        )

    def test_event_offer_must_have_beginning(self):
        offer = factories.EventOfferFactory()

        with pytest.raises(ApiErrors) as error:
            validation.check_required_dates_for_stock(
                offer,
                beginning=None,
                booking_limit_datetime=datetime.datetime.now(),
            )
        assert error.value.errors["beginningDatetime"] == ["Ce paramètre est obligatoire"]

    def test_event_offer_must_have_booking_limit_datetime(self):
        offer = factories.EventOfferFactory()

        with pytest.raises(ApiErrors) as error:
            validation.check_required_dates_for_stock(
                offer,
                beginning=datetime.datetime.now(),
                booking_limit_datetime=None,
            )
        assert error.value.errors["bookingLimitDatetime"] == ["Ce paramètre est obligatoire"]

    def test_event_offer_ok_with_beginning_and_booking_limit_datetime(self):
        offer = factories.EventOfferFactory()

        validation.check_required_dates_for_stock(
            offer,
            beginning=datetime.datetime.now(),
            booking_limit_datetime=datetime.datetime.now(),
        )


@pytest.mark.usefixtures("db_session")
class CheckStocksAreEditableForOfferTest:
    def should_fail_when_offer_is_from_provider(self, app):
        provider = offerers_factories.ProviderFactory()
        offer = factories.OfferFactory(lastProvider=provider, idAtProviders="1")

        with pytest.raises(ApiErrors) as error:
            validation.check_stocks_are_editable_for_offer(offer)

        assert error.value.errors["global"] == ["Les offres importées ne sont pas modifiables"]

    def should_not_raise_an_error_when_offer_is_not_from_provider(self):
        offer = factories.OfferFactory(lastProvider=None)
        validation.check_stocks_are_editable_for_offer(offer)  # should not raise


@pytest.mark.usefixtures("db_session")
class CheckStockIsDeletableTest:
    def test_ok_if_stock_from_allocine(self):
        provider = offerers_factories.ProviderFactory(localClass="AllocineStocks")
        offer = factories.OfferFactory(lastProvider=provider, idAtProviders="1")
        stock = factories.StockFactory(offer=offer)

        validation.check_stock_is_deletable(stock)  # should not raise

    def test_raise_if_stock_from_provider_that_is_not_allocine(self):
        provider = offerers_factories.ProviderFactory()
        offer = factories.OfferFactory(lastProvider=provider, idAtProviders="1")
        stock = factories.StockFactory(offer=offer)

        with pytest.raises(ApiErrors) as error:
            validation.check_stock_is_deletable(stock)
        assert error.value.errors["global"] == ["Les offres importées ne sont pas modifiables"]

    def test_ok_if_event_stock_started_recently_enough(self):
        recently = datetime.datetime.now() - datetime.timedelta(days=1)
        stock = factories.EventStockFactory(beginningDatetime=recently)

        validation.check_stock_is_deletable(stock)  # should not raise

    def test_raise_if_event_stock_started_long_ago(self):
        too_long_ago = datetime.datetime.now() - datetime.timedelta(days=3)
        stock = factories.EventStockFactory(beginningDatetime=too_long_ago)

        with pytest.raises(exceptions.TooLateToDeleteStock):
            validation.check_stock_is_deletable(stock)


class CheckThumbQualityTest:
    def test_an_error_is_raised_if_the_thumb_width_is_less_than_400_px(self):
        image_as_bytes = (IMAGES_DIR / "mouette_portrait.jpg").read_bytes()

        with pytest.raises(ApiErrors) as error:
            validation.check_mediation_thumb_quality(image_as_bytes)

        assert error.value.errors["thumb"] == ["L'image doit faire 400 * 400 px minimum"]

    def test_an_error_is_raised_if_the_thumb_height_is_less_than_400_px(self):
        image_as_bytes = (IMAGES_DIR / "mouette_landscape.jpg").read_bytes()

        with pytest.raises(ApiErrors) as error:
            validation.check_mediation_thumb_quality(image_as_bytes)

        assert error.value.errors["thumb"] == ["L'image doit faire 400 * 400 px minimum"]

    def test_no_error_is_raised_if_the_thumb_is_heavier_than_100_ko(self):
        image_as_bytes = (IMAGES_DIR / "mouette_full_size.jpg").read_bytes()
        validation.check_mediation_thumb_quality(image_as_bytes)  # should not raise


class GetDistantImageTest:
    def test_ok_with_headers(self, requests_mock):
        remote_image_url = "https://example.com/image.jpg"
        requests_mock.get(
            remote_image_url,
            headers={"content-type": "image/jpeg", "content-length": "4"},
            content=b"\xff\xd8\xff\xd9",
        )

        validation.get_distant_image(
            url=remote_image_url,
            accepted_types=("jpeg", "jpg"),
            max_size=100000,
        )

    def test_ok_without_headers(self, requests_mock):
        remote_image_url = "https://example.com/image.jpg"
        requests_mock.get(
            remote_image_url,
            headers={},
            content=b"\xff\xd8\xff\xd9",
        )

        validation.get_distant_image(
            url=remote_image_url,
            accepted_types=("jpeg", "jpg"),
            max_size=100000,
        )

    def test_unaccessible_file(self, requests_mock):
        remote_image_url = "https://example.com/this-goes-nowhere"
        requests_mock.get(
            remote_image_url,
            status_code=404,
        )

        with pytest.raises(exceptions.FailureToRetrieve):
            validation.get_distant_image(
                url=remote_image_url,
                accepted_types=("jpeg", "jpg"),
                max_size=100000,
            )

    def test_content_length_header_too_large(self, requests_mock):
        remote_image_url = "https://example.com/image.jpg"
        requests_mock.get(
            remote_image_url,
            headers={"content-type": "image/jpeg", "content-length": "2000"},
            content=b"\xff\xd8\xff\xd9",
        )

        with pytest.raises(exceptions.FileSizeExceeded):
            validation.get_distant_image(
                url=remote_image_url,
                accepted_types=("jpeg", "jpg", "png"),
                max_size=1000,
            )

    def test_content_type_header_not_accepted(self, requests_mock):
        remote_image_url = "https://example.com/image.gif"
        requests_mock.get(
            remote_image_url,
            headers={"content-type": "image/gif", "content-length": "27661"},
        )

        with pytest.raises(exceptions.UnacceptedFileType):
            validation.get_distant_image(
                url=remote_image_url,
                accepted_types=("jpeg", "jpg", "png"),
                max_size=100000,
            )

    def test_timeout(self, requests_mock):
        remote_image_url = "https://example.com/image.jpg"
        requests_mock.get(remote_image_url, exc=requests.exceptions.ConnectTimeout)

        with pytest.raises(exceptions.FailureToRetrieve):
            validation.get_distant_image(
                url=remote_image_url,
                accepted_types=("jpeg", "jpg"),
                max_size=100000,
            )

    def test_content_too_large(self, requests_mock):
        remote_image_url = "https://example.com/image.jpg"
        requests_mock.get(remote_image_url, content=b"1234567890")

        with pytest.raises(exceptions.FileSizeExceeded):
            validation.get_distant_image(
                url=remote_image_url,
                accepted_types=("jpeg", "jpg", "png"),
                max_size=5,
            )


class CheckImageTest:
    def test_ok(self):
        image_as_bytes = (IMAGES_DIR / "mouette_full_size.jpg").read_bytes()
        validation.check_image(
            image_as_bytes,
            accepted_types=("jpeg", "jpg"),
            min_width=400,
            min_height=400,
        )

    def test_image_too_small(self):
        image_as_bytes = (IMAGES_DIR / "mouette_portrait.jpg").read_bytes()
        with pytest.raises(exceptions.ImageTooSmall):
            validation.check_image(
                image_as_bytes,
                accepted_types=("jpeg", "jpg"),
                min_width=400,
                min_height=400,
            )

    def test_fake_jpeg(self):
        image_as_bytes = (IMAGES_DIR / "mouette_fake_jpg.jpg").read_bytes()
        with pytest.raises(exceptions.UnacceptedFileType):
            validation.check_image(
                image_as_bytes,
                accepted_types=("jpeg", "jpg"),
                min_width=1,
                min_height=1,
            )

    def test_wrong_format(self):
        image_as_bytes = (IMAGES_DIR / "mouette_full_size.jpg").read_bytes()
        with pytest.raises(exceptions.UnacceptedFileType):
            validation.check_image(
                image_as_bytes,
                accepted_types=("png",),
                min_width=1,
                min_height=1,
            )
