# Read-only preflight. Does not start a second Java process or store passwords.
$ErrorActionPreference = 'Stop'
$instanceRoot = 'C:\Users\18270\.Neo4jDesktop2\Data\dbmss\dbms-956da0b3-4eec-4a04-aa01-484899f94108'
$listeners = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalPort -in 7474,7687 }
if (-not $listeners) {
    Write-Output 'NOT READY: In Neo4j Desktop 2, start ShipFaultKG once and wait for RUNNING.'
    exit 1
}
$listeners | Select-Object LocalAddress,LocalPort,OwningProcess | Format-Table
try {
    $discovery = Invoke-RestMethod -Uri 'http://127.0.0.1:7474/' -TimeoutSec 8
    Write-Output ('Bolt: ' + $discovery.bolt_direct)
    Write-Output ('Version: ' + $discovery.neo4j_version)
    Write-Output 'READY: Open http://localhost:7474/browser/; connect to bolt://127.0.0.1:7687; choose shipfaultkg.'
} catch {
    Write-Output 'HTTP NOT READY: Wait for startup. Do not start another instance.'
    if (Test-Path -LiteralPath (Join-Path $instanceRoot 'logs\neo4j.log')) {
        Get-Content -LiteralPath (Join-Path $instanceRoot 'logs\neo4j.log') -Tail 12
    }
    exit 1
}
