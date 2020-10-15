from pcapi.domain.venue.venue_with_offerer_name.venue_with_offerer_name import VenueWithOffererName
from pcapi.routes.serialization.venues_serialize import serialize_venues_with_offerer_name
from pcapi.utils.human_ids import humanize


class SerializeVenuesWithOffererNameTest:
    def test_should_return_json_with_expected_information(self):
        # Given
        venue_1 = VenueWithOffererName(identifier=1, name='Librairie Kléber', offerer_name='Gilbert Joseph',
                                       is_virtual=True)
        venue_2 = VenueWithOffererName(identifier=2, name='Librairie Réjean', offerer_name='Gilbert Joseph',
                                       public_name='Mon gérant de librairies', is_virtual=False)

        # When
        response = serialize_venues_with_offerer_name([venue_1, venue_2])

        # Then
        assert response == [
            {
                'id': f'{humanize(venue_1.identifier)}',
                'name': venue_1.name,
                'offererName': venue_1.offerer_name,
                'publicName': None,
                'isVirtual': venue_1.is_virtual,
            },
            {
                'id': f'{humanize(venue_2.identifier)}',
                'name': venue_2.name,
                'offererName': venue_2.offerer_name,
                'publicName': 'Mon gérant de librairies',
                'isVirtual': venue_2.is_virtual,
            }
        ]
