from pydantic import BaseModel
from datetime import datetime

class SyncResponse(BaseModel):
    handle: str
    contests_synced: int
    submissions_synced: int
    status: str
    last_synced_at: datetime
