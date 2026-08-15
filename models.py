from pydantic import BaseModel


class InkLevel(BaseModel):
    color: str
    percent: int


class SupplyLevels(BaseModel):
    printer: str
    supported: bool
    levels: list[InkLevel] = []


class PrinterStatus(BaseModel):
    name: str
    state: str
    state_reasons: list[str] = []
    accepting_jobs: bool
    queued_jobs: int


class PrintJobRequest(BaseModel):
    printer: str
    file_path: str
    copies: int = 1
