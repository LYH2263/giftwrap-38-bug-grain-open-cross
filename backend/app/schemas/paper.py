from pydantic import BaseModel, Field

class PaperWidthUpdate(BaseModel):
    roll_width: float = Field(gt=0)
