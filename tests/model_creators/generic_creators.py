from datetime import datetime, timedelta
from hashlib import sha256
from typing import Optional


from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon

from local_providers.price_rule import PriceRule
from models import ApiKey, BankInformation, BeneficiaryImport, \
    BeneficiaryImportStatus, Booking, Criterion, Deposit, \
    Email, Favorite, ImportStatus, Mediation, Offer, Offerer, \
    Payment, PaymentMessage, PaymentStatus, Provider, \
    Recommendation, RightsType, Stock, ThingType, User, \
    UserOfferer, Venue, AllocineVenueProviderPriceRule, AllocinePivot, VenueProvider, IrisFrance, IrisVenues
from models.allocine_venue_provider import AllocineVenueProvider
from models.email import EmailStatus
from domain.payments import PaymentDetails
from models.payment_status import TransactionStatus
from scripts.iris.import_iris import WGS_SPATIAL_REFERENCE_IDENTIFIER, create_centroid_from_polygon
from tests.model_creators.specific_creators import create_offer_with_thing_product, create_stock_with_thing_offer
from utils.token import random_token

API_URL = 'http://localhost:5000'
DEFAULT_USER = User()
PLAIN_DEFAULT_TESTING_PASSWORD = 'user@AZERTY123'
DEFAULT_USER.setPassword(PLAIN_DEFAULT_TESTING_PASSWORD)
HASHED_DEFAULT_TESTING_PASSWORD = DEFAULT_USER.password


def create_api_key(idx: int = None,
                   offerer_id: int = 99,
                   value: str = 'A_MOCKED_API_KEY') -> ApiKey:
    api_key = ApiKey()
    api_key.id = idx
    api_key.offererId = offerer_id
    api_key.value = value

    return api_key


def create_bank_information(application_id: int = 1,
                            bic: str = 'QSDFGH8Z555',
                            date_modified_at_last_provider: datetime = None,
                            iban: str = 'FR7630006000011234567890189',
                            idx: int = None,
                            id_at_providers: str = None,
                            last_provider_id: int = None,
                            offerer: Offerer = None,
                            venue: Venue = None) -> BankInformation:
    bank_information = BankInformation()
    bank_information.applicationId = application_id
    bank_information.bic = bic
    bank_information.dateModifiedAtLastProvider = date_modified_at_last_provider
    bank_information.iban = iban
    bank_information.id = idx
    bank_information.idAtProviders = id_at_providers
    bank_information.lastProviderId = last_provider_id
    bank_information.offerer = offerer
    bank_information.venue = venue

    return bank_information


def create_beneficiary_import(date: datetime = datetime.utcnow(),
                              demarche_simplifiee_application_id: int = 99,
                              detail: str = None,
                              idx: int = None,
                              status: ImportStatus = ImportStatus.CREATED,
                              user: User = None) -> BeneficiaryImport:
    import_status = BeneficiaryImportStatus()
    import_status.date = date
    import_status.detail = detail
    import_status.status = status

    beneficiary_import = BeneficiaryImport()
    beneficiary_import.id = idx
    beneficiary_import.beneficiary = user
    beneficiary_import.demarcheSimplifieeApplicationId = demarche_simplifiee_application_id
    beneficiary_import.statuses = [import_status]

    return beneficiary_import


def create_booking(user: User,
                   amount: int = None,
                   date_created: datetime = datetime.utcnow(),
                   date_used: datetime = None,
                   idx: int = None,
                   is_cancelled: bool = False,
                   is_used: bool = False,
                   quantity: int = 1,
                   recommendation: Recommendation = None,
                   stock: Stock = None,
                   token: str = None,
                   venue: Venue = None) -> Booking:
    booking = Booking()
    offerer = create_offerer(siren='987654321', address='Test address', city='Test city', postal_code='93000',
                             name='Test name')
    if venue is None:
        venue = create_venue(offerer=offerer, name='Test offerer', booking_email='reservations@test.fr',
                             address='123 rue test', postal_code='93000', city='Test city', departement_code='93')
    if stock is None:
        price = amount if amount is not None else 10
        product_with_thing_type = create_offer_with_thing_product(venue)
        stock = create_stock_with_thing_offer(offerer, venue, product_with_thing_type, price=price)

    if recommendation:
        booking.recommendation = recommendation
    elif not stock.offer:
        offer = create_offer_with_thing_product(venue)
        booking.recommendation = create_recommendation(offer=offer, user=user)

    booking.user = user
    booking.amount = stock.price
    booking.dateCreated = date_created
    booking.dateUsed = date_used
    booking.id = idx
    booking.isCancelled = is_cancelled
    booking.isUsed = is_used
    booking.quantity = quantity
    booking.stock = stock
    booking.token = token if token is not None else random_token()
    booking.userId = user.id

    return booking


