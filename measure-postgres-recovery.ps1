
$start = Get-Date

Write-Host "Starting PostgreSQL Pod recovery test..."

kubectl delete pod postgres-0

$ready = ""

do {
    Start-Sleep -Milliseconds 200

    $ready = kubectl get pod postgres-0 `
        -o jsonpath='{.status.containerStatuses[0].ready}' 2>$null

    $elapsed = ((Get-Date) - $start).TotalSeconds

} while ($ready -ne "true" -and $elapsed -lt 180)

$end = Get-Date
$recoveryTime = ($end - $start).TotalSeconds

if ($ready -eq "true") {
    Write-Host ""
    Write-Host "POSTGRESQL SELF-HEALING TEST COMPLETED"
    Write-Host "Pod: postgres-0"
    Write-Host ("Recovery Time: {0:N2} seconds" -f $recoveryTime)
}
else {
    Write-Host "TEST FAILED: Pod did not become Ready within 180 seconds."
}
