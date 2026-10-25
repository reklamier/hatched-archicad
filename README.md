# Hatched für Archicad

Holt eine Schraffur von [hatched.tech](https://hatched.tech) als Füllung in Archicad: auf der
Website bei einer Schraffur „In Archicad importieren“ wählen, in Archicad in der Tapir-Palette
`Hatched_Import` ausführen.

## Einrichten (einmalig)

1. **Tapir** installieren, die Gratis-Erweiterung für Archicad 25 bis 30:
   [Mac](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/latest/download/TapirInstaller_Mac.zip),
   [Windows](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/latest/download/TapirInstaller_Win.exe).
2. **Hatched eintragen:** [Hatched_Setup.py](https://hatched.tech/archicad/setup)
   herunterladen. In Archicad in der Tapir-Palette auf „+“ klicken, die Datei wählen und
   ausführen. Ein Python-Skript statt eines Programms, damit Mac und Windows nicht warnen.
3. **Archicad neu starten.** In der Tapir-Palette steht unter „Hatched“ das Skript `Hatched_Import`.

Die Einrichtung trägt dieses Projekt in `Dokumente/Tapir/config.json` ein (Sicherung:
`config.json.before-hatched`). Tapir lädt das Skript bei jedem Start von Archicad neu von hier,
Verbesserungen kommen also von selbst. Danach kann der Eintrag „Hatched_Setup“ mit „−“
wieder aus der Palette.

## Inhalt

- `Hatched_Import.py`: das Skript für die Tapir-Palette. Nimmt den Link aus der Zwischenablage
  (sonst fragt ein Fenster), lädt die Schraffur und legt sie als Symbol-Füllung
  „Hatched <Name>“ an.
- `tools/hatched_archicad.py`: DXF lesen und Füllungen anlegen; im Terminal auch zum Testen
  (`pruefen`, `zeigen`, `anlegen <datei.dxf>`), mit Beispielen in `tools/examples/`.
- `setup/Hatched_Setup.py`: die Einrichtung (hatched.tech/archicad/setup gibt
  diese Datei zum Herunterladen aus).
