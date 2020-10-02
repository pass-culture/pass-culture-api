import time
from datetime import datetime

import pytz

from models.db import db
from repository import discovery_view_queries
from tests.conftest import clean_database


class CleanTest:
    @clean_database
    def test_should_remove_dead_tuples_in_database(self, app):
        # Given
        discovery_last_vacuum_date = datetime.now().replace(tzinfo=pytz.utc)
        discovery_view_queries.refresh()

        # When
