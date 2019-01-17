import string
from functools import partial

import pandas as pd
import unidecode

from models import Venue, Offer, PcObject, Offerer, UserOfferer
from models.db import db
from scripts.v14_clean_duplicate_offerers.connectors_google_spreadsheet import get_offerer_equivalence, \
    get_venue_equivalence


def get_venues_by_offerer_equivalences():
    offerers_KO_df = get_offerer_equivalence()
    return _get_venue_equivalence_df_for_KO_offerers(offerers_KO_df)


def save_venues_by_offerer_equivalences(file_name):
    venues_df = get_venues_by_offerer_equivalences()
    venues_df.to_csv(file_name, index=False)


def correcting_KO_venues_and_offers(venue_equivalence_df):
    venue_KO_has_matching_in_venue_OK = venue_equivalence_df.venue_OK_id.notnull()
    correct_venue_id(venue_equivalence_df[venue_KO_has_matching_in_venue_OK])
    correct_mananging_offerer_id(venue_equivalence_df[~venue_KO_has_matching_in_venue_OK])


def correct_mananging_offerer_id(df):
    for index, venue_equivalence_row in df.iterrows():
        venue_to_edit = Venue.query.filter_by(id=venue_equivalence_row.venue_KO_id).first()
        venue_to_edit.managingOffererId = int(venue_equivalence_row.offerer_OK_id)
        if not venue_to_edit.managingOfferer.siren:
            venue_to_edit.managingOfferer.siren = str(100000000 + index)
        PcObject.check_and_save(venue_to_edit)


def correct_venue_id(df_with_venue_equivalences):
    for index, venue_equivalence_row in df_with_venue_equivalences.iterrows():
        offers_to_edit = Offer.query.filter_by(venueId=venue_equivalence_row.venue_KO_id).all()
        edited_offers = list(
            map(partial(_change_offer_venue_id, new_id=venue_equivalence_row.venue_OK_id), offers_to_edit))
        if edited_offers:
            PcObject.check_and_save(*edited_offers)


def delete_offerers_KO(df_with_offerer_equivalence):
    offerers_to_delete_id = set(df_with_offerer_equivalence.offerer_KO_id)
    Offerer.query.filter(Offerer.id.in_(offerers_to_delete_id)).delete(synchronize_session="fetch")
    db.session.commit()


def delete_venues_linked_to_offerers_KO(df_with_offerer_equivalence):
    offerers_to_delete_id = set(df_with_offerer_equivalence.offerer_KO_id)
    Venue.query.filter(Venue.managingOffererId.in_(offerers_to_delete_id)).delete(synchronize_session="fetch")
    db.session.commit()


def delete_user_offerers_linked_to_offerers_KO(df_with_offerer_equivalence):
    offerers_to_delete_id = set(df_with_offerer_equivalence.offerer_KO_id)
    UserOfferer.query.filter(UserOfferer.offererId.in_(offerers_to_delete_id)).delete(synchronize_session="fetch")
    db.session.commit()


def clean_offerers_KO():
    df_with_venue_equivalences = get_venue_equivalence()
    correcting_KO_venues_and_offers(df_with_venue_equivalences)
    delete_user_offerers_linked_to_offerers_KO(df_with_venue_equivalences)
    delete_venues_linked_to_offerers_KO(df_with_venue_equivalences)
    delete_offerers_KO(df_with_venue_equivalences)


def _change_offer_venue_id(offer, new_id):
    offer.venueId = int(new_id)
    return offer


def _get_venue_equivalence_df_for_KO_offerers(offerers_KO_df):
    venue_equivalence_columns = ['venue_KO_id', 'venue_KO_name', 'venue_OK_id', 'venue_OK_name',
                'offerer_OK_id', 'offerer_KO_id', 'only_virtual_venue_for_offerer_OK']
    venue_equivalence_df = pd.DataFrame(
        columns=venue_equivalence_columns)
    for index, offerer_KO_row in offerers_KO_df.iterrows():
        offerer_OK_id = int(offerer_KO_row["offerer_OK_id"])
        offerer_KO_id = int(offerer_KO_row["offerer_KO_id"])
        venues_KO = Venue.query.filter_by(managingOffererId=offerer_KO_id).all()
        venues_OK = Venue.query.filter_by(managingOffererId=offerer_OK_id).all()

        for venue_KO in venues_KO:
            matching_venue_OK = next((venue for venue in venues_OK if _normalize_name(venue.name) == _normalize_name(venue_KO.name)), None)
            venue_OK_id, venue_OK_name = _get_venue_OK_id_and_name(matching_venue_OK)
            if len(venues_OK) == 1 and venues_OK[0].isVirtual:
                only_virtual_venue_for_offerer_OK = True
            else:
                only_virtual_venue_for_offerer_OK = False

            venue_matching_row = pd.Series(
                index=venue_equivalence_columns,
                data=[venue_KO.id, venue_KO.name, venue_OK_id, venue_OK_name,
                      offerer_OK_id, offerer_KO_id, only_virtual_venue_for_offerer_OK]
            )
            venue_equivalence_df = venue_equivalence_df.append(venue_matching_row, ignore_index=True)
    return venue_equivalence_df


def _get_venue_OK_id_and_name(matching_venue_OK):
    if matching_venue_OK:
        venue_OK_id = matching_venue_OK.id
        venue_OK_name = matching_venue_OK.name
    else:
        venue_OK_id = None
        venue_OK_name = None
    return venue_OK_id, venue_OK_name


def _normalize_name(name):
    translator = str.maketrans('', '', string.punctuation)
    return unidecode.unidecode(name.lower().translate(translator))


