import gspread
import numpy
import pandas as pd

from connectors.google_spreadsheet import get_credentials
from utils.human_ids import dehumanize


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