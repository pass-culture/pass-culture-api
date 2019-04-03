from unittest.mock import patch, MagicMock, call

import pytest

from models import PcObject
from scripts.init_titelive.import_thumbs import import_init_titelive_thumbs, \
    get_titelive_thumb_names_group_by_id_at_providers
from tests.conftest import clean_database
from tests.test_utils import create_offerer, create_venue, create_thing
from utils.human_ids import humanize


@pytest.mark.standalone
class InitTiteliveThumbsTest:

    @clean_database
    @patch('scripts.init_titelive.import_thumbs.compute_dominant_color')
    def test_register_image_from_object_storage_second_version(self,
                                                               compute_dominant_color,
                                                               app):
        # given
        offerer = create_offerer(siren='987654321')
        venue = create_venue(offerer, name='Librairie Titelive', siret='77567146400110')
        PcObject.check_and_save(venue)

        thing_1 = create_thing(id_at_providers='3663608844000',
                               thumb_count=0)

        PcObject.check_and_save(thing_1)

        filename_to_save_1 = 'thumbs/titelive/3663608844000_1_v.jpg'
        filename_to_save_2 = 'thumbs/titelive/3663608844000_1_75.jpg'

        connexion = MagicMock()
        connexion.get_container = MagicMock()
        connexion.get_container.return_value = [
            {'config'},
            [
                {
                    "name": filename_to_save_1
                },
                {
                    "name": filename_to_save_2
                }
            ]
        ]

        connexion.get_object = MagicMock()
        connexion.get_object.side_effect = [filename_to_save_1,
                                            filename_to_save_2]

        connexion.put_object = MagicMock()
        connexion.delete_object = MagicMock()

        compute_dominant_color.return_value = b'\x00\x00\x00'

        container_name = "storage-pc-testing"
        titelive_thumb_identifier = 'titelive/'

        # when
        import_init_titelive_thumbs(connexion, container_name, titelive_thumb_identifier)

        # then
        assert thing_1.thumbCount == 2
        assert thing_1.firstThumbDominantColor == b'\x00\x00\x00'

        assert connexion.get_object.call_count == 2
        assert connexion.get_object.call_args_list[0] == call(container_name, filename_to_save_1)
        assert connexion.get_object.call_args_list[1] == call(container_name, filename_to_save_2)

        assert connexion.put_object.call_args_list[0] == call(container_name,
                                                              'thumbs/things/' + humanize(thing_1.id),
                                                              content_type='image/jpeg', contents='h')
        assert connexion.put_object.call_args_list[1] == call(container_name,
                                                              'thumbs/things/' + humanize(thing_1.id) + '_1',
                                                              content_type='image/jpeg', contents='h')

        assert connexion.delete_object.call_args_list[0] == call(container_name, filename_to_save_1)
        assert connexion.delete_object.call_args_list[1] == call(container_name, filename_to_save_2)

    @clean_database
    def test_get_titelive_thumb_names_group_by_id_at_providers(self, app):
        filename_to_save_1 = 'thumbs/titelive/3663608844000_1_v.jpg'
        filename_to_save_2 = 'thumbs/titelive/3663608844000_1_75.jpg'

        connexion = MagicMock()
        connexion.get_container = MagicMock()
        connexion.get_container.return_value = [
            {'config'},
            [
                {
                    "name": filename_to_save_1
                },
                {
                    "name": filename_to_save_2
                }
            ]
        ]

        container_name = "storage-pc-testing"
        titelive_thumb_identifier = 'titelive/'

        images_name_in_object_storage = get_titelive_thumb_names_group_by_id_at_providers(connexion,
                                                                                          container_name,
                                                                                          titelive_thumb_identifier)

        connexion.get_container.assert_called_once_with(container_name)
        assert '3663608844000' in images_name_in_object_storage
        assert filename_to_save_1 in images_name_in_object_storage['3663608844000']
        assert filename_to_save_2 in images_name_in_object_storage['3663608844000']
