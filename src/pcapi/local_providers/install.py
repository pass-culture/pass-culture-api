from pcapi.core.providers.models import Provider
from pcapi.core.providers.repository import get_provider_by_local_class
import pcapi.local_providers
from pcapi.models.db import db


def install_local_providers():
    for class_name in pcapi.local_providers.__all__:
        provider_class = getattr(pcapi.local_providers, class_name)
        db_provider = get_provider_by_local_class(class_name)

        if not db_provider:
            provider = Provider()
            provider.name = provider_class.name
            provider.localClass = class_name
            provider.isActive = False
            db.session.add(provider)

    db.session.commit()
