import csv
from typing import List
from pcapi.repository import repository
from pcapi.models import VenueSQLEntity, ApiErrors
from pcapi.utils.logger import logger

def update_venue_creation_date(file_path: str):
    updated_venue_count = 0
    venues_to_update = _read_venue_creation_date_from_file(file_path)
    venue_ids_in_error = []

    for venue_id, creation_date in venues_to_update:
        venue = VenueSQLEntity.query.get(venue_id)
        if not venue:
            venue_ids_in_error.append(str(venue_id))
            continue

        venue.dateCreated = creation_date
        try:
            repository.save(venue)
            updated_venue_count += 1
        except ApiErrors:
            venue_ids_in_error.append(str(venue_id))

    if venue_ids_in_error:
        errored_venues = ', '.join(venue_ids_in_error)
        logger.info(f'Venues in error : {errored_venues}')

    logger.info(f'{updated_venue_count} venues have been updated')


def _read_venue_creation_date_from_file(file_path: str) -> List[tuple]:
    with open(file_path, mode='r', newline='\n') as file:
        data = [tuple(line) for line in csv.reader(file, delimiter=',')]
        return data
