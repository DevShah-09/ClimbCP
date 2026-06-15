from pydantic import BaseModel

class SyncResponse(BaseModel):
    handle: str
    contests_synced: int
    submissions_synced: int
    status: str