def create_criterion(description: str = None,
                     name: str = 'best offer',
                     score_delta: int = 1) -> Criterion:
    criterion = Criterion()
    criterion.name = name
    criterion.description = description
    criterion.scoreDelta = score_delta

    return criterion


def create_deposit(user: User,
                   amount: int = 500,
                   date_created: datetime = datetime.utcnow(),
                   idx: int = None,
                   source: str = 'public') -> Deposit:
    deposit = Deposit()
    deposit.amount = amount
    deposit.dateCreated = date_created
    deposit.id = idx
    deposit.source = source
    deposit.user = user

    return deposit


def create_email(content: str,
                 idx: int = None,
                 status: EmailStatus = EmailStatus.ERROR,
                 time: datetime = datetime.utcnow()) -> Email:
    email = Email()
    email.content = content
    email.datetime = time
    email.id = idx
    email.status = status

    return email


def create_favorite(idx: int = None,
                    mediation: Mediation = None,
                    offer: Offer = None,
                    user: User = None) -> Favorite:
    favorite = Favorite()
    favorite.id = idx
    favorite.mediation = mediation
    favorite.offer = offer
    favorite.user = user

    return favorite


def create_mediation(offer: Offer = None,
                     author: User = None,
                     back_text: str = None,
                     credit: str = None,
                     date_created: datetime = datetime.utcnow(),
                     date_modified_at_last_provider: datetime = None,
                     front_text: str = None,
                     id_at_providers: str = None,
                     idx: int = None,
                     is_active: bool = True,
                     last_provider_id: int = None,
                     thumb_count: int = 0,
                     tuto_index: int = None,
                     ) -> Mediation:
    mediation = Mediation()
    mediation.author = author
    mediation.backText = back_text
    mediation.credit = credit
    mediation.dateCreated = date_created
    mediation.dateModifiedAtLastProvider = date_modified_at_last_provider
    mediation.frontText = front_text
    mediation.idAtProviders = id_at_providers
    mediation.id = idx
    mediation.isActive = is_active
    mediation.lastProviderId = last_provider_id
    mediation.offer = offer
    mediation.thumbCount = thumb_count
    mediation.tutoIndex = tuto_index

    return mediation


def create_offerer(address: str = None,
                   city: str = 'Montreuil',
                   date_created: datetime = datetime.utcnow(),
                   date_modified_at_last_provider: datetime = None,
                   idx: int = None,
                   id_at_providers: str = None,
                   is_active: bool = True,
                   last_provider_id: int = None,
                   name: str = 'Test Offerer',
                   postal_code: str = '93100',
                   siren: Optional[str] = '123456789',
                   thumb_count: int = 0,
                   validation_token: str = None) -> Offerer:
    offerer = Offerer()
    offerer.address = address
    offerer.city = city
    offerer.dateCreated = date_created
    offerer.dateModifiedAtLastModified = date_modified_at_last_provider
    offerer.id = idx
    offerer.idAtProviders = id_at_providers
    offerer.isActive = is_active
    offerer.lastProviderId = last_provider_id
    offerer.name = name
    offerer.postalCode = postal_code
    offerer.siren = siren
    offerer.thumbCount = thumb_count
    offerer.validationToken = validation_token

    return offerer


