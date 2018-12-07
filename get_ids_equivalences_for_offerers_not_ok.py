import pandas as pd

from models import Venue, Offerer
from utils.human_ids import dehumanize


offerers_KO = pd.read_excel('/Users/sofiacalcagno/Downloads/SIREN manquants.xlsx', sheet_name='Doublons + erreurs', na_values=[''], keep_default_na=False)

offerers_KO = offerers_KO[~offerers_KO['ID Strctuture OK'].isna()]

dehumanized_offerer_KO_ids = offerers_KO['id'].astype(str).apply(dehumanize)
dehumanized_offerer_OK_ids = offerers_KO['ID Strctuture OK'].astype(str).apply(dehumanize)


dehumanized_offerer_OK_ids.name = 'ID Structure OK'
dehumanized_offerer_KO_ids.name = 'ID Structure KO'

eq_ids = pd.concat([dehumanized_offerer_KO_ids, dehumanized_offerer_OK_ids], axis=1)
eq_ids.to_csv('eq_id_offerers.csv', index=False)

venues_by_offerer_id = {}
for index, row in eq_ids.iterrows():
    offerer_OK_id = int(row["ID Structure OK"])
    offerer_KO_id = int(row["ID Structure KO"])
    venues_OK = Venue.query.filter_by(managingOffererId=offerer_OK_id).join(Offerer).all()
    venues_KO = Venue.query.filter_by(managingOffererId=offerer_KO_id).join(Offerer).all()
    venues_by_offerer_id[offerer_KO_id] = {"venues_OK": venues_OK, "venues_KO": venues_KO}

