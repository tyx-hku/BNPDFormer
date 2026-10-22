$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$out = Join-Path $root 'figures'
$ppt = New-Object -ComObject PowerPoint.Application
$deck = $ppt.Presentations.Add(0)
$deck.PageSetup.SlideWidth = 900
$deck.PageSetup.SlideHeight = 1080
$s = $deck.Slides.Add(1,12)
function RGB($hex) {
    $h=$hex.TrimStart('#'); return [int]::Parse($h.Substring(0,2),'HexNumber') + 256*[int]::Parse($h.Substring(2,2),'HexNumber') + 65536*[int]::Parse($h.Substring(4,2),'HexNumber')
}
$ink='243D50'; $blue='3D6EB4'; $cyan='A6DCED'; $gold='FCB84D'; $red='CB001C'; $orange='F26121'
function Rect($x,$y,$w,$h,$fill,$edge='none') {
    $sh=$s.Shapes.AddShape(1,$x,$y,$w,$h)
    $sh.Fill.ForeColor.RGB=RGB $fill
    if($edge -eq 'none'){$sh.Line.Visible=0}else{$sh.Line.ForeColor.RGB=RGB $edge; $sh.Line.Weight=.8}
    return $sh
}
function Txt($x,$y,$w,$h,$str,$size=16,$bold=$false,$align=1,$color=$ink) {
    $t=$s.Shapes.AddTextbox(1,$x,$y,$w,$h)
    $t.TextFrame.MarginLeft=0; $t.TextFrame.MarginRight=0
    $t.TextFrame.MarginTop=0; $t.TextFrame.MarginBottom=0
    $t.TextFrame.WordWrap=-1
    $t.TextFrame.TextRange.Text=$str
    $t.TextFrame.TextRange.Font.Name='Times New Roman'
    $t.TextFrame.TextRange.Font.Size=[int]$size
    $t.TextFrame.TextRange.Font.Bold=[int]$bold*-1
    $t.TextFrame.TextRange.Font.Color.RGB=RGB $color
    $t.TextFrame.TextRange.ParagraphFormat.Alignment=$align
    return $t
}
function Line($x1,$y1,$x2,$y2,$color=$blue,$weight=1.2,$arrow=$false) {
    $l=$s.Shapes.AddLine($x1,$y1,$x2,$y2)
    $l.Line.ForeColor.RGB=RGB $color; $l.Line.Weight=[double]$weight
    if($arrow){$l.Line.EndArrowheadStyle=3}
    return $l
}
function Dot($x,$y,$r,$label,$color,$size=15,$textcolor=$ink) {
    $d=$s.Shapes.AddShape(9,($x-$r),($y-$r),($r*2),($r*2))
    $d.Fill.ForeColor.RGB=RGB $color; $d.Line.Visible=0
    $d.TextFrame.MarginLeft=0; $d.TextFrame.MarginRight=0
    $d.TextFrame.MarginTop=0; $d.TextFrame.MarginBottom=0
    $d.TextFrame.VerticalAnchor=3
    $d.TextFrame.TextRange.Text=[string]$label
    $d.TextFrame.TextRange.Font.Name='Times New Roman'
    $d.TextFrame.TextRange.Font.Size=[int]$size
    $d.TextFrame.TextRange.Font.Bold=-1
    $d.TextFrame.TextRange.Font.Color.RGB=RGB $textcolor
    $d.TextFrame.TextRange.ParagraphFormat.Alignment=2
    return $d
}
function Header($x,$y,$w,$title,$fill) {
    $null=Rect $x $y $w 27 $fill
    $null=Txt ($x+6) ($y+3) ($w-12) 23 $title 17 $true 2
}
function Picture($file,$x,$y,$w,$h,$left=0,$top=0,$right=1,$bottom=1) {
    $pic=$s.Shapes.AddPicture((Join-Path $root $file),0,-1,$x,$y,$w,$h)
    $crop=$pic.PictureFormat.Crop
    $crop.ShapeWidth=[double]$w; $crop.ShapeHeight=[double]$h
    $crop.PictureWidth=[double]($w/($right-$left)); $crop.PictureHeight=[double]($h/($bottom-$top))
    $crop.PictureOffsetX=[double]($crop.PictureWidth*(.5-$left)-$w/2)
    $crop.PictureOffsetY=[double]($crop.PictureHeight*(.5-$top)-$h/2)
    return $pic
}

