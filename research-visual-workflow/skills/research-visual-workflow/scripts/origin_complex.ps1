param([Parameter(Mandatory=$true)][string]$JobPath)
$ErrorActionPreference = 'Stop'
$job = Get-Content -LiteralPath $JobPath -Raw -Encoding UTF8 | ConvertFrom-Json
$folder = Split-Path -Parent $JobPath
$project = Join-Path $folder 'figure.opj'
$graphFile = Join-Path $folder 'figure.ogg'
$missing = -1.23456789E-300
$invariant = [Globalization.CultureInfo]::InvariantCulture
$getProperty = [Reflection.BindingFlags]::GetProperty

function Run-LT([string]$code) {
    if (-not $origin.Execute($code)) { throw "Origin could not execute: $code" }
}

function Read-LT([string]$expression) {
    Run-LT ('ComplexQuery=' + $expression + ';')
    return $origin.GetType().InvokeMember('LTVar',$getProperty,$null,$origin,@('ComplexQuery'))
}

function Read-Text([string]$name) {
    return $origin.GetType().InvokeMember('LTStr',$getProperty,$null,$origin,@($name))
}

function Fmt([double]$value) { return $value.ToString('R',$invariant) }

function RGB([string]$hex) {
    $hex = $hex.TrimStart('#')
    $r = [Convert]::ToInt32($hex.Substring(0,2),16)
    $g = [Convert]::ToInt32($hex.Substring(2,2),16)
    $b = [Convert]::ToInt32($hex.Substring(4,2),16)
    return "color($r,$g,$b)"
}

function Set-Range([string]$axis,[double]$first,[double]$last) {
    Run-LT ('layer.' + $axis + '.from=' + (Fmt $first) + '; layer.' + $axis + '.to=' + (Fmt $last) + ';')
}

function Build-Series($p) {
    $book = $origin.CreatePage(2,$p.book,'Origin',2)
    if ($book -cne $p.book) { throw 'Could not create the requested worksheet.' }
    $n = $p.columns.Count
    Run-LT ('wks.ncols=' + $n + '; wks.col1.type=4;')
    if ($p.categorical) { Run-LT 'wks.col1.format=2;' }
    for ($col=0; $col -lt $n; $col++) {
        if ($col -eq 0 -and $p.categorical) {
            $values = [string[]]$p.columns[$col]
        } else {
            $values = [double[]]@($p.columns[$col] | ForEach-Object { if ($null -eq $_) {$missing} else {[double]$_} })
        }
        if (-not $origin.PutWorksheet($book,$values,0,$col)) { throw 'Could not write a worksheet column.' }
        Run-LT ('wks.col' + ($col+1) + '.lname$="' + $p.labels[$col] + '";')
    }
    if ($p.categorical) { Run-LT 'wks.col1.iscat=1; wks.col1.categorical.sort=0;' }
    foreach ($pair in $p.error_columns) { Run-LT ('wks.col' + $pair[1] + '.type=3;') }
    $plot = @{ 'grouped-bar'='203 column'; 'stacked-bar'='213 STACKCOLUMN'; line='200 line'; scatter='201 scatter' }[$p.kind]
    Run-LT ('worksheet -s 1 1 ' + $n + ' -1; worksheet -p ' + $plot + ';')
    if ($p.categorical) {
        Set-Range 'x' 0.5 ($p.columns[0].Count + 0.5)
        Run-LT 'layer.x.inc=1;'
    }
    if ($null -ne $p.y_range) { Set-Range 'y' $p.y_range[0] $p.y_range[1] }
    if ($job.theme -ne 'default' -and -not $p.categorical) {
        Run-LT 'layer -gu;'
        for ($i=0; $i -lt $p.value_columns.Count; $i++) {
            $dataset = $book + '_' + [char](64 + $p.value_columns[$i])
            $color = RGB $job.colors[$i]
            Run-LT ('set ' + $dataset + ' -c ' + $color + '; set ' + $dataset + ' -w 650;')
        }
    }
    Run-LT ('label -xb ' + $p.x_label + '; label -yl ' + $p.y_label + ';')
}

function Matrix-Values($p) {
    $rows = $p.matrix.Count
    $cols = $p.matrix[0].Count
    $cells = New-Object 'double[,]' $rows,$cols
    for ($r=0; $r -lt $rows; $r++) {
        for ($c=0; $c -lt $cols; $c++) {
            $v = $p.matrix[$r][$c]
            $cells[$r,$c] = if ($null -eq $v) {$missing} else {[double]$v}
        }
    }
    return ,$cells
}

