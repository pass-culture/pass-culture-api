import gspread
import numpy
import pandas as pd
from memoize import Memoizer
from os import path
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
from pathlib import Path

from utils.human_ids import dehumanize

user_spreadsheet_store = {}
memo = Memoizer(user_spreadsheet_store)


def get_credentials():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    if "PC_GOOGLE_KEY" in os.environ:
        google_key_json_payload = json.loads(os.environ.get("PC_GOOGLE_KEY"))
        key_path = '/tmp/data.json'
        with open(key_path, 'w') as outfile:
            json.dump(google_key_json_payload, outfile)
        credentials = ServiceAccountCredentials.from_json_keyfile_name(key_path, scope)
        os.remove(key_path)
    else:
        key_path = Path(path.dirname(path.realpath(__file__))) / '..'\
                   / 'private' / 'google_key.json'
        credentials = ServiceAccountCredentials.from_json_keyfile_name(key_path, scope)
    return credentials


@memo(max_age=60)
def get_authorized_emails_and_dept_codes():
    gc = gspread.authorize(get_credentials())
    spreadsheet = gc.open_by_key('1YCLVZNU5Gzb2P4Jaf9OW50Oedm2-Z9S099FGitFG64s')
    worksheet = spreadsheet.worksheet('Utilisateurs')

    labels = worksheet.row_values(1)
    email_index = None
    departement_index = None
    for index, label in enumerate(labels):
        if label == 'Email':
            email_index = index
        elif label == 'Département':
            departement_index = index
    if email_index is None:
        raise ValueError("Can't find 'Email' column in users spreadsheet")
    if departement_index is None:
        raise ValueError("Can't find 'Département' column in users spreadsheet")

    values = worksheet.get_all_values()[1:]

    return list(map(lambda v: v[email_index],
                    values)),\
           list(map(lambda v: v[departement_index],
                    values))


def get_offerer_equivalence():
    gc = gspread.authorize(get_credentials())
    spreadsheet = gc.open_by_key('1DlhgbmDqQlu2USZ81yYcrc5ZfVGlBI_oLmVGzmy1gq4')
    worksheet = spreadsheet.worksheet('Doublons + erreurs')
    header = worksheet.row_values(1)
    values = worksheet.get_all_values()[1:]
    for index, column in enumerate(header):
        if column == 'id':
            offerer_KO_col_number = index
        elif column == 'ID Strctuture OK':
            offerer_OK_col_number = index
    structures_to_correct = pd.DataFrame(columns=['offerer_OK_id', 'offerer_KO_id'])
    for row in values:
        if row[offerer_OK_col_number]:
            series = pd.Series(index=['offerer_OK_id', 'offerer_KO_id'],
                               data=[row[offerer_OK_col_number], row[offerer_KO_col_number]])
            structures_to_correct = structures_to_correct.append(series, ignore_index=True)
    structures_to_correct['offerer_OK_id'] = structures_to_correct.offerer_OK_id.apply(dehumanize)
    structures_to_correct['offerer_KO_id'] = structures_to_correct.offerer_KO_id.apply(dehumanize)
    return structures_to_correct


def get_venue_equivalence():
    gc = gspread.authorize(get_credentials())
    spreadsheet = gc.open_by_key('1DlhgbmDqQlu2USZ81yYcrc5ZfVGlBI_oLmVGzmy1gq4')
    worksheet = spreadsheet.worksheet('venue_matching')
    header = worksheet.row_values(1)
    values = worksheet.get_all_values()[1:]
    structures_to_correct = pd.DataFrame(columns=header)
    for row in values:
        series = pd.Series(index=header, data=row)
        structures_to_correct = structures_to_correct.append(series, ignore_index=True)
    structures_to_correct.replace('', numpy.nan, inplace=True)
    return structures_to_correct


