""" update providables """
import traceback
from pprint import pprint

from flask import current_app as app

import local_providers
from models import VenueProvider # pas besoin de faire un import de venue_provider.py ?


@app.manager.option('-p',
                    '--provider-name',
                    help='Limit update to this provider name')
@app.manager.option('-l',
                    '--limit',
                    help='Limit update to n items per providerName/venueId'
                         + ' (for test purposes)', type=int)
@app.manager.option('-w',
                    '--venue-provider-id',
                    help='Limit update to this venue provider id')
def update_providables(provider_name: str, venue_provider_id: str, limit: int):
    if (provider_name and venue_provider_id) or not (provider_name or venue_provider_id):
        raise ValueError('Call either with provider-name or venue-provider-id')

    if provider_name:
        ProviderClass = get_class_by_name(provider_name)
        provider = ProviderClass()
        return do_update(provider, limit)

    if venue_provider_id:
        venue_provider = VenueProvider.query.get(venue_provider_id)
        ProviderClass = get_class_by_name(venue_provider.provider.localClass)
        provider = ProviderClass(venue_provider)
        return do_update(provider, limit)

@app.manager.option('-p',
                    '--provider-id',
                    help='Update providables for this provider')
def update_providables_by_provider_id(provider_id: int):
    print('provider_id : ' + provider_id)
    venue_providers = VenueProvider.query.filter(VenueProvider.providerId == provider_id).all()
    print('venue_providers : ' , venue_providers)
    for venue_provider in venue_providers:
        ProviderClass = get_class_by_name(venue_provider.provider.localClass)
        provider = ProviderClass(venue_provider)
        # do_update(provider)
    pass


def do_update(provider, limit):
    try:
        provider.updateObjects(limit)
    except Exception as e:
        print('ERROR: '+e.__class__.__name__+' '+str(e))
        traceback.print_tb(e.__traceback__)
        pprint(vars(e))


def get_class_by_name(class_name: str):
    return getattr(local_providers, class_name)

