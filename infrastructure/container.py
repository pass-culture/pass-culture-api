from infrastructure.repository.beneficiary.beneficiary_sql_repository import BeneficiarySQLRepository
from infrastructure.repository.booking.booking_sql_repository import BookingSQLRepository
from infrastructure.repository.stock.stock_sql_repository import StockSQLRepository
from infrastructure.repository.venue.venue_label.venue_label_sql_repository import VenueLabelSQLRepository
from infrastructure.services.notification.mailjet_notification_service import MailjetNotificationService
from use_cases.book_an_offer import BookAnOffer
from use_cases.save_offerer_bank_informations import SaveOffererBankInformations
from use_cases.save_venue_bank_informations import SaveVenueBankInformations
from use_cases.get_venue_labels import GetVenueLabels

# Repositories
booking_repository = BookingSQLRepository()
user_repository = BeneficiarySQLRepository()
stock_repository = StockSQLRepository()
notification_service = MailjetNotificationService()
venue_label_repository = VenueLabelSQLRepository()

# Usecases
book_an_offer = BookAnOffer(booking_repository=booking_repository,
                            user_repository=user_repository,
                            stock_repository=stock_repository,
                            notification_service=notification_service)

get_venue_labels = GetVenueLabels(venue_label_repository=venue_label_repository)
