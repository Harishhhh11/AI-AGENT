param(
    [string]$Branch = "main",
    [int]$IntervalSeconds = 20
)

$ErrorActionPreference = "Stop"
$RepoPath = Split-Path -Parent $PSScriptRoot
Set-Location $RepoPath

Write-Host "AI-AGENT Auto Sync started" -ForegroundColor Green
Write-Host "Repository: $RepoPath"
Write-Host "Branch: $Branch"
Write-Host "Checking every $IntervalSeconds seconds. Press Ctrl+C to stop."

while ($true) {
    try {
        $status = git status --porcelain

        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Git status failed. Retrying later."
        }
        elseif ($status) {
            Write-Warning "Local changes detected. Auto-sync skipped to avoid overwriting your work. Commit/stash/discard local changes, then auto-sync will continue."
        }
        else {
            git fetch origin $Branch --quiet

            if ($LASTEXITCODE -eq 0) {
                $local = git rev-parse HEAD
                $remote = git rev-parse "origin/$Branch"

                if ($local -ne $remote) {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] New GitHub changes detected. Updating..." -ForegroundColor Cyan
                    git pull --ff-only origin $Branch

                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Sync complete. VS Code now reflects the latest files." -ForegroundColor Green
                    }
                    else {
                        Write-Warning "Auto-sync could not fast-forward. Resolve the Git state manually before continuing."
                    }
                }
            }
            else {
                Write-Warning "Unable to fetch from GitHub. Check your internet connection and Git authentication."
            }
        }
    }
    catch {
        Write-Warning $_.Exception.Message
    }

    Start-Sleep -Seconds $IntervalSeconds
}
