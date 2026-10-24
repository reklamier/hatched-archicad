#!/bin/bash
# Hatched für Archicad einrichten (Mac): trägt dieses Projekt in die Einstellungen von Tapir ein
# (Dokumente/Tapir/config.json), damit „hatched_holen“ in der Tapir-Palette erscheint. Tapir lädt
# das Skript dann bei jedem Start von Archicad neu von GitHub. Doppelklick genügt.
osascript -l JavaScript - <<'JS'
ObjC.import("Foundation");

const PATH = $.NSHomeDirectory().js + "/Documents/Tapir/config.json";
const HATCHED = {
  displayName: "Hatched", repoOwner: "reklamier", repoName: "hatched-archicad", relativeLoc: "",
  token: "", includePattern: "", excludePattern: "",
  // Nur die Skripte holen, nicht Anleitungen, Beispiele und diese Einrichtung.
  excludeFromDownloadPattern:
    "reklamier/hatched-archicad/(einrichten|werkzeug/beispiele)/.*|reklamier/hatched-archicad/[^/]*[.]md",
};
// So legt Tapir die Datei selbst an, wenn es sie noch nicht gibt.
const TAPIR_DEFAULTS = {
  repositories: [{ displayName: "Tapir", repoOwner: "ENZYME-APD", repoName: "tapir-archicad-automation",
    relativeLoc: "builtin-scripts", token: "", excludeFromDownloadPattern: "", includePattern: "",
    excludePattern: "" }],
  localFolders: [], askUpdatingAddOnBeforeEachExecution: false, uvLocation: "", pythonLocation: "",
};

function readText(path) {
  const text = $.NSString.stringWithContentsOfFileEncodingError(path, $.NSUTF8StringEncoding, null);
  return text.isNil() ? null : text.js;
}

function writeText(path, text) {
  const folder = $(path).stringByDeletingLastPathComponent;
  $.NSFileManager.defaultManager.createDirectoryAtPathWithIntermediateDirectoriesAttributesError(
    folder, true, $(), null);
  if (!$(text).writeToFileAtomicallyEncodingError(path, true, $.NSUTF8StringEncoding, null)) {
    throw new Error("Die Einstellungen von Tapir lassen sich nicht speichern: " + path);
  }
}

function tell(text) {
  const app = Application.currentApplication();
  app.includeStandardAdditions = true;
  app.displayDialog(text, { withTitle: "Hatched für Archicad", buttons: ["OK"], defaultButton: "OK" });
  return text;
}

function setUp() {
  const text = readText(PATH);
  const config = text ? JSON.parse(text) : TAPIR_DEFAULTS;
  config.repositories = config.repositories || [];
  const known = config.repositories.some((r) => r.repoOwner === HATCHED.repoOwner &&
    r.repoName === HATCHED.repoName);
  if (known) return tell("Hatched ist schon eingerichtet. Falls „hatched_holen“ in der " +
    "Tapir-Palette fehlt: Archicad neu starten.");
  if (text && !readText(PATH + ".vor-hatched")) writeText(PATH + ".vor-hatched", text);
  config.repositories.push(HATCHED);
  writeText(PATH, JSON.stringify(config, null, 4));
  return tell("Fertig. Bitte Archicad neu starten: In der Tapir-Palette steht dann unter " +
    "„Hatched“ das Skript „hatched_holen“.");
}

function run() {
  try {
    return setUp();
  } catch (error) {
    return tell("Das hat nicht geklappt: " + error.message);
  }
}
JS