def create_payment(booking: Booking,
                   offerer: Offerer,
                   amount: int = 10,
                   author: str = 'test author',
                   bic: str = None,
                   comment: str = None,
                   iban: str = None,
                   idx: int = None,
                   payment_message: PaymentMessage = None,
                   payment_message_name: str = None,
                   reimbursement_rate: float = 0.5,
                   reimbursement_rule: str = 'remboursement à 100%',
                   status: TransactionStatus = TransactionStatus.PENDING,
                   detail: str = None,
                   status_date: datetime = datetime.utcnow(),
                   transaction_end_to_end_id: str = None,
                   transaction_label: str = None) -> Payment:
    payment_status = PaymentStatus()
    payment_status.status = status
    payment_status.date = status_date
    payment_status.detail = detail

    payment = Payment()
    payment.amount = amount
    payment.author = author
    payment.bic = bic
    payment.booking = booking
    payment.comment = comment
    payment.iban = iban
    payment.id = idx
    if payment_message_name:
        payment.paymentMessage = create_payment_message(name=payment_message_name)
    elif payment_message:
        payment.paymentMessage = payment_message
    payment.recipientName = offerer.name
    payment.recipientSiren = offerer.siren
    payment.reimbursementRate = reimbursement_rate
    payment.reimbursementRule = reimbursement_rule
    payment.statuses = [payment_status]
    payment.transactionEndToEndId = transaction_end_to_end_id
    payment.transactionLabel = transaction_label

    return payment


def create_payment_details(booking_amount: int = 15,
                           booking_date: datetime = datetime.utcnow() - timedelta(days=10),
                           booking_used_date: datetime = datetime.utcnow() - timedelta(days=5),
                           booking_user_email: str = 'john.doe@example.com',
                           booking_user_id: int = 1234,
                           offer_name: str = 'Blake & Mortimer',
                           offer_type: ThingType = ThingType.LIVRE_EDITION,
                           offerer_name: str = 'Les petites librairies',
                           offerer_siren: str = '123456789',
                           payment_iban: str = 'FR7630001007941234567890185',
                           payment_id: int = 123,
                           payment_message_name: str = 'AZERTY123456',
                           reimbursed_amount: float = 7.5,
                           reimbursement_rate: float = 0.5,
                           transaction_end_to_end_id: str = None,
                           venue_name: str = 'Vive les BDs',
                           venue_siret: str = '12345678912345',
                           venue_humanized_id: str = 'AE') -> PaymentDetails:
    payment_details = PaymentDetails()
    payment_details.booking_amount = booking_amount
    payment_details.booking_date = booking_date
    payment_details.booking_used_date = booking_used_date
    payment_details.booking_user_email = booking_user_email
    payment_details.booking_user_id = booking_user_id
    payment_details.offer_name = offer_name
    payment_details.offer_type = str(offer_type)
    payment_details.offerer_name = offerer_name
    payment_details.offerer_siren = offerer_siren
    payment_details.payment_iban = payment_iban
    payment_details.payment_id = payment_id
    payment_details.payment_message_name = payment_message_name
    payment_details.reimbursed_amount = reimbursed_amount
    payment_details.reimbursement_rate = reimbursement_rate
    payment_details.transaction_end_to_end_id = transaction_end_to_end_id
    payment_details.venue_name = venue_name
    payment_details.venue_siret = venue_siret
    payment_details.venue_humanized_id = venue_humanized_id

    return payment_details


def create_payment_message(checksum: str = None,
                           idx: int = None,
                           name: str = 'ABCD123') -> PaymentMessage:
    payment_message = PaymentMessage()
    payment_message.checksum = checksum if checksum else sha256(name.encode('utf-8')).digest()
    payment_message.id = idx
    payment_message.name = name

    return payment_message


def create_provider(api_key: str = None,
                    api_key_generation_date: datetime = None,
                    idx: int = None,
                    is_active: bool = True,
                    is_enable_for_pro: bool = True,
                    local_class: str = 'TiteLive',
                    name: str = 'My Test Provider',
                    require_provider_identifier: bool = True) -> Provider:
    provider = Provider()
    provider.apiKey = api_key
    provider.apiKeyGenerationDate = api_key_generation_date
    provider.id = idx
    provider.enabledForPro = is_enable_for_pro
    provider.isActive = is_active
    provider.localClass = local_class
    provider.name = name
    provider.requireProviderIdentifier = require_provider_identifier

    return provider


def create_recommendation(offer: Offer = None,
                          user: User = None,
                          date_created: datetime = datetime.utcnow(),
                          date_read: datetime = None,
                          date_updated: datetime = datetime.utcnow(),
                          idx: int = None,
                          is_clicked: bool = False,
                          is_first: bool = False,
                          mediation: Mediation = None,
                          search: str = None,
                          share_medium: str = None) -> Recommendation:
    recommendation = Recommendation()
    recommendation.dateCreated = date_created
    recommendation.dateRead = date_read
    recommendation.dateUpdated = date_updated
    recommendation.id = idx
    recommendation.isClicked = is_clicked
    recommendation.isFirst = is_first
    recommendation.mediation = mediation
    recommendation.offer = offer
    recommendation.search = search
    recommendation.shareMedium = share_medium
    recommendation.user = user

    return recommendation


