from flask import Flask
from flask_script import Manager
from sqlalchemy import func
from glob import glob
from inspect import isclass

from utils.human_ids import dehumanize
from utils.object_storage import STORAGE_DIR


app = Flask(__name__)


def create_app(env=None):
    app.env = env
    return app


app.manager = Manager(create_app)

savedCounts = {}

with app.app_context():
    import models
    import local_providers

    def saveCounts():
        for modelName in app.model:
            if isclass(app.model[modelName])\
               and issubclass(app.model[modelName], app.model.PcObject)\
               and modelName != "PcObject":
                savedCounts[modelName] = app.model[modelName].query.count()

    def assertCreatedCounts(**counts):
        for modelName in counts:
            print(savedCounts)
            print(app.model[modelName])
            print(savedCounts[modelName])
            assert app.model[modelName].query.count() - savedCounts[modelName]\
                   == counts[modelName]

    def assertEmptyDb():
        for modelName in app.model:
            if isinstance(app.model[modelName], app.model.PcObject):
                if modelName == 'Mediation':
                    assert app.model[modelName].query.count() == 2
                else:
                    assert app.model[modelName].query.count() == 0
        assert len(glob(str(STORAGE_DIR / "thumbs" / "*"))) == 1

    def provider_test(provider, venueProvider, **counts):
        with app.app_context():
            providerObj = provider(venueProvider, mock=True)
            providerObj.dbObject.isActive = True
            app.model.PcObject.check_and_save(providerObj.dbObject)
            saveCounts()
            providerObj.updateObjects()
            for countName in ['updatedObjects',
                              'createdObjects',
                              'checkedObjects',
                              'erroredObjects',
                              'createdThumbs',
                              'updatedThumbs',
                              'checkedThumbs',
                              'erroredThumbs']:
                assert getattr(providerObj, countName) == counts[countName]
                del counts[countName]
            assertCreatedCounts(**counts)

    def test_10_titelive_venues_provider():
        assertEmptyDb()
        provider_test(app.local_providers.TiteLiveVenues,
                      None,
                      checkedObjects=6,
                      createdObjects=6,
                      updatedObjects=0,
                      erroredObjects=0,
                      checkedThumbs=0,
                      createdThumbs=0,
                      updatedThumbs=0,
                      erroredThumbs=0,
                      Venue=2,
                      Offerer=2)
        with app.app_context():
            provider = app.model.Provider.getByClassName('TiteLiveOffers')
            for vp in app.model.VenueProvider.query\
                               .filter_by(provider=provider)\
                               .all():
                assert vp.isActive == False
                vp.isActive = True
                app.model.PcObject.check_and_save(vp)

    def test_11_titelive_things_provider():
        provider_test(app.local_providers.TiteLiveThings,
                      None,
                      checkedObjects=422,
                      createdObjects=355,
                      updatedObjects=13,
                      erroredObjects=0,
                      checkedThumbs=0,
                      createdThumbs=0,
                      updatedThumbs=0,
                      erroredThumbs=0,
                      Thing=355
                      )

    def test_12_titelive_thing_thumbs_provider():
        provider_test(app.local_providers.TiteLiveBookThumbs,
                      None,
                      checkedObjects=106,
                      createdObjects=0,
                      updatedObjects=0,
                      erroredObjects=0,
                      checkedThumbs=166,
                      createdThumbs=92,
                      updatedThumbs=0,
                      erroredThumbs=0,
                      Thing=0
                      )
        with app.app_context():
            assert app.db.session.query(func.sum(app.model.Thing.thumbCount))\
                                 .scalar() == 92

    def test_13_titelive_thing_desc_provider():
        provider_test(app.local_providers.TiteLiveBookDescriptions,
                      None,
                      checkedObjects=6,
                      createdObjects=0,
                      updatedObjects=6,
                      erroredObjects=0,
                      checkedThumbs=0,
                      createdThumbs=0,
                      updatedThumbs=0,
                      erroredThumbs=0,
                      Thing=0
                      )

    def test_14_titelive_offer_provider():
        with app.app_context():
            venueProvider = app.model.VenueProvider.query\
                                 .filter_by(venueIdAtOfferProvider='2949')\
                                 .one_or_none()
        assert venueProvider is not None
        provider_test(app.local_providers.TiteLiveOffers,
                      venueProvider,
                      checkedObjects=388,
                      createdObjects=370,
                      updatedObjects=0,
                      erroredObjects=0,
                      checkedThumbs=0,
                      createdThumbs=0,
                      updatedThumbs=0,
                      erroredThumbs=0,
                      Occasion=185,
                      Offer=185
                      )

        with app.app_context():
            venueProvider = app.model.VenueProvider.query\
                                 .filter_by(venueIdAtOfferProvider='2921')\
                                 .one_or_none()
        assert venueProvider is not None
        provider_test(app.local_providers.TiteLiveOffers,
                      venueProvider,
                      checkedObjects=370,
                      createdObjects=332,
                      updatedObjects=0,
                      erroredObjects=0,
                      checkedThumbs=0,
                      createdThumbs=0,
                      updatedThumbs=0,
                      erroredThumbs=0,
                      Occasion=166,
                      Offer=166
                      )

    def test_15_spreadsheet_exp_venues_provider():
        provider_test(app.local_providers.SpreadsheetExpVenues,
                      None,
                      checkedObjects=18,
                      createdObjects=18,
                      updatedObjects=0,
                      erroredObjects=0,
                      checkedThumbs=0,
                      createdThumbs=0,
                      updatedThumbs=0,
                      erroredThumbs=0,
                      Venue=9,
                      Offerer=9)

    def test_15_spreadsheet_exp_offers_provider():
        provider_test(app.local_providers.SpreadsheetExpOffers,
                      None,
                      checkedObjects=489,
                      createdObjects=482,
                      updatedObjects=0,
                      erroredObjects=0,
                      checkedThumbs=0,
                      createdThumbs=0,
                      updatedThumbs=0,
                      erroredThumbs=0,
                      Venue=0,
                      Offerer=0)

    def test_16_openagenda_events_provider():
        with app.app_context():
            oa_provider = app.model.Provider.getByClassName('OpenAgendaEvents')
            venueProvider = app.model.VenueProvider()
            venueProvider.venueId = dehumanize('AE')
            venueProvider.provider = oa_provider
            venueProvider.isActive = True
            venueProvider.venueIdAtOfferProvider = '49050769'
            app.model.PcObject.check_and_save(venueProvider)
            venueProvider = app.model.VenueProvider.query\
                                 .filter_by(venueIdAtOfferProvider='49050769')\
                                 .one_or_none()
        provider_test(app.local_providers.OpenAgendaEvents,
                      venueProvider,
                      checkedObjects=18,
                      createdObjects=18,
                      updatedObjects=0,
                      erroredObjects=0,
                      checkedThumbs=3,
                      createdThumbs=3,
                      updatedThumbs=0,
                      erroredThumbs=0,
                      Event=3,
                      EventOccurence=12,
                      Occasion=3,
                      Offer=0,
                      Venue=0,
                      Offerer=0)
 

    def test_99_init():
        with app.app_context():
            saveCounts()
            import scripts
            from scripts.sandbox import sandbox
            sandbox()
            assertCreatedCounts(User=3)
