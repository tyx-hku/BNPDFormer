$ErrorActionPreference = 'Stop'
$previousTexInputs = $env:TEXINPUTS
$previousBibInputs = $env:BIBINPUTS
Push-Location $PSScriptRoot
try {
    $env:TEXINPUTS = '.;..;'
    $env:BIBINPUTS = '.;..;'
    # CAS regenerates this scratch file; remove the previous copy before writing it.
    if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'main.abs')) {
        Remove-Item -LiteralPath (Join-Path $PSScriptRoot 'main.abs') -Force
    }
    & xelatex -synctex=1 -interaction=nonstopmode -halt-on-error main.tex
    if ($LASTEXITCODE -ne 0) { throw 'First XeLaTeX pass failed.' }
    & bibtex main
    if ($LASTEXITCODE -ne 0) { throw 'BibTeX failed.' }
    for ($pass = 0; $pass -lt 2; $pass++) {
        if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'main.abs')) {
            Remove-Item -LiteralPath (Join-Path $PSScriptRoot 'main.abs') -Force
        }
        & xelatex -synctex=1 -interaction=nonstopmode -halt-on-error main.tex
        if ($LASTEXITCODE -ne 0) { throw 'XeLaTeX pass failed.' }
    }
    Write-Host "PDF: $PSScriptRoot\main.pdf"
}
finally {
    $env:TEXINPUTS = $previousTexInputs
    $env:BIBINPUTS = $previousBibInputs
    Pop-Location
}
