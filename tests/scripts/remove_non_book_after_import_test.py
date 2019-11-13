from pathlib import Path
from unittest.mock import patch

import os

from models import Product, PcObject
from scripts.remove_non_book_after_import import remove_non_book_after_import, read_isbn_from_file
from tests.conftest import clean_database
from tests.test_utils import create_product_with_thing_type, create_user, create_offerer, create_venue, \
    create_offer_with_thing_product, create_stock, create_booking


@clean_database
@patch('scripts.remove_non_book_after_import.read_isbn_from_file')
def test_remove_only_unwanted_book(read_isbn_from_file_mock, app):
    # Given
    unwanted_isbn = '9876543211231'
    conform_isbn = '0987654567098'
    product1 = create_product_with_thing_type(id_at_providers=unwanted_isbn)
    product2 = create_product_with_thing_type(id_at_providers=conform_isbn)

    read_isbn_from_file_mock.return_value = [
        '9876543211231',
        '1234567890981',
        '4567890987652',
        '0987467896549'
    ]
    PcObject.save(product1, product2)

    # When
    remove_non_book_after_import('mon_fichier_isbns.txt')

    # Then
    assert Product.query.count() == 1


@clean_database
@patch('scripts.remove_non_book_after_import.read_isbn_from_file')
def test_should_not_delete_product_with_bookings(read_isbn_from_file_mock, app):
    # Given
    unwanted_isbn = '9876543211231'
    product = create_product_with_thing_type(id_at_providers=unwanted_isbn)
    user = create_user()
    offerer = create_offerer(siren='775671464')
    venue = create_venue(offerer, name='Librairie Titelive', siret='77567146400110')
    offer = create_offer_with_thing_product(venue, product=product)
    stock = create_stock(offer=offer, price=0)
    booking = create_booking(user=user, stock=stock)
    PcObject.save(venue, product, offer, stock, booking, user)

    read_isbn_from_file_mock.return_value = [
        '9876543211231',
        '1234567890981',
        '4567890987652',
        '0987467896549'
    ]
    PcObject.save(product)

    # When
    remove_non_book_after_import('mon_fichier_isbns.txt')

    # Then
    assert Product.query.count() == 1


def test_read_isbn_from_file(app):
    # Given
    file_path = Path(os.path.dirname(os.path.realpath(__file__))) \
                / '..' / '..' / 'sandboxes' / 'scripts' / 'isbn_test_file.txt'

    # When
    book_isbns = read_isbn_from_file(file_path)

    # Then
    assert len(book_isbns) == 2
    assert book_isbns[0] == '9876543211231'
    assert book_isbns[1] == '9876543211224'