# Match the supplied reference: environment montage, task list, graph and legend.
$null=Rect 8 8 884 1064 'FFFFFF' '8B9DAA'
$null=Rect 9 9 882 310 'F1F4F6'
Header 9 9 882 'Part 1: Production environment and entities' 'E7EEF3'
$null=Picture 'figures/camera_views/env_screen_shot.png' 15 42 425 271 0 .18 .48 .94
$null=Picture 'figures/camera_views/camera_num08_workbench.jpg' 447 42 197 120
$null=Picture 'figures/camera_views/camera_num00_rotaryPipeAutomaticWeldingMachine_part_01_station.jpg' 447 181 197 114
$null=Rect 447 147 197 23 'FFF2C7'
$null=Txt 449 149 193 21 '3. Shared workbenches' 15 $true 2
$null=Rect 447 290 197 23 'FFF2C7'
$null=Txt 449 292 193 21 '5. Rotary welding stations' 15 $true 2
$null=Rect 652 42 232 271 'DDEFF7'
$legend=@('CNC pipe cutting machine','Pipe grooving machine','Shared workbenches','Root-welding robot','Rotary welding machine','Workers','Transport robots','Overhead gantries','Storage / buffer areas')
for($i=0;$i -lt 9;$i++) {
    $null=Dot 667 (59+$i*27.4) 9 ($i+1) $cyan 13
    $null=Txt 682 (49+$i*27.4) 198 25 $legend[$i] 14.2
}
# Native, independently editable image labels and leader lines.
$pins=@(@(.265,.65,'1',-12,-28),@(.388,.65,'2',9,-30),@(.255,.365,'3',0,-23),@(.423,.31,'4',0,-24),@(.10,.65,'5',0,-26),@(.214,.764,'7',35,0),@(.32,.59,'8',0,-22),@(.31,.38,'9',18,16))
foreach($p in $pins){
    $px=15+425*$p[0]/.48; $py=42+271*($p[1]-.18)/.76
    $cx=$px+$p[3]; $cy=$py+$p[4]
    $null=Line $px $py $cx $cy 'FFFFFF' 1.4
    $null=Dot $cx $cy 10 $p[2] $cyan 14
}

$null=Rect 9 323 882 397 'FFF0E5'
Header 9 323 882 'Part 2: Manufacturing tasks and handling subtasks' 'FBE3D0'
$tasks=@(
 @('Pipe cutting','Raw pipe is delivered to the CNC cutting station and cut to the required geometry.'),
 @('Pipe grooving','The cut pipe moves to the grooving station for end preparation.'),
 @('Assembly and spot welding','Pipe, flange and elbow are supplied to a workbench and joined into a pipe assembly.'),
 @('Argon-arc root welding','The assembled pipe moves to the welding robot for root-pass welding.'),
 @('MIG surface welding','The pipe moves to a rotary welding station for surface welding.'),
 @('Rust-proof painting','The welded pipe returns to the workbench resource family for final rust-proof treatment.'),
 @('Material transfer within a zone','Worker approaches material → gantry picks up → gantry transfers → worker assists placement.'),
 @('Material transfer across zones','Source gantry loads robot → robot travels → destination gantry unloads → material reaches station.')
)
for($i=0;$i -lt $tasks.Count;$i++){
    $y=356+$i*44
    $null=Dot 29 ($y+9) 10 ($i+1) $red 14 'FFFFFF'
    $null=Txt 47 ($y-2) 829 22 $tasks[$i][0] 16 $true
    $null=Txt 47 ($y+19) 829 22 $tasks[$i][1] 14.5
}

