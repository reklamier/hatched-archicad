@echo off
rem Hatched fuer Archicad einrichten (Windows): traegt dieses Projekt in die Einstellungen von Tapir
rem ein (Dokumente\Tapir\config.json), damit "hatched_holen" in der Tapir-Palette erscheint. Tapir
rem laedt das Skript dann bei jedem Start von Archicad neu von GitHub. Doppelklick genuegt.
rem Der Teil nach der Marke unten ist PowerShell; die Zeilen hier fuehren ihn aus.
set "HATCHED_BAT=%~f0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$f = $env:HATCHED_BAT; $s = [IO.File]::ReadAllText($f, [Text.Encoding]::UTF8); $m = '#POWER' + 'SHELL#'; Invoke-Expression $s.Substring($s.IndexOf($m) + $m.Length)"
exit /b
#POWERSHELL#
Add-Type -AssemblyName PresentationFramework

$Path = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "Tapir\config.json"
$Hatched = [ordered]@{
    displayName = "Hatched"; repoOwner = "reklamier"; repoName = "hatched-archicad"; relativeLoc = ""
    token = ""; includePattern = ""; excludePattern = ""
    # Nur die Skripte holen, nicht Anleitungen, Beispiele und diese Einrichtung.
    excludeFromDownloadPattern =
        "reklamier/hatched-archicad/(einrichten|werkzeug/beispiele)/.*|reklamier/hatched-archicad/[^/]*[.]md"
}
# So legt Tapir die Datei selbst an, wenn es sie noch nicht gibt.
$TapirDefaults = '{"repositories": [{"displayName": "Tapir", "repoOwner": "ENZYME-APD",
    "repoName": "tapir-archicad-automation", "relativeLoc": "builtin-scripts", "token": "",
    "excludeFromDownloadPattern": "", "includePattern": "", "excludePattern": ""}],
    "localFolders": [], "askUpdatingAddOnBeforeEachExecution": false, "uvLocation": "",
    "pythonLocation": ""}'
$Utf8 = New-Object System.Text.UTF8Encoding $false

function Tell($text) {
    [System.Windows.MessageBox]::Show($text, "Hatched für Archicad") | Out-Null
}

function Set-Up {
    $text = if (Test-Path -LiteralPath $Path) { [IO.File]::ReadAllText($Path, $Utf8) } else { $null }
    $config = ConvertFrom-Json $(if ($text) { $text } else { $TapirDefaults })
    $repositories = @($config.repositories | Where-Object { $_ })
    if ($repositories | Where-Object { $_.repoOwner -eq "reklamier" -and $_.repoName -eq "hatched-archicad" }) {
        return Tell "Hatched ist schon eingerichtet. Falls „hatched_holen“ in der Tapir-Palette fehlt: Archicad neu starten."
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $Path) | Out-Null
    if ($text -and -not (Test-Path -LiteralPath "$Path.vor-hatched")) {
        [IO.File]::WriteAllText("$Path.vor-hatched", $text, $Utf8)
    }
    $all = @($repositories + [pscustomobject]$Hatched)
    $config | Add-Member -NotePropertyName repositories -NotePropertyValue $all -Force
    [IO.File]::WriteAllText($Path, (ConvertTo-Json $config -Depth 10), $Utf8)
    Tell "Fertig. Bitte Archicad neu starten: In der Tapir-Palette steht dann unter „Hatched“ das Skript „hatched_holen“."
}

try { Set-Up } catch { Tell "Das hat nicht geklappt: $($_.Exception.Message)" }