def create_stock(available: int = None,
                 booking_limit_datetime: datetime = None,
                 beginning_datetime: datetime = None,
                 date_created: datetime = datetime.utcnow(),
                 date_modified: datetime = datetime.utcnow(),
                 date_modified_at_last_provider: datetime = None,
                 end_datetime: datetime = None,
                 has_been_migrated: bool = None,
                 idx: int = None,
                 id_at_providers: str = None,
                 is_soft_deleted: bool = False,
                 last_provider_id: int = None,
                 offer: Offer = None,
                 price: int = 10) -> Stock:
    stock = Stock()
    stock.available = available
    stock.beginningDatetime = beginning_datetime
    stock.bookingLimitDatetime = booking_limit_datetime
    stock.dateCreated = date_created
    stock.dateModified = date_modified
    stock.dateModifiedAtLastModified = date_modified_at_last_provider
    stock.endDatetime = end_datetime
    stock.hasBeenMigrated = has_been_migrated
    stock.id = idx
    stock.idAtProviders = id_at_providers
    stock.isSoftDeleted = is_soft_deleted
    stock.lastProviderId = last_provider_id
    stock.offer = offer
    stock.price = price

    return stock


def create_user(activity: str = None,
                can_book_free_offers: bool = True,
                civility: str = None,
                cultural_survey_id: str = None,
                cultural_survey_filled_date: datetime = None,
                date_created: datetime = datetime.utcnow(),
                date_of_birth: datetime = None,
                departement_code: str = '93',
                email: str = 'john.doe@example.com',
                first_name: str = None,
                idx: int = None,
                is_admin: bool = False,
                last_name: str = None,
                needs_to_fill_cultural_survey: bool = False,
                password: str = None,
                phone_number: str = None,
                postal_code: str = None,
                public_name: str = 'John Doe',
                reset_password_token: str = None,
                reset_password_token_validity_limit: datetime = None,
                validation_token: str = None) -> User:
    user = User()
    user.activity = activity
    user.canBookFreeOffers = can_book_free_offers
    user.civility = civility
    user.culturalSurveyId = cultural_survey_id
    user.culturalSurveyFilledDate = cultural_survey_filled_date
    user.dateCreated = date_created
    user.dateOfBirth = date_of_birth
    user.departementCode = departement_code
    user.email = email
    user.firstName = first_name
    user.id = idx
    user.isAdmin = is_admin
    user.lastName = last_name
    user.needsToFillCulturalSurvey = needs_to_fill_cultural_survey
    user.phoneNumber = phone_number
    user.publicName = public_name
    user.postalCode = postal_code
    user.validationToken = validation_token

    if password:
        user.setPassword(password)
    else:
        user.clearTextPassword = PLAIN_DEFAULT_TESTING_PASSWORD
        user.password = HASHED_DEFAULT_TESTING_PASSWORD
        user.resetPasswordToken = reset_password_token
        user.resetPasswordTokenValidityLimit = reset_password_token_validity_limit

    return user


def create_user_offerer(user: User,
                        offerer: Offerer,
                        idx: int = None,
                        is_admin: bool = False,
                        validation_token: str = None) -> UserOfferer:
    user_offerer = UserOfferer()
    user_offerer.id = idx
    user_offerer.offerer = offerer
    user_offerer.rights = RightsType.admin if is_admin else RightsType.editor
    user_offerer.user = user
    user_offerer.validationToken = validation_token

    return user_offerer


