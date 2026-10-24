#!/usr/bin/env python3
"""
Eine Hatched-Schraffur (DXF von hatched.tech) als echte Füllung in Archicad anlegen.

Braucht ein offenes Archicad (25 bis 30) mit der Gratis-Erweiterung Tapir
(https://github.com/ENZYME-APD/tapir-archicad-automation). Nur Python 3, keine weiteren Pakete.

Werkzeug zum Testen; „hatched_holen“ in der Tapir-Palette verwendet die Teile hier.

  python3 hatched_archicad.py pruefen
      Findet Archicad und Tapir und sagt, ob alles bereit ist.

  python3 hatched_archicad.py zeigen
      Listet die Symbol-Füllungen im Projekt mit ihren ersten Linien. Zum Vergleich mit den
      Werten im Dialog „Füllungen“, damit wir die Einheiten von Archicad kennen.

  python3 hatched_archicad.py anlegen <datei.dxf> [--name NAME] [--kachel 100x100]
                                                  [--einheit 0.001] [--ohne-flaeche]
      Legt die Schraffur als Symbol-Füllung „Hatched <Name>“ an (eine gleichnamige wird
      überschrieben) und zeichnet daneben eine Fläche damit, zum Anschauen.
      --kachel   Kachelgrösse in mm, falls die DXF keinen Kachelrahmen hat (Ebene KACHEL_RAHMEN).
      --einheit  Faktor von mm in die Einheit von Archicad; 0.001 heisst Meter.
"""

import argparse
import json
import math
import os
import sys
import urllib.request

PORTS = range(19723, 19744)
FRAME_LAYER = "KACHEL_RAHMEN"
# Ab so vielen Linien warnen: Archicad könnte beim Zeichnen der Füllung langsam werden.
MANY_LINES = 20000


# ---------------------------------------------------------------- Verbindung zu Archicad

