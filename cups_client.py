import threading

import cups

from server.print.models import PrinterStatus

# pycups (extension C autour de libcups) n'est pas thread-safe pour un
# usage concurrent d'une meme Connection. app.state.cups_conn est
# partage entre toutes les requetes, et les routes sync de print/app.py
# tournent dans le pool de threads de Starlette -- plusieurs requetes
# simultanees (le Dashboard interroge status+supplies des deux
# imprimantes en parallele a chaque poll) pouvaient donc toucher la
# connexion depuis plusieurs threads a la fois, provoquant un SIGSEGV
# observe en conditions reelles (16/08). Verrou pour serialiser l'acces.
_cups_lock = threading.Lock()


def get_connection() -> cups.Connection:
    return cups.Connection()


def list_printers(conn: cups.Connection) -> list[str]:
    with _cups_lock:
        return list(conn.getPrinters().keys())


def get_status(conn: cups.Connection, printer_name: str) -> PrinterStatus:
    with _cups_lock:
        attrs = conn.getPrinterAttributes(printer_name)
        jobs = conn.getJobs(which_jobs="not-completed", my_jobs=False)
    queued = sum(1 for j in jobs.values() if j.get("job-printer-uri", "").endswith(printer_name))

    return PrinterStatus(
        name=printer_name,
        state=attrs.get("printer-state-message") or _state_label(attrs.get("printer-state")),
        state_reasons=attrs.get("printer-state-reasons", []) or [],
        accepting_jobs=attrs.get("printer-is-accepting-jobs", True),
        queued_jobs=queued,
    )


def _state_label(state_enum: int) -> str:
    return {3: "idle", 4: "processing", 5: "stopped"}.get(state_enum, "unknown")


def submit_job(conn: cups.Connection, printer_name: str, file_path: str, copies: int = 1) -> int:
    options = {"copies": str(copies)}
    with _cups_lock:
        return conn.printFile(printer_name, file_path, "Neron print job", options)


def cancel_job(conn: cups.Connection, job_id: int) -> None:
    with _cups_lock:
        conn.cancelJob(job_id)