# Lower left: representative subgraph with actual graph.py edges.
$null=Rect 9 724 539 347 'FFF7DB'
Header 9 724 539 'Part 3: Multi-entity dependency graph' 'FFF2C7'
$null=Rect 552 724 339 347 'E8F1FC'
Header 552 724 339 'Part 4: Workstation node information' 'D9E7FA'
$mx=@(46,120,194,268,342,416,510); $my=@(858,883,858,883,858,883,858)
# Representatives of agent families connect to all stations in the implemented graph.
$agents=@(@(93,789,'G',$gold),@(278,789,'H',$orange),@(463,789,'R',$cyan))
foreach($ag in $agents){for($i=0;$i -lt 7;$i++){$null=Line $ag[0] ($ag[1]+12) $mx[$i] ($my[$i]-13) 'B4BCC0' .65}}
for($i=0;$i -lt 6;$i++){$null=Line ($mx[$i]+13) $my[$i] ($mx[$i+1]-13) $my[$i+1] $blue 2}
$buffers=@(@(93,963,'B1',@(0,1)),@(278,963,'B2',@(0,1,2)),@(463,963,'B3',@(2,3,4,5,6)))
foreach($bf in $buffers){foreach($i in $bf[3]){$null=Line $bf[0] ($bf[1]-13) $mx[$i] ($my[$i]+13) 'D5AB52' .85}}
foreach($ag in $agents){$null=Dot $ag[0] $ag[1] 14 $ag[2] $ag[3] 16}
for($i=0;$i -lt 7;$i++){$null=Dot $mx[$i] $my[$i] 14 ($i+1) $blue 16 'FFFFFF'}
foreach($bf in $buffers){$null=Dot $bf[0] $bf[1] 14 $bf[2] $gold 13}
$null=Txt 24 757 507 21 'G: gantry       H: worker       R: transport robot' 14 $false 2
$null=Txt 24 985 507 20 'B1: BlackStorage   B2: GroundStorage   B3: YellowStorage' 12.5 $false 2
$null=Txt 24 1012 507 45 "Representative undirected subgraph. Repeated resource nodes,`nwithin-type links and self-loops are omitted." 13 $false 2
$info=@('CNC cutting station','Grooving station','Workbench 0','Workbench 1','Robotic root-welding station','Rotary welding station 0','Rotary welding station 1')
for($i=0;$i -lt 7;$i++){
    $y=765+$i*30
    $null=Dot 574 $y 10 ($i+1) $cyan 14
    $null=Txt 591 ($y-10) 290 25 $info[$i] 15.2
}
$null=Line 564 974 878 974 'A9BED6' .8
$null=Txt 565 984 312 52 "38 nodes: 7 workstations, 4 gantries,`n4 transport robots, 5 workers, 18 buffers" 14
$null=Txt 565 1030 310 31 'Steps 3 and 6 share the workbench family.' 13

$notes='Sources: _isaac_factory/source/isaaclab_tasks/isaaclab_tasks/direct/hc_factory/env_asset_cfg/cfg_process_task_gallery.py; cfg_process_subtask_gallery.py; PDFormer/factory_bn/graph.py; _isaac_factory/10.实验说明.md. Photo: figures/camera_views/env_screen_shot.png and supplied camera views. Graph uses seven machine nodes and one representative per agent / buffer family. Edges match graph.py; it does not depict a dispatch schedule. All diagram shapes, labels and connectors are editable native PowerPoint objects. Photos remain embedded raster objects with native editable crop settings.'
$s.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text=$notes
$target=Join-Path $out 'fig_factory_process_entities_editable.pptx'
$deck.SaveAs($target,24)
$s.Export((Join-Path $out 'fig_factory_process_entities_redesign.png'),'PNG',1800,2160)
$deck.SaveAs((Join-Path $out 'fig_factory_process_entities_redesign.pdf'),32)
Write-Output "Saved $target; slide objects: $($s.Shapes.Count)"
$deck.Close()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($s) | Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($deck) | Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) | Out-Null