function Build-Heatmap($p) {
    $book = $origin.CreatePage(1,$p.book,'Origin',2)
    if ($book -cne $p.book) { throw 'Could not create the requested matrix.' }
    $cells = Matrix-Values $p
    Run-LT ('mdim rows:=' + $cells.GetLength(0) + ' cols:=' + $cells.GetLength(1) +
            ' x1:=' + (Fmt $p.x[0]) + ' x2:=' + (Fmt $p.x[1]) + ' y1:=' + (Fmt $p.y[0]) + ' y2:=' + (Fmt $p.y[1]) + ';')
    if (-not $origin.PutMatrix($book,$cells)) { throw 'Could not write the matrix.' }
    Run-LT 'plotm im:=<active> plot:=220 ogl:=[<new template:=IMAGE>];'
    Set-Range 'x' ($p.x[0] - $p.x[2]/2) ($p.x[1] + $p.x[2]/2)
    Set-Range 'y' ($p.y[0] - $p.y[2]/2) ($p.y[1] + $p.y[2]/2)
    Run-LT 'layer.y.reverse=1;'
    if ($cells.GetLength(1) -le 10) { Run-LT ('layer.x.inc=' + (Fmt $p.x[2]) + ';') }
    if ($cells.GetLength(0) -le 10) { Run-LT ('layer.y.inc=' + (Fmt $p.y[2]) + ';') }
    Run-LT ('layer.cmap.zmin=' + (Fmt $p.scale[0]) + '; layer.cmap.zmax=' + (Fmt $p.scale[1]) +
            '; layer.cmap.numMajorLevels=10; layer.cmap.numMinorLevels=0; layer.cmap.setLevels(1);')
    $levels = [int](Read-LT 'layer.cmap.numColors')
    if ($levels -lt 2) { throw 'Origin did not configure the color levels.' }
    $anchors = if ($p.palette -eq 'diverging') {
        @(@(38,95,156),@(248,247,241),@(162,53,49))
    } elseif ($job.theme -eq 'default') {
        @(@(239,239,239),@(51,51,51))
    } elseif ($job.theme -eq 'clean') {
        @(@(238,240,245),@(53,74,119))
    } else {
        @(@(239,246,245),@(13,88,99))
    }
    for ($i=1; $i -le $levels; $i++) {
        $where = ($i-1)*($anchors.Count-1)/($levels-1)
        $left = [math]::Min([int][math]::Floor($where),$anchors.Count-2)
        $f = $where-$left
        $channels = for ($j=0; $j -lt 3; $j++) {
            [int][math]::Round($anchors[$left][$j]*(1-$f)+$anchors[$left+1][$j]*$f)
        }
        Run-LT ('layer.cmap.color' + $i + '=color(' + ($channels -join ',') + ');')
    }
    Run-LT 'layer.cmap.colorMiss=color(185,185,185); layer.cmap.colorBelow=color(185,185,185); layer.cmap.updateScale();'
    Run-LT ('label -yl ' + $p.y_label + '; YL.fsize=14; label -p 2 3 -n MatrixX ' + $p.x_label + '; MatrixX.fsize=14;')
    $absent = 0
    for ($r=0; $r -lt $cells.GetLength(0); $r++) {
        for ($c=0; $c -lt $cells.GetLength(1); $c++) {
            if ($null -eq $p.matrix[$r][$c]) {
                $absent++
                $tag = 'Missing' + $absent
                Run-LT ('label -a ' + (Fmt ($p.x[0]+$c*$p.x[2])) + ' ' + (Fmt ($p.y[0]+$r*$p.y[2])) + ' -n ' + $tag + ' NA; ' + $tag + '.background=1;')
            }
        }
    }
}

