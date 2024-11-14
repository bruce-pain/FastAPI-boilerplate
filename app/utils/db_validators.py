from fastapi import HTTPException
from sqlalchemy.orm import Session


def check_model_existence(db: Session, model, id):
    """Checks if a model exists by its id"""

    obj = db.get(model, ident=id)

    if not obj:
        raise HTTPException(
            status_code=404, detail=f"{model.__name__} does not exist")

    return obj


def get_model_or_none(db: Session, model, id):
    """Unlike `check_model_existence` which throws 
    error if object is not found, this fnction returns 
    the object if it exists, and `None` otherwise """
    return db.get(model, ident=id)


def get_models_by_params(db: Session, model, query_params):
    """Get collection of a model by multiple query params"""
    query = db.query(model)
    for column, value in query_params.items():
        if hasattr(model, column) and value:
            query = query.filter(getattr(model, column).ilike(f"%{value}%"))
    return query


def get_model_by_params(db: Session, model, query_params):
    """Get a single model by multiple query params"""
    return get_models_by_params(db, model, query_params).first()
