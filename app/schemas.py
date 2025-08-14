from pydantic import BaseModel, Field


class SpinInput(BaseModel):
    user_id: int
    bet: int = Field(..., gt=0)
