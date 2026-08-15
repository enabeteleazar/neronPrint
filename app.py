from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from server.common.paths import service_version
from server.common.service import create_service_app
from server.print import cups_client, ink_probe
from server.print.models import PrintJobRequest

VERSION = service_version(__file__)


@asynccontextmanager
async def _setup(app: FastAPI):
    app.state.cups_conn = cups_client.get_connection()
    yield


async def _health_details(request):
    return {}


app = create_service_app(
    name="print",
    title="Neron Print Service",
    version=VERSION,
    capabilities=["print", "printer-status", "ink-levels"],
    setup=_setup,
    health=_health_details,
)


@app.get("/print/printers")
def printers():
    return cups_client.list_printers(app.state.cups_conn)


@app.get("/print/status/{printer_name}")
def status(printer_name: str):
    try:
        return cups_client.get_status(app.state.cups_conn, printer_name)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/print/supplies/{printer_name}")
def supplies(printer_name: str):
    return ink_probe.get_supplies(printer_name)


@app.post("/print/job")
def create_job(job: PrintJobRequest):
    job_id = cups_client.submit_job(
        app.state.cups_conn, job.printer, job.file_path, job.copies
    )
    return {"job_id": job_id}


@app.delete("/print/job/{job_id}")
def delete_job(job_id: int):
    cups_client.cancel_job(app.state.cups_conn, job_id)
    return {"cancelled": job_id}
