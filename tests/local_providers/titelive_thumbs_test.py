""" local providers test """
from datetime import datetime

from pathlib import Path
from unittest.mock import patch

import os
from zipfile import ZipFile

from local_providers import TiteLiveThingThumbs
from local_providers.titelive_thing_thumbs import THUMB_FOLDER_NAME_TITELIVE, extract_thumb_index
from models import PcObject, ThingType, Product
from tests.conftest import clean_database
from tests.test_utils import provider_test, \
    create_product_with_thing_type, \
    create_provider, \
    create_providable_info
from tests.local_providers.provider_test_utils import TestLocalProvider

class TiteliveThingThumbsTest:
    class ExtractThumbIndexTest:
        def test_return_0_for_filename_with_1_75(self):
            # Given
            filename = "9780847858903_1_75.jpg"

            # When
            thumb_index = extract_thumb_index(filename)

            # Then
            assert thumb_index == 0

        def test_return_3_for_filename_with_4(self):
            # Given
            filename = "9780847858903_4_75.jpg"

            # When
            thumb_index = extract_thumb_index(filename)

            # Then
            assert thumb_index == 3

    @clean_database
    @patch('local_providers.titelive_thing_thumbs.get_files_to_process_from_titelive_ftp')
    @patch('local_providers.titelive_thing_thumbs.get_zip_file_from_ftp')
    def test_compute_first_thumb_dominant_color_even_if_not_first_file(self,
                                                                       get_thumbs_zip_file_from_ftp,
                                                                       get_ordered_thumbs_zip_files,
                                                                       app):
        # given
        product1 = create_product_with_thing_type(id_at_providers='9780847858903', thumb_count=0)
        product2 = create_product_with_thing_type(id_at_providers='9782016261903', thumb_count=0)
        PcObject.save(product1, product2)
        zip_thumb_file = get_zip_thumb_file_for_test_compute_first_thumb_color_dominant()
        get_ordered_thumbs_zip_files.return_value = [zip_thumb_file]
        get_thumbs_zip_file_from_ftp.side_effect = [get_zip_file_from_sandbox(zip_thumb_file)]

        # Import thumbs for existing things
        provider_test(app,
                      TiteLiveThingThumbs,
                      None,
                      checkedObjects=2,
                      createdObjects=0,
                      updatedObjects=2,
                      erroredObjects=0,
                      checkedThumbs=2,
                      createdThumbs=5,
                      updatedThumbs=0,
                      erroredThumbs=0,
                      Product=0
                      )

    @clean_database
    @patch('local_providers.titelive_thing_thumbs.get_files_to_process_from_titelive_ftp')
    @patch('local_providers.titelive_thing_thumbs.get_zip_file_from_ftp')
    def test_updates_thumb_count_for_product_when_new_thumbs_added(self,
                                                                       get_thumbs_zip_file_from_ftp,
                                                                       get_ordered_thumbs_zip_files,
                                                                       app):
        # Given
        product1 = create_product_with_thing_type(id_at_providers='9780847858903', thumb_count=0)
        PcObject.save(product1)
        zip_thumb_file = get_zip_thumb_file_for_test_updates_thumb_count_for_product()
        get_ordered_thumbs_zip_files.return_value = [zip_thumb_file]
        get_thumbs_zip_file_from_ftp.side_effect = [get_zip_file_from_sandbox(zip_thumb_file)]

        provider_object = TiteLiveThingThumbs()
        provider_object.provider.isActive = True
        PcObject.save(provider_object.provider)

        # When
        provider_object.updateObjects()

        # Then
        new_product = Product.query.one()
        assert new_product.name == 'Test Book'
        assert new_product.thumbCount == 1

def get_zip_thumb_file_for_test_compute_first_thumb_color_dominant():
    return get_zip_thumbs_file_from_named_sandbox_file('test_livres_tl20190505.zip')

def get_zip_thumb_file_for_test_updates_thumb_count_for_product():
    return get_zip_thumbs_file_from_named_sandbox_file('test_livres_tl20191104.zip')

def get_zip_thumbs_file_from_named_sandbox_file(file_name):
    data_root_path = Path(os.path.dirname(os.path.realpath(__file__))) \
                     / '..' / '..' / 'sandboxes' / 'providers' / 'titelive_works'
    return data_root_path / THUMB_FOLDER_NAME_TITELIVE / file_name


def get_zip_file_from_sandbox(file):
    return ZipFile(file)