function Finish-Layout($p,$index) {
    Run-LT ('page.active=' + ($index+1) + ';')
    if ($job.panels.Count -gt 1) {
        $colSpan = 100.0/$job.columns
        $rowSpan = 100.0/$job.rows
        $left = ($index % $job.columns)*$colSpan + 0.18*$colSpan
        $top = [math]::Floor($index/$job.columns)*$rowSpan + 0.14*$rowSpan
        Run-LT ('layer.unit=1; layer.left=' + (Fmt $left) + '; layer.top=' + (Fmt $top) +
                '; layer.width=' + (Fmt (0.70*$colSpan)) + '; layer.height=' + (Fmt (0.64*$rowSpan)) + ';')
    }
    if ($p.kind -eq 'heatmap') {
        Run-LT 'layer.unit=1; layer.left=layer.left+layer.width*0.10; layer.width=layer.width*0.74; spectrum;'
        Run-LT ('SPECTRUM1.width=page.width*' + (Fmt (0.12/$job.columns)) + '; SPECTRUM1.height=page.height*layer.height*0.72/100; ' +
                'SPECTRUM1.left=page.width*(layer.left+layer.width+1.5)/100; SPECTRUM1.top=page.height*(layer.top+layer.height*0.12)/100;')
        Run-LT ('label -p 105 2 -n MatrixZ ' + $p.z_label + '; MatrixZ.fsize=13;')
    } else {
        $entries = for ($i=0; $i -lt $p.value_columns.Count; $i++) {
            '\l(' + ($i+1) + ') ' + $p.labels[$p.value_columns[$i]-1]
        }
        Run-LT ('Legend.text$="' + ($entries -join '%(CRLF)') + '"; Legend.fsize=15; Legend.background=0;')
        Run-LT 'Legend.x=layer.x.from+Legend.dx/2+(layer.x.to-layer.x.from)*0.025; Legend.y=layer.y.to-Legend.dy/2-(layer.y.to-layer.y.from)*0.13;'
    }
    if ($job.panels.Count -gt 1) {
        $title = if ($p.kind -eq 'heatmap') { $p.title + ' / ' + $p.x_label } else { $p.title }
        if ($p.kind -eq 'heatmap') { Run-LT 'label -r MatrixX;' }
        Run-LT ('label -p 2 2 -n PanelTag \b(' + [char](97+$index) + ') ' + $title + '; PanelTag.fsize=15;')
    }
}

function Check-Number($actual,$expected) {
    if ($null -eq $expected) {
        if ($null -ne $actual -and [double]$actual -ne $missing) { throw 'A missing cell changed.' }
    } elseif ($null -eq $actual -or [math]::Abs([double]$actual-[double]$expected) -gt 1e-12*[math]::Max(1,[math]::Abs([double]$expected))) {
        throw "A numeric value changed: actual $actual expected $expected."
    }
}

function Check-Data($p) {
    if ($p.kind -eq 'heatmap') {
        $rows = $p.matrix.Count
        $cols = $p.matrix[0].Count
        $data = $origin.GetMatrix($p.book)
    } else {
        $rows = $p.columns[0].Count
        $cols = $p.columns.Count
        $data = $origin.GetWorksheet($p.book,0,0,$rows-1,$cols-1)
    }
    if ($null -eq $data -or $data.Rank -ne 2 -or $data.GetLength(0) -ne $rows -or $data.GetLength(1) -ne $cols) {
        throw ('Data dimensions differ for ' + $p.book + '.')
    }
    $rb = $data.GetLowerBound(0)
    $cb = $data.GetLowerBound(1)
    for ($r=0; $r -lt $rows; $r++) {
        for ($c=0; $c -lt $cols; $c++) {
            $v = $data[($r+$rb),($c+$cb)]
            if ($p.kind -eq 'heatmap') { Check-Number $v $p.matrix[$r][$c] }
            elseif ($c -eq 0 -and $p.categorical) {
                if ($v -cne $p.columns[$c][$r]) { throw 'A category label or its order changed.' }
            } else { Check-Number $v $p.columns[$c][$r] }
        }
    }
}

