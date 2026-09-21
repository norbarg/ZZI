New-Item -ItemType Directory -Force -Path "builds" | Out-Null


function Check-Build {
    param([string]$Name)

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ERROR: build failed: $Name" -ForegroundColor Red
        exit 1
    }

    Write-Host "Created: $Name" -ForegroundColor Green
    Write-Host ""
}


Write-Host "============================================================"
Write-Host "Variant 1: ALL protections disabled"
Write-Host "============================================================"

gcc vulnerable.c `
    -o builds\vuln_unprotected.exe `
    -fno-stack-protector `
    "-Wl,--disable-nxcompat" `
    "-Wl,--disable-dynamicbase" `
    -w

Check-Build "builds\vuln_unprotected.exe"


Write-Host "============================================================"
Write-Host "Variant 2: DEP/NX only"
Write-Host "============================================================"

gcc vulnerable.c `
    -o builds\vuln_nx_only.exe `
    -fno-stack-protector `
    "-Wl,--nxcompat" `
    "-Wl,--disable-dynamicbase" `
    -w

Check-Build "builds\vuln_nx_only.exe"


Write-Host "============================================================"
Write-Host "Variant 3: DEP/NX + Stack Canary"
Write-Host "============================================================"

gcc vulnerable.c `
    -o builds\vuln_canary.exe `
    -fstack-protector-all `
    "-Wl,--nxcompat" `
    "-Wl,--disable-dynamicbase" `
    -w

Check-Build "builds\vuln_canary.exe"


Write-Host "============================================================"
Write-Host "Variant 4: FULL protection - DEP/NX + Canary + ASLR"
Write-Host "============================================================"

gcc vulnerable.c `
    -o builds\vuln_full_protection.exe `
    -fstack-protector-all `
    "-Wl,--nxcompat" `
    "-Wl,--dynamicbase" `
    -w

Check-Build "builds\vuln_full_protection.exe"


Write-Host "============================================================"
Write-Host "ALL FOUR BUILDS CREATED SUCCESSFULLY"
Write-Host "============================================================"