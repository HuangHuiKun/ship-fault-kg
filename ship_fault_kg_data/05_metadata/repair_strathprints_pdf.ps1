$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$paper = Join-Path $root '03_papers\2024_Data_Driven_Marine_Engine_Fault_Diagnosis.pdf'
$temp = Join-Path $root 'downloads_tmp\strathprints_repair'
$url = 'https://strathprints.strath.ac.uk/90777/13/Patil-etal-JMET-2024-Data-driven-model-for-marine-engine-fault-diagnosis.pdf'
$expectedLength = 3594884
$expectedMd5 = 'cb29038676437494fb156eeeb6f95f0b'
$currentLength = (Get-Item -LiteralPath $paper).Length
if ($currentLength -ge $expectedLength) { throw 'Expected a truncated PDF prefix.' }
New-Item -ItemType Directory -Force -Path $temp | Out-Null
$remaining = $expectedLength - $currentLength
$size = [math]::Ceiling($remaining / 8)
$jobs = @()
for ($i = 0; $i -lt 8; $i++) {
    $start = $currentLength + $i * $size
    if ($start -ge $expectedLength) { break }
    $end = [math]::Min($expectedLength - 1, $start + $size - 1)
    $part = Join-Path $temp ('part_{0:D2}.bin' -f $i)
    $err = Join-Path $temp ('part_{0:D2}.err' -f $i)
    $args = @('-L','--silent','--show-error','--max-time','240','--range',"$start-$end",$url,'-o',$part)
    $proc = Start-Process -FilePath 'curl.exe' -ArgumentList $args -WindowStyle Hidden -PassThru -RedirectStandardError $err
    $jobs += [pscustomobject]@{ Process=$proc; Part=$part; Expected=($end-$start+1); Range="$start-$end" }
}
foreach ($job in $jobs) {
    $job.Process.WaitForExit()
    $actual = if (Test-Path -LiteralPath $job.Part) { (Get-Item -LiteralPath $job.Part).Length } else { 0 }
    Write-Output ("range=" + $job.Range + " actual=" + $actual + " expected=" + $job.Expected)
    if ($actual -ne $job.Expected) { throw "Incomplete range $($job.Range)" }
}
$candidate = Join-Path $temp 'complete_candidate.pdf'
$output = [IO.File]::Open($candidate,[IO.FileMode]::Create)
try {
    $input = [IO.File]::OpenRead($paper)
    try { $input.CopyTo($output) } finally { $input.Dispose() }
    foreach ($job in $jobs) {
        $input = [IO.File]::OpenRead($job.Part)
        try { $input.CopyTo($output) } finally { $input.Dispose() }
    }
} finally { $output.Dispose() }
$newLength = (Get-Item -LiteralPath $candidate).Length
$md5 = (Get-FileHash -LiteralPath $candidate -Algorithm MD5).Hash.ToLowerInvariant()
Write-Output "candidate_length=$newLength md5=$md5"
if ($newLength -ne $expectedLength -or $md5 -ne $expectedMd5) { throw 'PDF checksum did not match server header.' }
$backup = Join-Path $temp 'old_truncated.pdf'
Move-Item -LiteralPath $paper -Destination $backup
Copy-Item -LiteralPath $candidate -Destination $paper
Write-Output 'Repaired PDF installed; truncated original saved in downloads_tmp.'
