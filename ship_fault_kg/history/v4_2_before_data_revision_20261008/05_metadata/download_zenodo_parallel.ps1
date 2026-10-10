$ErrorActionPreference = 'Stop'

$base = 'D:\RAGQnASystem\RAGQnASystem-main\ship_fault_kg_data'
$tempRoot = Join-Path $base 'downloads_tmp'
$zenodoIps = @(
    '188.185.48.75',
    '188.184.103.118',
    '137.138.52.235',
    '137.138.153.219'
)
$zenodoIp = $zenodoIps[0]
$parallelParts = 8

$items = @(
    @{
        Url = 'https://zenodo.org/records/20258638/files/All_data.zip?download=1'
        Output = Join-Path $base '01_datasets\marine_diesel_RAG_corpus_All_data.zip'
    },
    @{
        Url = 'https://zenodo.org/records/19857425/files/Marine_Engine_Fault_Data_v1.zip?download=1'
        Output = Join-Path $base '01_datasets\Marine_Engine_Fault_Data_v1.zip'
    },
    @{
        Url = 'https://zenodo.org/records/20101612/files/Zenodo_Dataset_Package.zip?download=1'
        Output = Join-Path $base '01_datasets\Azimuth_Thruster_CBM_Dataset.zip'
    },
    @{
        Url = 'https://zenodo.org/records/14620906/files/1-Version%20postprint-copyright.pdf?download=1'
        Output = Join-Path $base '03_papers\2018_Marine_Diesel_Engine_Failure_Simulator.pdf'
    }
)

New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

foreach ($item in $items) {
    $url = $item.Url
    $output = $item.Output
    $name = [IO.Path]::GetFileName($output)
    Write-Output "Preparing $name"

    $headers = $null
    foreach ($headerIp in $zenodoIps) {
        $candidateHeaders = & curl.exe --resolve "zenodo.org:443:$headerIp" --head --location --fail --max-time 60 --silent --show-error $url
        if ($LASTEXITCODE -eq 0 -and $candidateHeaders) {
            $headers = $candidateHeaders
            $zenodoIp = $headerIp
            break
        }
    }
    if (-not $headers) {
        throw "Unable to read headers for $url from any configured Zenodo node"
    }

    $lengthLines = @($headers | Where-Object { $_ -match '^content-length:\s*\d+' })
    if ($lengthLines.Count -eq 0) {
        throw "No Content-Length returned for $url"
    }
    $totalLength = [int64](($lengthLines[-1] -replace '(?i)^content-length:\s*', '').Trim())

    if ((Test-Path -LiteralPath $output) -and ((Get-Item -LiteralPath $output).Length -eq $totalLength)) {
        Write-Output "Already complete: $name ($totalLength bytes)"
        continue
    }

    $itemTemp = Join-Path $tempRoot ([IO.Path]::GetFileNameWithoutExtension($output))
    New-Item -ItemType Directory -Force -Path $itemTemp | Out-Null
    $chunkSize = [math]::Ceiling($totalLength / $parallelParts)
    $jobs = @()

    for ($index = 0; $index -lt $parallelParts; $index++) {
        $start = [int64]($index * $chunkSize)
        if ($start -ge $totalLength) { break }
        $end = [int64][math]::Min($totalLength - 1, $start + $chunkSize - 1)
        $partPath = Join-Path $itemTemp ("part_{0:D2}.bin" -f $index)
        $expected = $end - $start + 1

        $existingLength = if (Test-Path -LiteralPath $partPath) { (Get-Item -LiteralPath $partPath).Length } else { 0 }
        if ($existingLength -eq $expected) {
            continue
        }

        if ($existingLength -gt 0) {
            $jobs += [pscustomobject]@{
                Process = $null
                Path = $partPath
                Expected = $expected
                Range = "$start-$end"
                Start = $start
                End = $end
            }
            continue
        }

        $args = @(
            '--resolve', "zenodo.org:443:$zenodoIp",
            '--location', '--fail',
            '--connect-timeout', '30', '--max-time', '300',
            '--silent', '--show-error', '--range', "$start-$end",
            '--output', $partPath, $url
        )
        $process = Start-Process -FilePath 'curl.exe' -ArgumentList $args -WindowStyle Hidden -PassThru
        $jobs += [pscustomobject]@{
            Process = $process
            Path = $partPath
            Expected = $expected
            Range = "$start-$end"
            Start = $start
            End = $end
        }
    }

    foreach ($job in $jobs) {
        if ($null -ne $job.Process) {
            $job.Process.WaitForExit()
        }
        $actual = if (Test-Path -LiteralPath $job.Path) { (Get-Item -LiteralPath $job.Path).Length } else { 0 }
        $repairAttempt = 0
        while ($actual -lt $job.Expected -and $repairAttempt -lt 12) {
            $repairAttempt++
            $repairStart = [int64]($job.Start + $actual)
            $repairPath = "$($job.Path).resume"
            $repairIp = $zenodoIps[$repairAttempt % $zenodoIps.Count]
            if (Test-Path -LiteralPath $repairPath) {
                Remove-Item -LiteralPath $repairPath -Force
            }
            & curl.exe --resolve "zenodo.org:443:$repairIp" --location --fail `
                --connect-timeout 30 --max-time 300 --silent --show-error `
                --range "$repairStart-$($job.End)" --output $repairPath $url
            $repairBytes = if (Test-Path -LiteralPath $repairPath) { (Get-Item -LiteralPath $repairPath).Length } else { 0 }
            if ($repairBytes -gt 0) {
                $destination = [IO.File]::Open($job.Path, [IO.FileMode]::Append, [IO.FileAccess]::Write)
                $source = [IO.File]::OpenRead($repairPath)
                try { $source.CopyTo($destination) }
                finally {
                    $source.Dispose()
                    $destination.Dispose()
                }
                Remove-Item -LiteralPath $repairPath -Force
            }
            $actual = if (Test-Path -LiteralPath $job.Path) { (Get-Item -LiteralPath $job.Path).Length } else { 0 }
        }
        if ($actual -ne $job.Expected) {
            throw "Incorrect part size for ${name} range $($job.Range): expected $($job.Expected), got $actual"
        }
    }

    $partFiles = Get-ChildItem -LiteralPath $itemTemp -Filter 'part_*.bin' | Sort-Object Name
    $outputStream = [IO.File]::Open($output, [IO.FileMode]::Create, [IO.FileAccess]::Write)
    try {
        foreach ($part in $partFiles) {
            $inputStream = [IO.File]::OpenRead($part.FullName)
            try { $inputStream.CopyTo($outputStream) }
            finally { $inputStream.Dispose() }
        }
    }
    finally {
        $outputStream.Dispose()
    }

    $finalLength = (Get-Item -LiteralPath $output).Length
    if ($finalLength -ne $totalLength) {
        throw "Combined file size mismatch for ${name}: expected $totalLength, got $finalLength"
    }

    foreach ($part in $partFiles) {
        Remove-Item -LiteralPath $part.FullName -Force
    }
    Remove-Item -LiteralPath $itemTemp -Force
    Write-Output "Completed $name ($finalLength bytes)"
}