def call(port, command, parameters=None):
    """Ein Befehl an die JSON-Schnittstelle von Archicad; gibt das Ergebnis oder wirft."""
    body = json.dumps({"command": command, "parameters": parameters or {}}).encode("utf8")
    request = urllib.request.Request(f"http://127.0.0.1:{port}", body,
                                     {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        answer = json.loads(response.read())
    if not answer.get("succeeded"):
        raise RuntimeError(f"{command}: {answer.get('error', answer)}")
    return answer.get("result", {})


def tapir(port, command, parameters=None):
    """Ein Befehl von Tapir; wirft, wenn Tapir einen Fehler meldet."""
    result = call(port, "API.ExecuteAddOnCommand", {
        "addOnCommandId": {"commandNamespace": "TapirCommand", "commandName": command},
        "addOnCommandParameters": parameters or {},
    })["addOnCommandResponse"]
    if isinstance(result, dict) and "error" in result:
        raise RuntimeError(f"{command}: {result['error']}")
    return result


def find_archicad():
    """Port des offenen Archicad (19723 bis 19743), sonst Abbruch mit Hinweis."""
    for port in PORTS:
        try:
            if call(port, "API.IsAlive").get("isAlive"):
                return port
        except OSError:
            continue
    sys.exit("Kein offenes Archicad gefunden. Bitte Archicad mit einem Projekt öffnen.")


def check_tapir(port):
    """Version von Tapir, sonst Abbruch mit Hinweis zur Installation."""
    try:
        return tapir(port, "GetAddOnVersion").get("version", "?")
    except (RuntimeError, KeyError):
        sys.exit("Archicad läuft, aber Tapir fehlt. Installer: "
                 "https://github.com/ENZYME-APD/tapir-archicad-automation/releases")


# ---------------------------------------------------------------- DXF lesen

def dxf_pairs(path):
    """Die DXF als Liste von (Gruppencode, Wert), nur der Abschnitt ENTITIES."""
    with open(path, encoding="utf8", errors="replace") as f:
        rows = [line.strip() for line in f]
    pairs = [(int(rows[i]), rows[i + 1]) for i in range(0, len(rows) - 1, 2)]
    start = next(i for i, p in enumerate(pairs) if p == (2, "ENTITIES"))
    end = next(i for i in range(start, len(pairs)) if pairs[i] == (0, "ENDSEC"))
    return pairs[start + 1:end]


def dxf_entities(path):
    """Jedes Objekt als (Art, Liste seiner Gruppencodes)."""
    entities = []
    for code, value in dxf_pairs(path):
        if code == 0:
            entities.append((value, []))
        elif entities:
            entities[-1][1].append((code, value))
    return entities


def polyline_points(data):
    """Punkte einer LWPOLYLINE und ob sie geschlossen ist."""
    xs = [float(v) for c, v in data if c == 10]
    ys = [float(v) for c, v in data if c == 20]
    closed = any(c == 70 and int(v) & 1 for c, v in data)
    return list(zip(xs, ys)), closed


def read_dxf(path):
    """Linienstücke, Kreise (Mitte, Radius) und den Kachelrahmen (oder None) in mm."""
    segments, circles, frame = [], [], None
    for kind, data in dxf_entities(path):
        values = dict(data)
        if kind == "LWPOLYLINE":
            points, closed = polyline_points(data)
            if values.get(8) == FRAME_LAYER:
                frame = points
                continue
            ends = points + points[:1] if closed else points
            segments += list(zip(ends, ends[1:]))
        elif kind == "LINE":
            segments.append(((float(values[10]), float(values[20])),
                             (float(values[11]), float(values[21]))))
        elif kind == "CIRCLE":
            circles.append(((float(values[10]), float(values[20])), float(values[40])))
    return segments, circles, frame


def tile_size(segments, frame, kachel):
    """Breite und Höhe der Kachel in mm: Rahmen, sonst --kachel, sonst die Ausdehnung."""
    if frame:
        xs, ys = [p[0] for p in frame], [p[1] for p in frame]
        return max(xs) - min(xs), max(ys) - min(ys)
    if kachel:
        w, h = kachel.lower().split("x")
        return float(w), float(h)
    xs = [p[0] for s in segments for p in s]
    ys = [p[1] for s in segments for p in s]
    print("Hinweis: kein Kachelrahmen in der DXF, nehme die Ausdehnung der Linien.")
    return max(xs) - min(xs), max(ys) - min(ys)


# ---------------------------------------------------------------- Füllung anlegen

def point(p, unit):
    return {"x": p[0] * unit, "y": p[1] * unit}


def fill_data(name, segments, circles, size, unit):
    """Die Füllung für CreateFills: Symbol-Füllung, Kachel als Wiederholung (X1/Y1, X2/Y2)."""
    lines = [{"begin": point(a, unit), "end": point(b, unit)} for a, b in segments if a != b]
    # Ein Kreis als zwei Halbkreise: Anfangspunkt, Mittelpunkt und Winkel.
    arcs = [{"begin": point((cx + s * r, cy), unit), "origin": point((cx, cy), unit),
             "angle": math.pi} for (cx, cy), r in circles for s in (1, -1)]
    return {
        "name": name,
        "subType": "Symbol",
        "scaleWithPlan": True,
        "useForDraft": True,
        "useForCover": True,
        "useForWalls": True,
        "horizontalSpacing": 1.0,
        "verticalSpacing": 1.0,
        "angle": 0.0,
        # Bei Symbol-Füllungen sind das die Versätze X1/Y1 und X2/Y2 aus dem Dialog „Füllungen“.
        "gradientStart": {"x": size[0] * unit, "y": 0.0},
        "gradientEnd": {"x": 0.0, "y": size[1] * unit},
        "symbolLines": lines,
        "symbolArcs": arcs,
    }


def create_fill(port, data):
    """Legt die Füllung an (überschreibt eine gleichnamige) und gibt ihre Kennung zurück."""
    result = tapir(port, "CreateFills", {"fillDataArray": [data], "overwriteExisting": True})
    first = result["attributeIds"][0]
    if "attributeId" not in first:
        raise RuntimeError(f"CreateFills: {first}")
    return first["attributeId"]


def draw_sample(port, fill_id, size, unit):
    """Eine quadratische Fläche mit der Füllung, mindestens 1 m oder 4 Kacheln breit."""
    side = max(1.0, 4 * max(size) * unit)
    corners = [(0, 0), (side, 0), (side, side), (0, side), (0, 0)]
    tapir(port, "CreateHatches", {"hatchesData": [{
        "coordinates": [{"x": x, "y": y} for x, y in corners],
        "fillId": fill_id,
    }]})
    return side


def cmd_anlegen(args):
    segments, circles, frame = read_dxf(args.datei)
    if not segments and not circles:
        sys.exit("Die DXF enthält keine Linien oder Kreise.")
    size = tile_size(segments, frame, args.kachel)
    print(f"Gelesen: {len(segments)} Linien, {len(circles)} Kreise, "
          f"Kachel {size[0]:g} × {size[1]:g} mm.")
    if len(segments) > MANY_LINES:
        print(f"Achtung: sehr viele Linien ({len(segments)}), Archicad wird eventuell langsam.")
    port = find_archicad()
    print(f"Archicad gefunden (Port {port}), Tapir {check_tapir(port)}.")
    name = f"Hatched {args.name or args.datei.rsplit('/', 1)[-1].rsplit('.', 1)[0]}"
    fill_id = create_fill(port, fill_data(name, segments, circles, size, args.einheit))
    print(f"Füllung „{name}“ angelegt.")
    if not args.ohne_flaeche:
        side = draw_sample(port, fill_id, size, args.einheit)
        print(f"Fläche {side:g} × {side:g} am Nullpunkt gezeichnet, zum Anschauen.")


# ---------------------------------------------------------------- Prüfen und Zeigen

def cmd_pruefen(_args):
    port = find_archicad()
    print(f"Archicad gefunden (Port {port}).")
    print(f"Tapir {check_tapir(port)} ist installiert. Alles bereit.")


def cmd_zeigen(_args):
    port = find_archicad()
    check_tapir(port)
    ids = tapir(port, "GetAttributesByType", {"attributeType": "Fill"})["attributes"]
    fills = tapir(port, "GetFills", {"attributeIds": [{"attributeId": a["attributeId"]}
                                                      for a in ids]})["fills"]
    symbols = [f for f in fills if f.get("subType") == "Symbol"]
    if not symbols:
        print("Keine Symbol-Füllung im Projekt.")
    for f in symbols:
        print(f"\n{f['name']}: {len(f.get('symbolLines', []))} Linien, "
              f"{len(f.get('symbolArcs', []))} Bögen, massstabsabhängig: {f.get('scaleWithPlan')}")
        for line in f.get("symbolLines", [])[:3]:
            print(f"  Linie {line['begin']} → {line['end']}")


def main():
    parser = argparse.ArgumentParser(description="Hatched-Schraffur als Archicad-Füllung (Test).")
    sub = parser.add_subparsers(dest="befehl", required=True)
    sub.add_parser("pruefen").set_defaults(run=cmd_pruefen)
    sub.add_parser("zeigen").set_defaults(run=cmd_zeigen)
    anlegen = sub.add_parser("anlegen")
    anlegen.add_argument("datei")
    anlegen.add_argument("--name")
    anlegen.add_argument("--kachel")
    anlegen.add_argument("--einheit", type=float, default=0.001)
    anlegen.add_argument("--ohne-flaeche", action="store_true")
    anlegen.set_defaults(run=cmd_anlegen)
    args = parser.parse_args()
    try:
        args.run(args)
    except RuntimeError as error:
        sys.exit(f"Fehler von Archicad/Tapir: {error}")


if __name__ == "__main__":
    main()
