#!/usr/bin/env python3
"""
Hatched Import: legt die Schraffur, die auf hatched.tech mit „Für Archicad“ kopiert wurde, als
Füllung in Archicad an. Gedacht für die Tapir-Palette in Archicad (Knopf statt Terminal); Tapir
übergibt den Port mit --port. Liegt kein Link in der Zwischenablage, fragt ein kleines Fenster.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
from hatched_archicad import (  # noqa: E402
    check_tapir, create_fill, fill_data, find_archicad, read_dxf, tile_size,
)

LINK = re.compile(r"https://[^/\s]+/api/archicad/[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")
# Die DXF von Hatched ist in mm, Archicad rechnet in Meter.
UNIT = 0.001


# ---------------------------------------------------------------- Meldungen

def tk_root():
    """Unsichtbares Hauptfenster für Dialoge, oder None ohne tkinter."""
    try:
        import tkinter
        root = tkinter.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        return root
    except Exception:
        return None


def tell(text, error=False):
    """Meldung als kleines Fenster und in der Ausgabe der Tapir-Palette."""
    print(text)
    root = tk_root()
    if root is None:
        return
    from tkinter import messagebox
    (messagebox.showerror if error else messagebox.showinfo)("Hatched", text, parent=root)
    root.destroy()


# ---------------------------------------------------------------- Link finden

def clipboard():
    """Text aus der Zwischenablage; leer, wenn es nicht geht."""
    if sys.platform == "darwin":
        result = subprocess.run(["pbpaste"], capture_output=True, text=True)
        return result.stdout
    root = tk_root()
    if root is None:
        return ""
    try:
        return root.clipboard_get()
    except Exception:
        return ""
    finally:
        root.destroy()


def ask_link():
    """Fenster zum Einfügen des Links; leer bei Abbrechen."""
    root = tk_root()
    if root is None:
        return ""
    from tkinter import simpledialog
    text = simpledialog.askstring(
        "Hatched Import",
        "Auf hatched.tech bei einer Schraffur „Für Archicad“ wählen\n"
        "und den Link hier einfügen:", parent=root)
    root.destroy()
    return text or ""


def find_link():
    """Der Link aus der Zwischenablage, sonst aus dem Fenster; None, wenn keiner da ist."""
    for text in (clipboard(), ask_link()):
        match = LINK.search(text or "")
        if match:
            return match.group(0)
    return None


# ---------------------------------------------------------------- Schraffur holen

def file_name(disposition):
    """Name der Schraffur aus dem Kopf der Antwort, ohne „.dxf“."""
    utf8 = re.search(r"filename\*=UTF-8''([^;]+)", disposition or "")
    plain = re.search(r'filename="([^"]+)"', disposition or "")
    name = urllib.parse.unquote(utf8.group(1)) if utf8 else plain.group(1) if plain else "Schraffur"
    return re.sub(r"\.dxf$", "", name, flags=re.I)


def server_message(error):
    """Meldung des Servers aus einer abgelehnten Anfrage."""
    try:
        return json.loads(error.read()).get("message") or f"Fehler {error.code}"
    except Exception:
        return f"Fehler {error.code}"


def fetch_with_curl(link):
    """Ersatz, wenn Python die Zertifikate nicht findet (z. B. Python ohne Zertifikate auf dem Mac)."""
    result = subprocess.run(["curl", "-sS", "-D", "-", link], capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"hatched.tech ist nicht erreichbar ({result.stderr.decode().strip()}).")
    head, _, data = result.stdout.partition(b"\r\n\r\n")
    status = int(head.split(b" ", 2)[1])
    if status != 200:
        try:
            raise RuntimeError(json.loads(data).get("message") or f"Fehler {status}")
        except ValueError:
            raise RuntimeError(f"Fehler {status}")
    disposition = re.search(rb"(?im)^content-disposition:(.*)$", head)
    return file_name(disposition.group(1).decode() if disposition else ""), data


def fetch(link):
    """Name und Inhalt der DXF über den Link; wirft mit der Meldung des Servers."""
    try:
        with urllib.request.urlopen(link, timeout=60) as response:
            return file_name(response.headers.get("Content-Disposition")), response.read()
    except urllib.error.HTTPError as error:
        raise RuntimeError(server_message(error))
    except urllib.error.URLError as error:
        if "CERTIFICATE" in str(error.reason).upper():
            return fetch_with_curl(link)
        raise RuntimeError(f"hatched.tech ist nicht erreichbar ({error.reason}).")


def download(link):
    """DXF über den Link holen; gibt (Name, Pfad der Datei) zurück oder wirft mit Meldung."""
    name, data = fetch(link)
    handle, path = tempfile.mkstemp(suffix=".dxf")
    with os.fdopen(handle, "wb") as f:
        f.write(data)
    return name, path


def bring_to_archicad(port, link):
    """Holt die Schraffur und legt sie als „Hatched <Name>“ an; gibt den Namen zurück."""
    name, path = download(link)
    try:
        segments, circles, frame = read_dxf(path)
    finally:
        os.remove(path)
    if not segments and not circles:
        raise RuntimeError("Die Schraffur enthält keine Linien.")
    size = tile_size(segments, frame, None)
    fill = f"Hatched {name}"
    create_fill(port, fill_data(fill, segments, circles, size, UNIT))
    return fill


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int)
    args, _unknown = parser.parse_known_args()
    port = args.port or find_archicad()
    check_tapir(port)
    link = find_link()
    if not link:
        tell("Kein Link von hatched.tech gefunden. Bitte dort „Für Archicad“ wählen.", error=True)
        return
    try:
        fill = bring_to_archicad(port, link)
    except RuntimeError as error:
        tell(str(error), error=True)
        return
    tell(f"„{fill}“ ist jetzt unter den Füllungen in Archicad.")


if __name__ == "__main__":
    main()
