"""
Generic base repository.
"""

from typing import Generic
from typing import Type
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session


ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):

    def __init__(
        self,
        db: Session,
        model: Type[ModelType],
    ):
        self.db = db
        self.model = model

    def add(
        self,
        instance: ModelType,
    ) -> ModelType:

        self.db.add(instance)

        return instance

    def get_by_id(
        self,
        record_id: int,
    ) -> ModelType | None:

        statement = select(
            self.model
        ).where(
            self.model.id == record_id
        )

        return self.db.scalar(statement)

    def get_all(self) -> list[ModelType]:

        statement = select(
            self.model
        )

        return list(
            self.db.scalars(statement).all()
        )

    def delete(
        self,
        instance: ModelType,
    ) -> None:

        self.db.delete(instance)