from flask_sqlalchemy import SQLAlchemy
from contextlib import ContextDecorator

from postgresql_audit.flask import versioning_manager

db = SQLAlchemy()

Model = db.Model

versioning_manager.init(Model)

def get_model_with_table_name(table_name):
    for model in Model._decl_class_registry.values():
        if not hasattr(model, '__table__'):
            continue
        if model.__tablename__ == table_name:
            return model

class auto_close_db_transaction(ContextDecorator):
    def __enter__(self, *exc):
       pass

    def __exit__(self, *exc):
        if len(db.session.dirty) > 0:
            raise Exception('Session was left dirty')
        db.session.commit()
        return False
