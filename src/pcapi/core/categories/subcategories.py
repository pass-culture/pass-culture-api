from dataclasses import dataclass
from enum import Enum

from pcapi.core.categories import categories


class OnlineOfflinePlatformChoices(Enum):
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"
    ONLINE_OR_OFFLINE = "ONLINE_OR_OFFLINE"


class SearchGroups(Enum):
    FILM = "Films, séries"
    CINEMA = "Cinéma"
    CONFERENCE = "Conférences, rencontres"
    JEU = "Jeux"
    LIVRE = "Livre"
    VISITE = "Visite, exposition"
    MUSIQUE = "Musique"
    COURS = "Cours, ateliers"
    PRESSE = "Presse, médias"
    SPECTACLE = "Spectacles"
    INSTRUMENT = "Instruments de musique"
    MATERIEL = "Beaux-Arts"
    NONE = None


class HomepageLabels(Enum):
    FILM = "Films"
    CINEMA = "Cinéma"
    CONFERENCE = "Rencontres"
    JEU = "Jeux"
    LIVRE = "Livre"
    VISITE = "Visites"
    MUSIQUE = "Musique"
    COURS = "Cours"
    PRESSE = "Médias"
    SPECTACLE = "Spectacle"
    INSTRUMENT = "Musique"
    MATERIEL = "Beaux-Arts"
    NONE = None


class ReimbursementRuleChoices(Enum):
    STANDARD = "STANDARD"
    NOT_REIMBURSED = "NOT_REIMBURSED"
    BOOK = "BOOK"


@dataclass(frozen=True)
class Subcategory:
    id: str
    category_id: str
    matching_type: str
    pro_label: str
    app_label: str
    search_group_name: str
    homepage_label_name: str
    is_event: bool
    conditional_fields: list[str]
    can_expire: bool
    # the booking amount will be substracted from physical cap
    is_physical_deposit: bool
    # the booking amount will be substracted from digital cap
    is_digital_deposit: bool
    online_offline_platform: str
    reimbursement_rule: str
    can_be_duo: bool
    # used by pc pro to build dropdown of subcategories during offer creation
    is_selectable: bool = True

    def __post_init__(self):
        if self.search_group_name not in [s.name for s in SearchGroups]:
            raise ValueError("search_group_name can only be one of SearchGroups")
        if self.homepage_label_name not in [h.name for h in HomepageLabels]:
            raise ValueError("search_group_name can only be one of HomepageLabels")
        if self.online_offline_platform not in [o.value for o in OnlineOfflinePlatformChoices]:
            raise ValueError("online_offline_platform can only be one of OnlineOfflinePlatformChoices")
        if self.reimbursement_rule not in [r.value for r in ReimbursementRuleChoices]:
            raise ValueError("online_offline_platform can only be one of ReimbursementRuleChoices")


