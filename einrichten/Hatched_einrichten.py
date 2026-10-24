#!/usr/bin/env python3
"""
Hatched für Archicad einrichten: in der Tapir-Palette mit „+“ hinzufügen und einmal ausführen.
Trägt dieses Projekt in die Einstellungen von Tapir ein (Dokumente/Tapir/config.json), damit
„hatched_holen“ nach einem Neustart von Archicad in der Palette steht. Tapir lädt das Skript dann
bei jedem Start neu von GitHub. Ein Python-Skript statt einer Datei zum Doppelklicken, damit Mac
und Windows nicht vor einem unbekannten Programm warnen.
"""

import copy
import json
import os
import shutil
import sys

HATCHED = {
    "displayName": "Hatched", "repoOwner": "reklamier", "repoName": "hatched-archicad",
    "relativeLoc": "", "token": "", "includePattern": "", "excludePattern": "",
    # Nur die Skripte holen, nicht Anleitungen, Beispiele und diese Einrichtung.
    "excludeFromDownloadPattern":
        "reklamier/hatched-archicad/(einrichten|werkzeug/beispiele)/.*"
        "|reklamier/hatched-archicad/[^/]*[.]md",
}
# So legt Tapir die Datei selbst an, wenn es sie noch nicht gibt.
TAPIR_DEFAULTS = {
    "repositories": [{
        "displayName": "Tapir", "repoOwner": "ENZYME-APD", "repoName": "tapir-archicad-automation",
        "relativeLoc": "builtin-scripts", "token": "", "excludeFromDownloadPattern": "",
        "includePattern": "", "excludePattern": "",
    }],
    "localFolders": [], "askUpdatingAddOnBeforeEachExecution": False, "uvLocation": "",
    "pythonLocation": "",
}


def documents():
    """Ordner „Dokumente“, wie Archicad ihn findet (unter Windows auch umgeleitet, z. B. OneDrive)."""
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        path = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, path)  # 5: Eigene Dokumente
        return path.value
    return os.path.join(os.path.expanduser("~"), "Documents")


def tell(text):
    """Meldung als kleines Fenster und in der Ausgabe der Tapir-Palette."""
    print(text)
    try:
        import tkinter
        from tkinter import messagebox
        root = tkinter.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showinfo("Hatched für Archicad", text, parent=root)
        root.destroy()
    except Exception:
        pass


def set_up(path):
    """Trägt Hatched ein; gibt die Meldung für den Architekten zurück."""
    config = copy.deepcopy(TAPIR_DEFAULTS)
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig") as f:
            config = json.load(f)
    repositories = config.setdefault("repositories", [])
    if any(r.get("repoOwner") == HATCHED["repoOwner"] and r.get("repoName") == HATCHED["repoName"]
           for r in repositories):
        return "Hatched ist schon eingerichtet. Falls „hatched_holen“ fehlt: Archicad neu starten."
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path) and not os.path.exists(path + ".vor-hatched"):
        shutil.copyfile(path, path + ".vor-hatched")
    repositories.append(HATCHED)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    return ("Fertig. Bitte Archicad neu starten: In der Tapir-Palette steht dann unter „Hatched“ "
            "das Skript „hatched_holen“. Diesen Eintrag „Hatched_einrichten“ kannst du danach "
            "mit „−“ entfernen.")


def main():
    path = os.path.join(documents(), "Tapir", "config.json")
    try:
        tell(set_up(path))
    except Exception as error:
        tell(f"Das hat nicht geklappt: {error}")


if __name__ == "__main__":
    main()
