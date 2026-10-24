# Hatched für Archicad

Holt eine Schraffur von [hatched.tech](https://hatched.tech) als Füllung in Archicad: auf der
Website bei einer Schraffur „Für Archicad“ wählen, in Archicad in der Tapir-Palette
`hatched_holen` ausführen.

## Einrichten (einmalig)

1. **Tapir** installieren, die Gratis-Erweiterung für Archicad 25 bis 30:
   [Mac](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/latest/download/TapirInstaller_Mac.zip),
   [Windows](https://github.com/ENZYME-APD/tapir-archicad-automation/releases/latest/download/TapirInstaller_Win.exe).
2. **Hatched eintragen**, Datei herunterladen und doppelklicken:
   [Mac](https://github.com/reklamier/hatched-archicad/releases/latest/download/Hatched-Archicad-einrichten-Mac.zip),
   [Windows](https://github.com/reklamier/hatched-archicad/releases/latest/download/Hatched-Archicad-einrichten.bat).
   - Mac: Meldet der Mac, er könne die Datei nicht prüfen, in *Systemeinstellungen →
     Datenschutz & Sicherheit* ganz unten „Trotzdem öffnen“ wählen.
   - Windows: Bei „Der Computer wurde durch Windows geschützt“ auf „Weitere Informationen“ und
     „Trotzdem ausführen“ klicken.
3. **Archicad neu starten.** In der Tapir-Palette steht unter „Hatched“ das Skript `hatched_holen`.

Die Einrichtung trägt dieses Projekt in `Dokumente/Tapir/config.json` ein (Sicherung:
`config.json.vor-hatched`). Tapir lädt das Skript bei jedem Start von Archicad neu von hier,
Verbesserungen kommen also von selbst.

## Inhalt

- `hatched_holen.py`: das Skript für die Tapir-Palette. Nimmt den Link aus der Zwischenablage
  (sonst fragt ein Fenster), lädt die Schraffur und legt sie als Symbol-Füllung
  „Hatched <Name>“ an.
- `werkzeug/hatched_archicad.py`: DXF lesen und Füllungen anlegen; im Terminal auch zum Testen
  (`pruefen`, `zeigen`, `anlegen <datei.dxf>`), mit Beispielen in `werkzeug/beispiele/`.
- `einrichten/`: die Dateien zum Doppelklicken für Mac und Windows.

## Neue Fassung der Einrichtung

Die Downloads oben sind die Dateien der neuesten Release. Nach einer Änderung in `einrichten/`:

```
cd einrichten && zip -X Hatched-Archicad-einrichten-Mac.zip Hatched-Archicad-einrichten.command
gh release create v<N> Hatched-Archicad-einrichten-Mac.zip Hatched-Archicad-einrichten.bat
rm Hatched-Archicad-einrichten-Mac.zip
```