function Check-Graph {
    if ((Read-LT 'page.nlayers') -ne $job.panels.Count) { throw 'Reopened graph layer count differs.' }
    for ($i=0; $i -lt $job.panels.Count; $i++) {
        $p = $job.panels[$i]
        Run-LT ('page.active=' + ($i+1) + '; %Z=""; layer -c;')
        if ((Read-LT 'count') -ne $p.expected_plots) { throw ('Reopened plot count differs for ' + $p.book) }
        $names = Read-Text '%Z'
        if ($p.kind -eq 'heatmap') {
            if ($names -notmatch ('\(' + $p.book + '\)')) { throw 'Heatmap lost its matrix link.' }
            Check-Number (Read-LT 'layer.cmap.zmin') $p.scale[0]
            Check-Number (Read-LT 'layer.cmap.zmax') $p.scale[1]
            Check-Number (Read-LT 'layer.x.from') ($p.x[0] - $p.x[2]/2)
            Check-Number (Read-LT 'layer.x.to') ($p.x[1] + $p.x[2]/2)
            Check-Number (Read-LT 'layer.y.from') ($p.y[0] - $p.y[2]/2)
            Check-Number (Read-LT 'layer.y.to') ($p.y[1] + $p.y[2]/2)
            Check-Number (Read-LT 'layer.y.reverse') 1
        } else {
            Run-LT 'NativeMain=0; doc -e DY { NativeMain=NativeMain+1; };'
            if ((Read-LT 'NativeMain') -ne $p.value_columns.Count) { throw 'The primary plots and error bars differ from the specification.' }
            foreach ($column in ($p.value_columns + @($p.error_columns | ForEach-Object { $_[1] }))) {
                $dataset = $p.book + '_' + [char](64 + $column)
                if ($names -notmatch ('\(' + $dataset + '\)')) { throw ('Missing plot link ' + $dataset) }
            }
        }
        Check-Data $p
    }
}

function Check-Edit($p) {
    if ($p.kind -eq 'heatmap') {
        $cells = Matrix-Values $p
        $next = 0.5*$p.scale[0]+0.5*$p.scale[1]
        if ($next -eq $cells[0,0]) { $next = 0.75*$p.scale[0]+0.25*$p.scale[1] }
        $cells[0,0] = $next
        if (-not $origin.PutMatrix($p.book,$cells)) { throw 'Native matrix edit failed.' }
        $actual = $origin.GetMatrix($p.book)
        Check-Number $actual[$actual.GetLowerBound(0),$actual.GetLowerBound(1)] $cells[0,0]
    } else {
        $edits = @($p.value_columns[0]) + @($p.error_columns | ForEach-Object { $_[1] })
        foreach ($index in $edits) {
            $column = $index-1
            $next = if ($p.columns[$column][0] -eq 0.875) {0.625} else {0.875}
            if (-not $origin.PutWorksheet($p.book,[double[]]@($next),0,$column)) { throw 'Native worksheet edit failed.' }
            $actual = $origin.GetWorksheet($p.book,0,$column,0,$column)
            Check-Number $actual[$actual.GetLowerBound(0),$actual.GetLowerBound(1)] $next
        }
    }
}

$origin = New-Object -ComObject Origin.ApplicationSI
try {
    if (-not $origin.NewProject()) { throw 'Could not start a new Origin project.' }
    $version = Read-LT '@V'
    foreach ($p in $job.panels) {
        if ($p.kind -eq 'heatmap') { Build-Heatmap $p } else { Build-Series $p }
    }
    if ($job.panels.Count -gt 1) {
        Run-LT ('merge_graph option:=folder row:=' + $job.rows + ' col:=' + $job.columns + ' keep:=0;')
    }
    for ($i=0; $i -lt $job.panels.Count; $i++) { Finish-Layout $job.panels[$i] $i }
    $graph = Read-Text '%H'
    Check-Graph
    Run-LT 'page.active=1;'
    if (-not $origin.Save($project)) { throw 'Origin failed to save the project.' }
    Run-LT '@sow=1;'
    Run-LT ('save -i "' + $graphFile + '";')
    Run-LT ('expGraph type:=png filename:="preview" path:="' + $folder + '" overwrite:=replace;')
    if (-not $origin.NewProject() -or -not $origin.Load($project)) { throw 'Saved project could not be reopened.' }
    Run-LT ('win -a ' + $graph + ';')
    Check-Graph
    foreach ($p in $job.panels) { Check-Edit $p }
    if (-not $origin.NewProject()) { throw 'Could not isolate the graph-file check.' }
    Run-LT ('doc -a "' + $graphFile + '";')
    Check-Graph
    [pscustomobject]@{origin_version=$version; layers=$job.panels.Count;
        kinds=@($job.panels | ForEach-Object { $_.kind });
        plot_counts=@($job.panels | ForEach-Object { $_.expected_plots });
        data_roundtrip=$true; native_data_edit=$true; standalone_graph=$true} |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $folder 'verification.json') -Encoding UTF8
} finally {
    $origin.Exit() | Out-Null
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($origin)
}
