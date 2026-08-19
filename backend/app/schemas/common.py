"""
Common schemas.
"""

from pydantic import BaseModel
from pydantic import ConfigDict


class BaseSchema(BaseModel):
    """
    Base schema used by all DTOs.
    """

    model_config = ConfigDict(
        from_attributes=True
    )