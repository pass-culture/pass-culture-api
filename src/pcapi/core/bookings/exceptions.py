from pcapi.domain.client_exceptions import ClientError


class OfferIsAlreadyBooked(ClientError):
    def __init__(self):
        super().__init__("offerId", "Cette offre a déja été reservée par l'utilisateur")


class QuantityIsInvalid(ClientError):
    def __init__(self, message: str):
        super().__init__("quantity", message)


class StockIsNotBookable(ClientError):
    def __init__(self):
        super().__init__("stock", "Ce stock n'est pas réservable")


class PhysicalExpenseLimitHasBeenReached(ClientError):
    def __init__(self, celling_amount):
        super().__init__(
            "global",
            f"Le plafond de {celling_amount} € pour les biens culturels ne vous permet pas " "de réserver cette offre.",
        )


class DigitalExpenseLimitHasBeenReached(ClientError):
    def __init__(self, celling_amount):
        super().__init__(
            "global",
            f"Le plafond de {celling_amount} € pour les offres numériques ne vous permet pas "
            "de réserver cette offre.",
        )


class CannotBookFreeOffers(ClientError):
    def __init__(self):
        super().__init__("cannotBookFreeOffers", "Votre compte ne vous permet pas de faire de réservation.")


class NoActivationCodeAvailable(ClientError):
    def __init__(self):
        super().__init__("noActivationCodeAvailable", "Ce stock ne contient plus de code d'activation disponible.")


class UserHasInsufficientFunds(ClientError):
    def __init__(self):
        super().__init__("insufficientFunds", "Le solde de votre pass est insuffisant pour réserver cette offre.")


class BookingIsAlreadyUsed(ClientError):
    def __init__(self):
        super().__init__("booking", "Impossible d'annuler une réservation consommée")


class CannotCancelConfirmedBooking(ClientError):
    def __init__(self, after_creation, before_event):
        super().__init__("booking", f"Impossible d'annuler une réservation {after_creation}{before_event}")


class BookingDoesntExist(ClientError):
    def __init__(self):
        super().__init__("bookingId", "bookingId ne correspond à aucune réservation")
