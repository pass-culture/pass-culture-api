from typing import Container
from typing import Optional
from typing import Type

from pydantic import BaseConfig
from pydantic import BaseModel
from pydantic import create_model
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.properties import ColumnProperty


class OrmConfig(BaseConfig):
    orm_mode = True


# From https://github.com/tiangolo/pydantic-sqlalchemy/blob/2b87140ed1230d39e03b4979527b820888ede8e7/pydantic_sqlalchemy/main.py
def sqlalchemy_to_pydantic(
    db_model: Type, *, config: Type = OrmConfig, exclude: Container[str] = []
) -> Type[BaseModel]:
    mapper = inspect(db_model)
    fields = {}
    for attr in mapper.attrs:
        if isinstance(attr, ColumnProperty):
            if attr.columns:
                name = attr.key
                if name in exclude:
                    continue
                column = attr.columns[0]
                python_type: Optional[type] = None
                if hasattr(column.type, "impl"):
                    if hasattr(column.type.impl, "python_type"):
                        python_type = column.type.impl.python_type
                elif hasattr(column.type, "python_type"):
                    python_type = column.type.python_type
                assert python_type, f"Could not infer python_type for {column}"
                # Modified to avoir taking default into account
                # default = None
                # if column.default is None and not column.nullable:
                #     default = ...
                default = None if column.nullable else ...
                fields[name] = (python_type, default)
    pydantic_model = create_model(db_model.__name__, __config__=config, **fields)  # type: ignore
    return pydantic_model


def validate_schema_is_substract(main_shema, substract_schema):
    errors = []
    for attr in substract_schema["properties"]:
        if attr not in main_shema["properties"]:
            errors.append((attr, "Unknown property"))
        elif substract_schema["properties"][attr]["type"] != substract_schema["properties"][attr]["type"]:
            errors.append((attr, "Not the same type"))
    for attr in substract_schema["required"]:
        if attr not in main_shema["required"]:
            errors.append((attr, "Can't be required"))
    return errors


def pydantic_model_is_valid(model):
    sqla_schema = sqlalchemy_to_pydantic(model._SQLAModel).schema()
    pydantic_schema = ProviderResponseORM.schema()
    errors = validate_schema_is_substract(sqla_schema, pydantic_schema)
    if errors:
        raise Exception(errors)
    return True


# Example test case

from pcapi.models.provider import Provider


class ProviderResponseORM(BaseModel):
    _SQLAModel = Provider
    enabledForPro: bool
    id: str
    isActive: bool
    localClass: str
    name: str
    requireProviderIdentifier: bool

    class Config:
        orm_mode = True


assert pydantic_model_is_valid(ProviderResponseORM)