def create_venue(offerer: Offerer,
                 address: Optional[str] = '123 rue de Paris',
                 booking_email: Optional[str] = None,
                 city: Optional[str] = 'Montreuil',
                 comment: Optional[str] = None,
                 date_modified_at_last_provider: Optional[datetime] = None,
                 departement_code: Optional[str] = '93',
                 idx: Optional[int] = None,
                 id_at_providers: Optional[str] = None,
                 is_virtual: bool = False,
                 last_provider_id: Optional[int] = None,
                 latitude: Optional[float] = None,
                 longitude: Optional[float] = None,
                 name: str = 'La petite librairie',
                 postal_code: Optional[str] = '93100',
                 public_name: Optional[str] = None,
                 siret: Optional[str] = '12345678912345',
                 thumb_count: int = 0,
                 validation_token: Optional[str] = None) -> Venue:
    venue = Venue()
    venue.bookingEmail = booking_email
    venue.comment = comment
    venue.dateModifiedAtLastModified = date_modified_at_last_provider
    venue.id = idx
    venue.idAtProviders = id_at_providers
    venue.isVirtual = is_virtual
    venue.lastProviderId = last_provider_id
    venue.managingOfferer = offerer
    venue.name = name
    venue.publicName = public_name
    venue.thumbCount = thumb_count
    venue.validationToken = validation_token
    venue.siret = siret

    if not is_virtual:
        venue.address = address
        venue.city = city
        venue.departementCode = departement_code
        venue.latitude = latitude
        venue.longitude = longitude
        venue.postalCode = postal_code

    return venue


def create_venue_provider(venue: Venue,
                          provider: Provider,
                          date_modified_at_last_provider: datetime = None,
                          id_at_providers: str = None,
                          idx: int = None,
                          is_active: bool = True,
                          last_provider_id: int = None,
                          last_sync_date: datetime = None,
                          venue_id_at_offer_provider: str = '123456789',
                          sync_worker_id: str = None
                          ) -> VenueProvider:
    venue_provider = VenueProvider()
    venue_provider.dateModifiedAtLastProvider = date_modified_at_last_provider
    venue_provider.id = idx
    venue_provider.idAtProviders = id_at_providers
    venue_provider.isActive = is_active
    venue_provider.lastProviderId = last_provider_id
    venue_provider.lastSyncDate = last_sync_date
    venue_provider.provider = provider
    venue_provider.venue = venue
    venue_provider.venueIdAtOfferProvider = venue_id_at_offer_provider
    venue_provider.syncWorkerId = sync_worker_id

    return venue_provider


def create_allocine_venue_provider(venue: Provider, allocine_provider: Venue, is_duo: bool = False,
                                   available: Optional[int] = None, venue_id_at_offer_provider: str = None) -> AllocineVenueProvider:
    allocine_venue_provider = AllocineVenueProvider()
    allocine_venue_provider.venue = venue
    allocine_venue_provider.provider = allocine_provider
    allocine_venue_provider.isDuo = is_duo
    allocine_venue_provider.available = available
    allocine_venue_provider.venueIdAtOfferProvider = venue_id_at_offer_provider
    return allocine_venue_provider


def create_allocine_venue_provider_price_rule(allocine_venue_provider: AllocineVenueProvider,
                                              idx: int = None,
                                              price: int = 10,
                                              price_rule: PriceRule = PriceRule.default) -> AllocineVenueProviderPriceRule:
    venue_provider_price_rule = AllocineVenueProviderPriceRule()
    venue_provider_price_rule.id = idx
    venue_provider_price_rule.price = price
    venue_provider_price_rule.priceRule = price_rule
    venue_provider_price_rule.allocineVenueProvider = allocine_venue_provider

    return venue_provider_price_rule


def create_allocine_pivot(siret: str = '12345678912345', theater_id: str = 'XXXXXXXXXXXXXXXXXX==') -> AllocinePivot:
    allocine_pivot = AllocinePivot()
    allocine_pivot.siret = siret
    allocine_pivot.theaterId = theater_id
    return allocine_pivot


def create_payment_status(payment: Payment, detail: str = None, status: TransactionStatus = TransactionStatus.PENDING,
                          date: datetime = datetime.utcnow()) -> PaymentStatus:
    payment_status = PaymentStatus()
    payment_status.payment = payment
    payment_status.detail = detail
    payment_status.status = status
    payment_status.date = date
    return payment_status


def create_iris(polygon: Polygon, iris_code: str = '123456789') -> IrisFrance:
    iris = IrisFrance()
    iris.centroid = from_shape(create_centroid_from_polygon(polygon), srid=WGS_SPATIAL_REFERENCE_IDENTIFIER)
    iris.irisCode = iris_code
    iris.shape = from_shape(polygon, srid=WGS_SPATIAL_REFERENCE_IDENTIFIER)
    return iris


def create_iris_venue(iris: IrisFrance, venue: Venue) -> IrisVenues:
    iris_venue = IrisVenues()
    iris_venue.venue = venue
    iris_venue.iris = iris
    return iris_venue
