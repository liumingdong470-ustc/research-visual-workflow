param([Parameter(Mandatory=$true)][string]$JobPath)
$ErrorActionPreference = 'Stop'
$job = Get-Content -LiteralPath $JobPath -Raw -Encoding UTF8 | ConvertFrom-Json
$folder = Split-Path -Parent $JobPath
$project = Join-Path $folder 'figure.opj'
$graphFile = Join-Path $folder 'figure.ogg'
$origin = $null
$missing = -1.23456789E-300
$getProperty = [Reflection.BindingFlags]::GetProperty

function Run-LabTalk([string]$code) {
    if (-not $origin.Execute($code)) { throw "Origin could not execute: $code" }
}

function Get-LabTalk([string]$name) {
    Run-LabTalk ('NativeQuery=' + $name + ';')
    return $origin.GetType().InvokeMember('LTVar',$getProperty,$null,$origin,@('NativeQuery'))
}

function Check-Table([string]$name) {
    $rows = $job.columns[0].Count
    $count = $job.columns.Count
    $actual = $origin.GetWorksheet($name, 0, 0, $rows-1, $count-1)
    if ($null -eq $actual -or $actual.Rank -ne 2 -or $actual.GetLength(0) -ne $rows -or $actual.GetLength(1) -ne $count) {
        throw 'Origin worksheet dimensions differ from the source.'
    }
    $rowBase = $actual.GetLowerBound(0)
    $colBase = $actual.GetLowerBound(1)
    for ($row=0; $row -lt $rows; $row++) {
        for ($col=0; $col -lt $count; $col++) {
            $value = $actual[($row+$rowBase),($col+$colBase)]
            $expected = $job.columns[$col][$row]
            if ($null -eq $expected) {
                if ($null -ne $value -and [double]$value -ne $missing) { throw 'A missing value changed.' }
            } elseif ($null -eq $value -or [math]::Abs([double]$value-[double]$expected) -gt 1e-12*[math]::Max(1,[math]::Abs([double]$expected))) {
                throw 'Origin worksheet value differs from the source.'
            }
        }
    }
}

try {
    # ApplicationSI creates an independent instance and preserves the user's active project.
    $origin = New-Object -ComObject Origin.ApplicationSI
    if (-not $origin.NewProject()) { throw 'Origin could not create a project.' }
    $version = Get-LabTalk '@V'
    $book = $origin.CreatePage(2, 'SourceData', 'Origin', 2)
    if (-not $book) { throw 'Origin could not create the data workbook.' }
    Run-LabTalk ('wks.ncols=' + $job.columns.Count + ';')
    for ($col=0; $col -lt $job.columns.Count; $col++) {
        $values = [double[]]@($job.columns[$col] | ForEach-Object { if ($null -eq $_) {$missing} else {[double]$_} })
        if (-not $origin.PutWorksheet($book,$values,0,$col)) { throw 'Origin could not write a worksheet column.' }
        $index = $col + 1
        Run-LabTalk ('wks.col' + $index + '.lname$="' + $job.labels[$col] + '";')
    }
    Check-Table $book
    $first = $job.display_start + 1
    $last = $first + $job.series_count - 1
    Run-LabTalk ('plotxy iy:=(1,' + $first + ':' + $last + ') plot:=' + $job.plot_id + ';')
    Run-LabTalk 'string NativeGraph$=%H;'
    $graph = $origin.GetType().InvokeMember('LTStr',$getProperty,$null,$origin,@('NativeGraph'))
    if (-not $graph) { throw 'Origin did not create a graph page.' }
    Run-LabTalk 'layer -gu; %Z=""; layer -c;'
    for ($i=1; $i -le $job.series_count; $i++) {
        $hex = $job.colors[($i-1)%$job.colors.Count].TrimStart('#')
        $r = [Convert]::ToInt32($hex.Substring(0,2),16)
        $g = [Convert]::ToInt32($hex.Substring(2,2),16)
        $b = [Convert]::ToInt32($hex.Substring(4,2),16)
        $dataset = '%[%Z,#' + $i + ']'
        Run-LabTalk ('set ' + $dataset + ' -c color(' + $r + ',' + $g + ',' + $b + '); set ' + $dataset + ' -w 650;')
    }
    $low = ([double]$job.x_limits[0]).ToString('R',[Globalization.CultureInfo]::InvariantCulture)
    $high = ([double]$job.x_limits[1]).ToString('R',[Globalization.CultureInfo]::InvariantCulture)
    Run-LabTalk ('layer.x.from=' + $low + '; layer.x.to=' + $high + ';')
    Run-LabTalk ('label -xb ' + $job.x_label + '; label -yl ' + $job.y_label + ';')
    Run-LabTalk 'legend -r;'
    if (-not $origin.Save($project)) { throw 'Origin failed to save the project.' }
    Run-LabTalk '@sow=1;'
    Run-LabTalk ('save -i "' + $graphFile + '";')
    Run-LabTalk ('expGraph type:=png filename:="preview" path:="' + $folder + '" overwrite:=replace;')

    if (-not $origin.NewProject() -or -not $origin.Load($project)) { throw 'Saved project could not be reopened.' }
    Check-Table $book
    Run-LabTalk ('win -a ' + $graph + ';')
    Run-LabTalk '%Z=""; layer -c;'
    $projectPlots = Get-LabTalk 'count'
    if ($projectPlots -ne $job.series_count) { throw "Reopened graph plot count differs: $projectPlots" }
    # Edit a native curve property in memory, without changing the delivered project.
    Run-LabTalk 'set %[%Z,#1] -w 2000; get %[%Z,#1] -w NativeWidth;'
    if ((Get-LabTalk 'NativeWidth') -ne 2000) { throw 'Native plot edit verification failed.' }
    if (-not $origin.NewProject()) { throw 'Could not isolate the graph-file check.' }
    Run-LabTalk ('doc -a "' + $graphFile + '";')
    Check-Table $book
    Run-LabTalk '%Z=""; layer -c;'
    $graphPlots = Get-LabTalk 'count'
    if ($graphPlots -ne $job.series_count) { throw 'Standalone graph plot count differs.' }
    [pscustomobject]@{origin_version=$version; rows=$job.columns[0].Count; series=$job.series_count;
        worksheet_roundtrip=$true; native_curve_edit=$true; standalone_graph=$true;
        project_plot_count=$projectPlots; graph_plot_count=$graphPlots} |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $folder 'verification.json') -Encoding UTF8
} finally {
    if ($null -ne $origin) {
        $origin.Exit() | Out-Null
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($origin)
    }
}
