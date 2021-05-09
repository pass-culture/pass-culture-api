from pcapi.infrastructure.repository.beneficiary_bookings.beneficiary_bookings_sql_repository import (
    BeneficiaryBookingsSQLRepository,
)
from pcapi.infrastructure.repository.pro_offerers.paginated_offerers_sql_repository import (
    PaginatedOfferersSQLRepository,
)
from pcapi.infrastructure.repository.venue.venue_label.venue_label_sql_repository import VenueLabelSQLRepository
from pcapi.use_cases.get_bookings_for_beneficiary import GetBookingsForBeneficiary
from pcapi.use_cases.get_venue_labels import GetVenueLabels
from pcapi.use_cases.list_offerers_for_pro_user import ListOfferersForProUser


beneficiary_bookings_repository = BeneficiaryBookingsSQLRepository()
venue_label_repository = VenueLabelSQLRepository()
paginated_offerers_repository = PaginatedOfferersSQLRepository()

# Usecases
get_venue_labels = GetVenueLabels(venue_label_repository=venue_label_repository)

get_bookings_for_beneficiary = GetBookingsForBeneficiary(
    beneficiary_bookings_repository=beneficiary_bookings_repository
)

list_offerers_for_pro_user = ListOfferersForProUser(paginated_offerers_repository=paginated_offerers_repository)