# region Subcategories declarations
# region FILM
SUPPORT_PHYSIQUE_FILM = Subcategory(
    id="SUPPORT_PHYSIQUE_FILM",
    category_id=categories.FILM.id,
    matching_type="ThingType.AUDIOVISUEL",
    pro_label="Support physique (DVD, Blu-ray...)",
    app_label="Support physique (DVD, Blu-ray...)",
    search_group_name=SearchGroups.FILM.name,
    homepage_label_name=HomepageLabels.FILM.name,
    is_event=False,
    conditional_fields=[],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
ABO_MEDIATHEQUE = Subcategory(
    id="ABO_MEDIATHEQUE",
    category_id=categories.FILM.id,
    matching_type="ThingType.AUDIOVISUEL",
    pro_label="Abonnement médiathèque",
    app_label="Abonnement médiathèque",
    search_group_name=SearchGroups.FILM.name,
    homepage_label_name=HomepageLabels.FILM.name,
    is_event=False,
    conditional_fields=[],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
VOD = Subcategory(
    id="VOD",
    category_id=categories.FILM.id,
    matching_type="ThingType.AUDIOVISUEL",
    pro_label="Vidéo à la demande",
    app_label="Vidéo à la demande",
    search_group_name=SearchGroups.FILM.name,
    homepage_label_name=HomepageLabels.FILM.name,
    is_event=False,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
)
ABO_PLATEFORME_VIDEO = Subcategory(
    id="ABO_PLATEFORME_VIDEO",
    category_id=categories.FILM.id,
    matching_type="ThingType.AUDIOVISUEL",
    pro_label="Abonnement plateforme streaming",
    app_label="Abonnement plateforme streaming",
    search_group_name=SearchGroups.FILM.name,
    homepage_label_name=HomepageLabels.FILM.name,
    is_event=False,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
)
AUTRE_SUPPORT_NUMERIQUE = Subcategory(
    id="AUTRE_SUPPORT_NUMERIQUE",
    category_id=categories.FILM.id,
    matching_type="ThingType.AUDIOVISUEL",
    pro_label="Autre support numérique",
    app_label="Autre support numérique",
    search_group_name=SearchGroups.FILM.name,
    homepage_label_name=HomepageLabels.FILM.name,
    is_event=False,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
)
# endregion
# region CINEMA
CARTE_CINE_MULTISEANCES = Subcategory(
    id="CARTE_CINE_MULTISEANCES",
    category_id=categories.CINEMA.id,
    matching_type="ThingType.CINEMA_ABO",
    pro_label="Carte cinéma multi-séances",
    app_label="Carte cinéma multi-séances",
    search_group_name=SearchGroups.CINEMA.name,
    homepage_label_name=HomepageLabels.CINEMA.name,
    is_event=False,
    conditional_fields=[],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
CARTE_CINE_ILLIMITE = Subcategory(
    id="CARTE_CINE_ILLIMITE",
    category_id=categories.CINEMA.id,
    matching_type="ThingType.CINEMA_ABO",
    pro_label="Carte cinéma illimité",
    app_label="Carte cinéma illimité",
    search_group_name=SearchGroups.CINEMA.name,
    homepage_label_name=HomepageLabels.CINEMA.name,
    is_event=False,
    conditional_fields=[],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
SEANCE_CINE = Subcategory(
    id="SEANCE_CINE",
    category_id=categories.CINEMA.id,
    matching_type="EventType.CINEMA",
    pro_label="Séance de cinéma",
    app_label="Séance de cinéma",
    search_group_name=SearchGroups.CINEMA.name,
    homepage_label_name=HomepageLabels.CINEMA.name,
    is_event=True,
    conditional_fields=["author", "visa", "stageDirector"],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
EVENEMENT_CINE = Subcategory(
    id="EVENEMENT_CINE",
    category_id=categories.CINEMA.id,
    matching_type="EventType.CINEMA",
    pro_label="Événement cinématographique",
    app_label="Événement cinéma",
    search_group_name=SearchGroups.CINEMA.name,
    homepage_label_name=HomepageLabels.CINEMA.name,
    is_event=True,
    conditional_fields=["author", "visa", "stageDirector"],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
FESTIVAL_CINE = Subcategory(
    id="FESTIVAL_CINE",
    category_id=categories.CINEMA.id,
    matching_type="EventType.CINEMA",
    pro_label="Festival de cinéma",
    app_label="Festival de cinéma",
    search_group_name=SearchGroups.CINEMA.name,
    homepage_label_name=HomepageLabels.CINEMA.name,
    is_event=True,
    conditional_fields=["author", "visa", "stageDirector"],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
CINE_VENTE_DISTANCE = Subcategory(
    id="CINE_VENTE_DISTANCE",
    category_id=categories.CINEMA.id,
    matching_type="ThingType.CINEMA_CARD",
    pro_label="Cinéma vente à distance",
    app_label="Cinéma",
    search_group_name=SearchGroups.CINEMA.name,
    homepage_label_name=HomepageLabels.CINEMA.name,
    is_event=False,
    conditional_fields=["author", "visa", "stageDirector"],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)

CINE_PLEIN_AIR = Subcategory(
    id="CINE_PLEIN_AIR",
    category_id=categories.CINEMA.id,
    matching_type="EventType.CINEMA",
    pro_label="Cinéma plein air",
    app_label="Cinéma plein air",
    search_group_name=SearchGroups.CINEMA.name,
    homepage_label_name=HomepageLabels.CINEMA.name,
    is_event=True,
    conditional_fields=["author", "visa", "stageDirector"],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)

# endregion
# region CONFERENCE

CONFERENCE = Subcategory(
    id="CONFERENCE",
    category_id=categories.CONFERENCE_RENCONTRE.id,
    matching_type="EventType.CONFERENCE_DEBAT_DEDICACE",
    pro_label="Conférence",
    app_label="Conférence",
    search_group_name=SearchGroups.CONFERENCE.name,
    homepage_label_name=HomepageLabels.CONFERENCE.name,
    is_event=True,
    conditional_fields=["speaker"],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
RENCONTRE = Subcategory(
    id="RENCONTRE",
    category_id=categories.CONFERENCE_RENCONTRE.id,
    matching_type="EventType.CONFERENCE_DEBAT_DEDICACE",
    pro_label="Rencontre",
    app_label="Rencontre",
    search_group_name=SearchGroups.CONFERENCE.name,
    homepage_label_name=HomepageLabels.CONFERENCE.name,
    is_event=True,
    conditional_fields=["speaker"],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
DECOUVERTE_METIERS = Subcategory(
    id="DECOUVERTE_METIERS",
    category_id=categories.CONFERENCE_RENCONTRE.id,
    matching_type="EventType.CONFERENCE_DEBAT_DEDICACE",
    pro_label="Découverte des métiers",
    app_label="Découverte des métiers",
    search_group_name=SearchGroups.CONFERENCE.name,
    homepage_label_name=HomepageLabels.CONFERENCE.name,
    is_event=True,
    conditional_fields=["speaker"],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
    is_selectable=False,
)
SALON = Subcategory(
    id="SALON",
    category_id=categories.CONFERENCE_RENCONTRE.id,
    matching_type="EventType.CONFERENCE_DEBAT_DEDICACE",
    pro_label="Salon, Convention",
    app_label="Salon, Convention",
    search_group_name=SearchGroups.CONFERENCE.name,
    homepage_label_name=HomepageLabels.CONFERENCE.name,
    is_event=True,
    conditional_fields=["speaker"],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
# endregion
# region JEU
CONCOURS = Subcategory(
    id="CONCOURS",
    category_id=categories.JEU.id,
    matching_type="EventType.JEUX",
    pro_label="Concours - jeux",
    app_label="Concours - jeux",
    search_group_name=SearchGroups.JEU.name,
    homepage_label_name=HomepageLabels.JEU.name,
    is_event=True,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
RENCONTRE_JEU = Subcategory(
    id="RENCONTRE_JEU",
    category_id=categories.JEU.id,
    matching_type="EventType.JEUX",
    pro_label="Rencontres - jeux",
    app_label="Rencontres - jeux",
    search_group_name=SearchGroups.JEU.name,
    homepage_label_name=HomepageLabels.JEU.name,
    is_event=True,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
ESCAPE_GAME = Subcategory(
    id="ESCAPE_GAME",
    category_id=categories.JEU.id,
    matching_type="ThingType.JEUX",
    pro_label="Escape game",
    app_label="Escape game",
    search_group_name=SearchGroups.JEU.name,
    homepage_label_name=HomepageLabels.JEU.name,
    is_event=False,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
EVENEMENT_JEU = Subcategory(
    id="EVENEMENT_JEU",
    category_id=categories.JEU.id,
    matching_type="EventType.JEUX",
    pro_label="Événements - jeux",
    app_label="Événements - jeux",
    search_group_name=SearchGroups.JEU.name,
    homepage_label_name=HomepageLabels.JEU.name,
    is_event=True,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
JEU_EN_LIGNE = Subcategory(
    id="JEU_EN_LIGNE",
    category_id=categories.JEU.id,
    matching_type="ThingType.JEUX_VIDEO",
    pro_label="Jeux en ligne",
    app_label="Jeux en ligne",
    search_group_name=SearchGroups.JEU.name,
    homepage_label_name=HomepageLabels.JEU.name,
    is_event=False,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
)
ABO_JEU_VIDEO = Subcategory(
    id="ABO_JEU_VIDEO",
    category_id=categories.JEU.id,
    matching_type="ThingType.JEUX_VIDEO_ABO",
    pro_label="Abonnement jeux vidéos",
    app_label="Abonnement jeux vidéos",
    search_group_name=SearchGroups.JEU.name,
    homepage_label_name=HomepageLabels.JEU.name,
    is_event=False,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
)
ABO_LUDOTHEQUE = Subcategory(
    id="ABO_LUDOTHEQUE",
    category_id=categories.JEU.id,
    matching_type="ThingType.JEUX_VIDEO_ABO",
    pro_label="Abonnement ludothèque",
    app_label="Abonnement ludothèque",
    search_group_name=SearchGroups.JEU.name,
    homepage_label_name=HomepageLabels.JEU.name,
    is_event=False,
    conditional_fields=[],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
    is_selectable=False,
)
# endregion
# region LIVRE

LIVRE_PAPIER = Subcategory(
    id="LIVRE_PAPIER",
    category_id=categories.LIVRE.id,
    matching_type="ThingType.LIVRE_EDITION",
    pro_label="Livre papier",
    app_label="Livre",
    search_group_name=SearchGroups.LIVRE.name,
    homepage_label_name=HomepageLabels.LIVRE.name,
    is_event=False,
    conditional_fields=["author", "isbn"],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.BOOK.value,
)
LIVRE_NUMERIQUE = Subcategory(
    id="LIVRE_NUMERIQUE",
    category_id=categories.LIVRE.id,
    matching_type="ThingType.LIVRE_AUDIO",
    pro_label="Livre numérique, e-book",
    app_label="Livre numérique, e-book",
    search_group_name=SearchGroups.LIVRE.name,
    homepage_label_name=HomepageLabels.LIVRE.name,
    is_event=False,
    conditional_fields=["author", "isbn"],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.BOOK.value,
)
TELECHARGEMENT_LIVRE_AUDIO = Subcategory(
    id="TELECHARGEMENT_LIVRE_AUDIO",
    category_id=categories.LIVRE.id,
    matching_type="ThingType.LIVRE_AUDIO",
    pro_label="Livre audio à télécharger",
    app_label="Livre audio à télécharger",
    search_group_name=SearchGroups.LIVRE.name,
    homepage_label_name=HomepageLabels.LIVRE.name,
    is_event=False,
    conditional_fields=["author"],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
)
LIVRE_AUDIO_PHYSIQUE = Subcategory(
    id="LIVRE_AUDIO_PHYSIQUE",
    category_id=categories.LIVRE.id,
    matching_type="ThingType.LIVRE_AUDIO",
    pro_label="Livre audio sur support physique",
    app_label="Livre audio sur support physique",
    search_group_name=SearchGroups.LIVRE.name,
    homepage_label_name=HomepageLabels.LIVRE.name,
    is_event=False,
    conditional_fields=["author", "isbn"],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
ABO_BIBLIOTHEQUE = Subcategory(
    id="ABO_BIBLIOTHEQUE",
    category_id=categories.LIVRE.id,
    matching_type="ThingType.LIVRE_AUDIO",
    pro_label="Abonnement (bibliothèques, médiathèques...)",
    app_label="Abonnement (bibliothèques, médiathèques...)",
    search_group_name=SearchGroups.LIVRE.name,
    homepage_label_name=HomepageLabels.LIVRE.name,
    is_event=False,
    conditional_fields=[],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
ABO_LIVRE_NUMERIQUE = Subcategory(
    id="ABO_LIVRE_NUMERIQUE",
    category_id=categories.LIVRE.id,
    matching_type="ThingType.LIVRE_AUDIO",
    pro_label="Abonnement livres numériques",
    app_label="Abonnement livres numériques",
    search_group_name=SearchGroups.LIVRE.name,
    homepage_label_name=HomepageLabels.LIVRE.name,
    is_event=False,
    conditional_fields=[],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.BOOK.value,
)
FESTIVAL_LIVRE = Subcategory(
    id="FESTIVAL_LIVRE",
    category_id=categories.LIVRE.id,
    matching_type="ThingType.LIVRE_AUDIO",
    pro_label="Festival et salon du livre",
    app_label="Festival et salon du livre",
    search_group_name=SearchGroups.LIVRE.name,
    homepage_label_name=HomepageLabels.LIVRE.name,
    is_event=True,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
# endregion
# region VISITE

CARTE_MUSEE = Subcategory(
    id="CARTE_MUSEE",
    category_id=categories.MUSEE.id,
    matching_type="ThingType.MUSEES_PATRIMOINE_ABO",
    pro_label="Cartes musées, patrimoine, architecture, arts visuels",
    app_label="Cartes musées, patrimoine...",
    search_group_name=SearchGroups.VISITE.name,
    homepage_label_name=HomepageLabels.VISITE.name,
    is_event=False,
    conditional_fields=[],
    can_expire=True,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
ABO_MUSEE = Subcategory(
    id="ABO_MUSEE",
    category_id=categories.MUSEE.id,
    matching_type="ThingType.MUSEES_PATRIMOINE_ABO",
    pro_label="Entrée libre ou abonnement musée, patrimoine…",
    app_label="Entrée libre ou abonnement musée",
    search_group_name=SearchGroups.VISITE.name,
    homepage_label_name=HomepageLabels.VISITE.name,
    is_event=False,
    conditional_fields=[],
    can_expire=True,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
VISITE = Subcategory(
    id="VISITE",
    category_id=categories.MUSEE.id,
    matching_type="EventType.MUSEES_PATRIMOINE",
    pro_label="Visite",
    app_label="Visite",
    search_group_name=SearchGroups.VISITE.name,
    homepage_label_name=HomepageLabels.VISITE.name,
    is_event=True,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
VISITE_GUIDEE = Subcategory(
    id="VISITE_GUIDEE",
    category_id=categories.MUSEE.id,
    matching_type="EventType.MUSEES_PATRIMOINE",
    pro_label="Visite guidée",
    app_label="Visite guidée",
    search_group_name=SearchGroups.VISITE.name,
    homepage_label_name=HomepageLabels.VISITE.name,
    is_event=True,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
EVENEMENT_PATRIMOINE = Subcategory(
    id="EVENEMENT_PATRIMOINE",
    category_id=categories.MUSEE.id,
    matching_type="EventType.MUSEES_PATRIMOINE",
    pro_label="Événement et atelier patrimoine",
    app_label="Événement et atelier patrimoine",
    search_group_name=SearchGroups.VISITE.name,
    homepage_label_name=HomepageLabels.VISITE.name,
    is_event=True,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
VISITE_VIRTUELLE = Subcategory(
    id="VISITE_VIRTUELLE",
    category_id=categories.MUSEE.id,
    matching_type="EventType.MUSEES_PATRIMOINE",
    pro_label="Visite virtuelle",
    app_label="Visite virtuelle",
    search_group_name=SearchGroups.VISITE.name,
    homepage_label_name=HomepageLabels.VISITE.name,
    is_event=False,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
)
MUSEE_VENTE_DISTANCE = Subcategory(
    id="MUSEE_VENTE_DISTANCE",
    category_id=categories.MUSEE.id,
    matching_type="ThingType.MUSEES_PATRIMOINE_ABO",
    pro_label="Musée vente à distance",
    app_label="Musée vente à distance",
    search_group_name=SearchGroups.VISITE.name,
    homepage_label_name=HomepageLabels.VISITE.name,
    is_event=False,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
# endregion
# region MUSIQUE_LIVE

CONCERT = Subcategory(
    id="CONCERT",
    category_id=categories.MUSIQUE_LIVE.id,
    matching_type="EventType.MUSIQUE",
    pro_label="Concert",
    app_label="Concert",
    search_group_name=SearchGroups.MUSIQUE.name,
    homepage_label_name=HomepageLabels.MUSIQUE.name,
    is_event=True,
    conditional_fields=["author", "musicType", "performer"],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
EVENEMENT_MUSIQUE = Subcategory(
    id="EVENEMENT_MUSIQUE",
    category_id=categories.MUSIQUE_LIVE.id,
    matching_type="EventType.MUSIQUE",
    pro_label="Autre type d'événement musical",
    app_label="Autre type d'événement musical",
    search_group_name=SearchGroups.MUSIQUE.name,
    homepage_label_name=HomepageLabels.MUSIQUE.name,
    is_event=True,
    conditional_fields=["author", "musicType", "performer"],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
LIVESTREAM_MUSIQUE = Subcategory(
    id="LIVESTREAM_MUSIQUE",
    category_id=categories.MUSIQUE_LIVE.id,
    matching_type="EventType.MUSIQUE",
    pro_label="Live stream musical",
    app_label="Live stream musical",
    search_group_name=SearchGroups.MUSIQUE.name,
    homepage_label_name=HomepageLabels.MUSIQUE.name,
    is_event=True,
    conditional_fields=["author", "musicType", "performer"],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
ABO_CONCERT = Subcategory(
    id="ABO_CONCERT",
    category_id=categories.MUSIQUE_LIVE.id,
    matching_type="ThingType.MUSIQUE_ABO",
    pro_label="Abonnement concert",
    app_label="Abonnement concert",
    search_group_name=SearchGroups.MUSIQUE.name,
    homepage_label_name=HomepageLabels.MUSIQUE.name,
    is_event=False,
    conditional_fields=["musicType"],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
FESTIVAL_MUSIQUE = Subcategory(
    id="FESTIVAL_MUSIQUE",
    category_id=categories.MUSIQUE_LIVE.id,
    matching_type="EventType.MUSIQUE",
    pro_label="Festival de musique",
    app_label="Festival de musique",
    search_group_name=SearchGroups.MUSIQUE.name,
    homepage_label_name=HomepageLabels.MUSIQUE.name,
    is_event=True,
    conditional_fields=["author", "musicType", "performer"],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
# endregion
# region MUSIQUE_ENREGISTREE
SUPPORT_PHYSIQUE_MUSIQUE = Subcategory(
    id="SUPPORT_PHYSIQUE_MUSIQUE",
    category_id=categories.MUSIQUE_ENREGISTREE.id,
    matching_type="ThingType.MUSIQUE",
    pro_label="Support physique (CD, vinyle...)",
    app_label="Support physique (CD, vinyle...)",
    search_group_name=SearchGroups.MUSIQUE.name,
    homepage_label_name=HomepageLabels.MUSIQUE.name,
    is_event=False,
    conditional_fields=["author", "musicType", "performer"],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
TELECHARGEMENT_MUSIQUE = Subcategory(
    id="TELECHARGEMENT_MUSIQUE",
    category_id=categories.MUSIQUE_ENREGISTREE.id,
    matching_type="ThingType.MUSIQUE",
    pro_label="Téléchargement de musique",
    app_label="Téléchargement de musique",
    search_group_name=SearchGroups.MUSIQUE.name,
    homepage_label_name=HomepageLabels.MUSIQUE.name,
    is_event=False,
    conditional_fields=["author", "musicType", "performer"],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
)
ABO_PLATEFORME_MUSIQUE = Subcategory(
    id="ABO_PLATEFORME_MUSIQUE",
    category_id=categories.MUSIQUE_ENREGISTREE.id,
    matching_type="ThingType.MUSIQUE_ABO",
    pro_label="Abonnement plateforme musicale",
    app_label="Abonnement plateforme musicale",
    search_group_name=SearchGroups.MUSIQUE.name,
    homepage_label_name=HomepageLabels.MUSIQUE.name,
    is_event=False,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
)
CAPTATION_MUSIQUE = Subcategory(
    id="CAPTATION_MUSIQUE",
    category_id=categories.MUSIQUE_ENREGISTREE.id,
    matching_type="ThingType.MUSIQUE",
    pro_label="Captation musicale",
    app_label="Captation musicale",
    search_group_name=SearchGroups.MUSIQUE.name,
    homepage_label_name=HomepageLabels.MUSIQUE.name,
    is_event=False,
    conditional_fields=["author", "musicType", "performer"],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
)

# endregion
# region PRATIQUE
SEANCE_ESSAI_PRATIQUE_ART = Subcategory(
    id="SEANCE_ESSAI_PRATIQUE_ART",
    category_id=categories.PRATIQUE_ART.id,
    matching_type="EventType.PRATIQUE_ARTISTIQUE",
    pro_label="Séance d'essai",
    app_label="Séance d'essai",
    search_group_name=SearchGroups.COURS.name,
    homepage_label_name=HomepageLabels.COURS.name,
    is_event=True,
    conditional_fields=["speaker"],
    can_expire=True,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
ATELIER_PRATIQUE_ART = Subcategory(
    id="ATELIER_PRATIQUE_ART",
    category_id=categories.PRATIQUE_ART.id,
    matching_type="EventType.PRATIQUE_ARTISTIQUE",
    pro_label="Atelier, stage de pratique artistique",
    app_label="Atelier, stage de pratique artistique",
    search_group_name=SearchGroups.COURS.name,
    homepage_label_name=HomepageLabels.COURS.name,
    is_event=True,
    conditional_fields=["speaker"],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
ABO_PRATIQUE_ART = Subcategory(
    id="ABO_PRATIQUE_ART",
    category_id=categories.PRATIQUE_ART.id,
    matching_type="ThingType.PRATIQUE_ARTISTIQUE_ABO",
    pro_label="Abonnement pratique artistique",
    app_label="Abonnement pratique artistique",
    search_group_name=SearchGroups.COURS.name,
    homepage_label_name=HomepageLabels.COURS.name,
    is_event=False,
    conditional_fields=[],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
# endregion
# region MEDIAS
ABO_PRESSE_EN_LIGNE = Subcategory(
    id="ABO_PRESSE_EN_LIGNE",
    category_id=categories.MEDIA.id,
    matching_type="ThingType.PRESSE_ABO",
    pro_label="Abonnement presse en ligne",
    app_label="Abonnement presse en ligne",
    search_group_name=SearchGroups.PRESSE.name,
    homepage_label_name=HomepageLabels.PRESSE.name,
    is_event=False,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
)
PODCAST = Subcategory(
    id="PODCAST",
    category_id=categories.MEDIA.id,
    matching_type="ThingType.PRESSE_ABO",
    pro_label="Podcast",
    app_label="Podcast",
    search_group_name=SearchGroups.PRESSE.name,
    homepage_label_name=HomepageLabels.PRESSE.name,
    is_event=False,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
)
APP_CULTURELLE = Subcategory(
    id="APP_CULTURELLE",
    category_id=categories.MEDIA.id,
    matching_type="ThingType.PRESSE_ABO",
    pro_label="Application culturelle",
    app_label="Application culturelle",
    search_group_name=SearchGroups.PRESSE.name,
    homepage_label_name=HomepageLabels.PRESSE.name,
    is_event=False,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
)
# endregion
# region SPECTACLE
SPECTACLE_REPRESENTATION = Subcategory(
    id="SPECTACLE_REPRESENTATION",
    category_id=categories.SPECTACLE.id,
    matching_type="EventType.SPECTACLE_VIVANT",
    pro_label="Spectacle, représentation",
    app_label="Spectacle, représentation",
    search_group_name=SearchGroups.SPECTACLE.name,
    homepage_label_name=HomepageLabels.SPECTACLE.name,
    is_event=True,
    conditional_fields=["author", "showType", "stageDirector", "performer"],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
SPECTACLE_ENREGISTRE = Subcategory(
    id="SPECTACLE_ENREGISTRE",
    category_id=categories.SPECTACLE.id,
    matching_type="EventType.SPECTACLE_VIVANT",
    pro_label="Spectacle enregistré",
    app_label="Spectacle enregistré",
    search_group_name=SearchGroups.SPECTACLE.name,
    homepage_label_name=HomepageLabels.SPECTACLE.name,
    is_event=False,
    conditional_fields=["author", "showType", "stageDirector", "performer"],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
)
LIVESTREAM_EVENEMENT = Subcategory(
    id="LIVESTREAM_EVENEMENT",
    category_id=categories.SPECTACLE.id,
    matching_type="EventType.SPECTACLE_VIVANT",
    pro_label="Live stream d'événement",
    app_label="Live stream d'événement",
    search_group_name=SearchGroups.SPECTACLE.name,
    homepage_label_name=HomepageLabels.SPECTACLE.name,
    is_event=True,
    conditional_fields=["author", "showType", "stageDirector", "performer"],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE.value,
    is_digital_deposit=True,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
FESTIVAL_SPECTACLE = Subcategory(
    id="FESTIVAL_SPECTACLE",
    category_id=categories.SPECTACLE.id,
    matching_type="EventType.SPECTACLE_VIVANT",
    pro_label="Festival",
    app_label="Festival",
    search_group_name=SearchGroups.SPECTACLE.name,
    homepage_label_name=HomepageLabels.SPECTACLE.name,
    is_event=True,
    conditional_fields=["author", "showType", "stageDirector", "performer"],
    can_expire=False,
    can_be_duo=True,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
ABO_SPECTACLE = Subcategory(
    id="ABO_SPECTACLE",
    category_id=categories.SPECTACLE.id,
    matching_type="ThingType.SPECTACLE_VIVANT_ABO",
    pro_label="Abonnement spectacle",
    app_label="Abonnement spectacle",
    search_group_name=SearchGroups.SPECTACLE.name,
    homepage_label_name=HomepageLabels.SPECTACLE.name,
    is_event=False,
    conditional_fields=["showType"],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
# endregion
# region INSTRUMENT
ACHAT_INSTRUMENT = Subcategory(
    id="ACHAT_INSTRUMENT",
    category_id=categories.INSTRUMENT.id,
    matching_type="ThingType.INSTRUMENT",
    pro_label="Achat instrument",
    app_label="Achat instrument",
    search_group_name=SearchGroups.INSTRUMENT.name,
    homepage_label_name=HomepageLabels.INSTRUMENT.name,
    is_event=False,
    conditional_fields=[],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
BON_ACHAT_INSTRUMENT = Subcategory(
    id="BON_ACHAT_INSTRUMENT",
    category_id=categories.INSTRUMENT.id,
    matching_type="ThingType.INSTRUMENT",
    pro_label="Bon d'achat instrument",
    app_label="Bon d'achat instrument",
    search_group_name=SearchGroups.INSTRUMENT.name,
    homepage_label_name=HomepageLabels.INSTRUMENT.name,
    is_event=False,
    conditional_fields=[],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
LOCATION_INSTRUMENT = Subcategory(
    id="LOCATION_INSTRUMENT",
    category_id=categories.INSTRUMENT.id,
    matching_type="ThingType.INSTRUMENT",
    pro_label="Location instrument",
    app_label="Location instrument",
    search_group_name=SearchGroups.INSTRUMENT.name,
    homepage_label_name=HomepageLabels.INSTRUMENT.name,
    is_event=False,
    conditional_fields=[],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
PARTITION = Subcategory(
    id="PARTITION",
    category_id=categories.INSTRUMENT.id,
    matching_type="ThingType.INSTRUMENT",
    pro_label="Partition",
    app_label="Partition",
    search_group_name=SearchGroups.INSTRUMENT.name,
    homepage_label_name=HomepageLabels.INSTRUMENT.name,
    is_event=False,
    conditional_fields=[],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
# endregion
# region BEAUX_ARTS
MATERIEL_ART_CREATIF = Subcategory(
    id="MATERIEL_ART_CREATIF",
    category_id=categories.BEAUX_ARTS.id,
    matching_type="ThingType.MATERIEL_ART_CREA",
    pro_label="Matériel arts créatifs",
    app_label="Matériel arts créatifs",
    search_group_name=SearchGroups.MATERIEL.name,
    homepage_label_name=HomepageLabels.MATERIEL.name,
    is_event=False,
    conditional_fields=[],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.STANDARD.value,
)
# endregion
# region TECHNICAL
ACTIVATION_EVENT = Subcategory(
    id="ACTIVATION_EVENT",
    category_id=categories.TECHNIQUE.id,
    matching_type="EventType.ACTIVATION",
    pro_label="Catégorie technique d'événement d'activation ",
    app_label="Catégorie technique d'événement d'activation ",
    search_group_name=SearchGroups.NONE.name,
    homepage_label_name=HomepageLabels.NONE.name,
    is_event=True,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE_OR_OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=False,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
    is_selectable=False,
)
ACTIVATION_THING = Subcategory(
    id="ACTIVATION_THING",
    category_id=categories.TECHNIQUE.id,
    matching_type="ThingType.ACTIVATION",
    pro_label="Catégorie technique de thing d'activation",
    app_label="Catégorie technique de thing d'activation",
    search_group_name=SearchGroups.NONE.name,
    homepage_label_name=HomepageLabels.NONE.name,
    is_event=False,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE_OR_OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
    is_selectable=False,
)
JEU_SUPPORT_PHYSIQUE = Subcategory(
    id="JEU_SUPPORT_PHYSIQUE",
    category_id=categories.TECHNIQUE.id,
    matching_type="ThingType.JEUX",
    pro_label="Catégorie technique Jeu support physique",
    app_label="Catégorie technique Jeu support physique",
    search_group_name=SearchGroups.NONE.name,
    homepage_label_name=HomepageLabels.NONE.name,
    is_event=False,
    conditional_fields=[],
    can_expire=False,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE_OR_OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
    is_selectable=False,
)
OEUVRE_ART = Subcategory(
    id="OEUVRE_ART",
    category_id=categories.TECHNIQUE.id,
    matching_type="ThingType.OEUVRE_ART",
    pro_label="Catégorie technique d'oeuvre d'art",
    app_label="Catégorie technique d'oeuvre d'art",
    search_group_name=SearchGroups.NONE.name,
    homepage_label_name=HomepageLabels.NONE.name,
    is_event=False,
    conditional_fields=[],
    can_expire=True,
    can_be_duo=False,
    online_offline_platform=OnlineOfflinePlatformChoices.ONLINE_OR_OFFLINE.value,
    is_digital_deposit=False,
    is_physical_deposit=True,
    reimbursement_rule=ReimbursementRuleChoices.NOT_REIMBURSED.value,
    is_selectable=False,
)
# endregion
# endregion

ALL_SUBCATEGORIES = (
    ABO_BIBLIOTHEQUE,
    ABO_CONCERT,
    ABO_JEU_VIDEO,
    ABO_LIVRE_NUMERIQUE,
    ABO_LUDOTHEQUE,
    ABO_MEDIATHEQUE,
    ABO_MUSEE,
    ABO_PLATEFORME_MUSIQUE,
    ABO_PLATEFORME_VIDEO,
    ABO_PRATIQUE_ART,
    ABO_PRESSE_EN_LIGNE,
    ABO_SPECTACLE,
    ACHAT_INSTRUMENT,
    ACTIVATION_EVENT,
    ACTIVATION_THING,
    APP_CULTURELLE,
    ATELIER_PRATIQUE_ART,
    AUTRE_SUPPORT_NUMERIQUE,
    BON_ACHAT_INSTRUMENT,
    CAPTATION_MUSIQUE,
    CARTE_CINE_ILLIMITE,
    CARTE_CINE_MULTISEANCES,
    CARTE_MUSEE,
    CINE_PLEIN_AIR,
    CINE_VENTE_DISTANCE,
    CONCERT,
    CONCOURS,
    CONFERENCE,
    DECOUVERTE_METIERS,
    ESCAPE_GAME,
    EVENEMENT_CINE,
    EVENEMENT_JEU,
    EVENEMENT_MUSIQUE,
    EVENEMENT_PATRIMOINE,
    FESTIVAL_CINE,
    FESTIVAL_LIVRE,
    FESTIVAL_MUSIQUE,
    FESTIVAL_SPECTACLE,
    JEU_EN_LIGNE,
    JEU_SUPPORT_PHYSIQUE,
    LIVESTREAM_EVENEMENT,
    LIVESTREAM_MUSIQUE,
    LIVRE_AUDIO_PHYSIQUE,
    LIVRE_NUMERIQUE,
    LIVRE_PAPIER,
    LOCATION_INSTRUMENT,
    MATERIEL_ART_CREATIF,
    MUSEE_VENTE_DISTANCE,
    OEUVRE_ART,
    PARTITION,
    PODCAST,
    RENCONTRE_JEU,
    RENCONTRE,
    SALON,
    SEANCE_CINE,
    SEANCE_ESSAI_PRATIQUE_ART,
    SPECTACLE_ENREGISTRE,
    SPECTACLE_REPRESENTATION,
    SUPPORT_PHYSIQUE_FILM,
    SUPPORT_PHYSIQUE_MUSIQUE,
    TELECHARGEMENT_LIVRE_AUDIO,
    TELECHARGEMENT_MUSIQUE,
    VISITE_GUIDEE,
    VISITE_VIRTUELLE,
    VISITE,
    VOD,
)
ALL_SUBCATEGORIES_DICT = {subcategory.id: subcategory for subcategory in ALL_SUBCATEGORIES}

assert set(subcategory.id for subcategory in ALL_SUBCATEGORIES) == set(
    subcategory.id for subcategory in locals().values() if isinstance(subcategory, Subcategory)
)

SubcategoryIdEnum = Enum("SubcategoryIdEnum", {subcategory.id: subcategory.id for subcategory in ALL_SUBCATEGORIES})
SearchGroupNameEnum = Enum(
    "SearchGroupNameEnum",
    {search_group_name: search_group_name for search_group_name in [c.name for c in SearchGroups]},
)
HomepageLabelEnum = Enum(
    "(HomepageLabelEnum",
    {homepage_label_name: homepage_label_name for homepage_label_name in [h.name for h in HomepageLabels]},
)
OnlineOfflinePlatformChoicesEnum = Enum(
    "OnlineOfflinePlatformChoicesEnum",
    {choice: choice for choice in [c.value for c in OnlineOfflinePlatformChoices]},
)


def get_search_group_label(search_group_name):
    return SearchGroups[search_group_name].value
