from models.versioned_mixin import VersionedMixin
from models.api_errors import ApiErrors
from models.pc_object import PcObject
from models.deactivable_mixin import DeactivableMixin
from models.extra_data_mixin import ExtraDataMixin
from models.has_address_mixin import HasAddressMixin
from models.has_thumb_mixin import HasThumbMixin
from models.needs_validation_mixin import NeedsValidationMixin
from models.providable_mixin import ProvidableMixin
from models.booking import Booking
from models.event import Event
from models.event_occurence import EventOccurence
from models.mediation import Mediation
from models.offer import Offer
from models.offerer import Offerer
from models.venue_provider import VenueProvider
from models.local_provider_event import LocalProviderEvent
from models.local_provider import LocalProvider
from models.occasion import Occasion
from models.provider import Provider
from models.recommendation import Recommendation
from models.thing import Thing
from models.user_offerer import UserOfferer
from models.user import User
from models.venue import Venue

from glob import glob
import random
import sys

ok={'9780500019917': True,
    '9780500050965': True,
    '9780500051917': True,
    '9780500279960': True,
    '9780500283967': True,
    '9780500285954': True,
    '9780500287972': True,
    '9780500288955': True,
    '9780500292907': True,
    '9780500292914': True,
    '9780500292921': True,
    '9780500292945': True,
    '9780500300992': True,
    '9780500410974': True,
    '9780500512951': True,
    '9780500515990': True,
    '9780500516904': True,
    '9780500517994': True,
    '9780500518915': True,
    '9780500650981': True,
    '9780692298916': True,
    '9780692496954': True,
    '9780847858903': True,
    '9780847861996': True,
    '9780870700989': True,
    '9780870704901': True,
    '9781584232933': True,
    '9781616896959': True,
    '9781616896973': True,
    '9781780676968': True,
    '9781786271914': True,
    '9781786271921': True,
    '9781786271945': True,
    '9781786271976': True,
    '9781786271990': True,
    '9781848857988': True,
    '9781851498901': True,
    '9781851498963': True,
    '9782016261903': True,
    '9782016261910': True,
    '9782016266939': True,
    '9782017022077': True,
    '9782017038092': True,
    '9782035950901': True,
    '9782100775064': True,
    '9782100775972': True,
    '9782204125987': True,
    '9782212565935': True,
    '9782212674910': True,
    '9782221190081': True,
    '9782221216040': True,
    '9782226393920': True,
    '9782297068901': True,
    '9782297068918': True,
    '9782322102990': True,
    '9782340022980': True,
    '9782343105987': True,
    '9782343140919': True,
    '9782344026953': True,
    '9782360545094': True,
    '9782367600963': True,
    '9782367740911': True,
    '9782378150020': True,
    '9782501126908': True,
    '9782713226946': True,
    '9782714312020': True,
    '9782749933948': True,
    '9782756091020': True,
    '9782806307989': True,
    '9782817606002': True,
    '9782817606064': True,
    '9782822605960': True,
    '9782843378966': True,
    '9782843378997': True,
    '9782844208934': True,
    '9782846792974': True,
    '9782847208092': True,
    '9782851171962': True,
    '9782877069922': True,
    '9782889275090': True,
    '9782908481921': True,
    '9783037780923': True,
    '9783037784990': True,
    '9791021020931': True,
    '9791025102916': True,
    '9791028101923': True,
    '9791097249083': True,
    '9791097309022': True,
    '9791097309053': True}

for file in glob('livre3_11/*.tit'):
    print(file)
    with open(file, "r", encoding='iso-8859-1') as f:
        for line in f.readlines():
            if line.split("~")[0] in ok or random.randint(0,100)>99:
                sys.stdout.write(line)
            
