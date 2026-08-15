import re
import subprocess

from server.print.models import InkLevel, SupplyLevels

# Seule l'EPSON XP-2200 est sondable, via un modele proche (escp2-xp240)
# et une regle sudoers ciblee sur cette commande exacte.
_EPSON_PRINTER_NAME = "EPSON_XP-2200_Series"
_EPSON_DEVICE = "/dev/usb/lp0"
_EPSON_MODEL = "escp2-xp240"

_LINE_RE = re.compile(r"^\s*(.+?)\s{2,}(\d+)\s*$")


def get_supplies(printer_name: str) -> SupplyLevels:
    if printer_name != _EPSON_PRINTER_NAME:
        return SupplyLevels(printer=printer_name, supported=False, levels=[])

    try:
        result = subprocess.run(
            [
                "sudo", "/usr/bin/escputil",
                "-r", _EPSON_DEVICE,
                "-m", _EPSON_MODEL,
                "--ink-level",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return SupplyLevels(printer=printer_name, supported=False, levels=[])

    levels = []
    for line in result.stdout.splitlines():
        match = _LINE_RE.match(line)
        if match:
            color, percent = match.groups()
            if color.lower() != "ink color":
                levels.append(InkLevel(color=color.strip(), percent=int(percent)))

    return SupplyLevels(printer=printer_name, supported=bool(levels), levels=levels)
