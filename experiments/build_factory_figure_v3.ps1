$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$out = Join-Path $root 'figures'
$ppt = New-Object -ComObject PowerPoint.Application
$deck = $ppt.Presentations.Add(0)
$deck.PageSetup.SlideWidth = 1200
$deck.PageSetup.SlideHeight = 1030
$s = $deck.Slides.Add(1,12)
function RGB($hex) {
    $h=$hex.TrimStart('#'); return [int]::Parse($h.Substring(0,2),'HexNumber') + 256*[int]::Parse($h.Substring(2,2),'HexNumber') + 65536*[int]::Parse($h.Substring(4,2),'HexNumber')
}
$ink='243D50'; $blue='5094D5'; $cyan='ABD8E5'; $gold='E8B86C'; $red='D15354'; $orange='F9AD95'
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

function Section($x,$y,$w,$h,$label,$color,$tint) {
    $f=Rect $x $y $w $h $tint $color
    $f.Line.DashStyle=4
    $null=Txt ($x+12) ($y+8) ($w-24) 27 $label 20 $true 1 $ink
}

# Palette supplied by the user: muted red / lavender / slate / blue / ochre.
Section 10 10 1180 386 '(a)  Digital-twin production line' '5E82A2' 'ECF6FD'
$null=Picture 'figures/camera_views/env_screen_shot.png' 22 52 760 328 0 .20 .68 .93
$null=Picture 'figures/camera_views/camera_num04_groovingMachineLarge_part01_large_fixed_base.jpg' 802 52 376 250.67
$null=Rect 802 303 376 25 'ABD8E5'
$null=Txt 808 305 364 22 'M2   Large pipe roll-grooving machine' 16 $true 2
$null=Txt 804 342 373 24 'Pipe-end groove forming' 18 $true 2
$null=Txt 804 369 373 22 'Cutting → roll grooving → assembly' 15 $false 2
$pins=@(@(.388,.65,'M1',0,-35),@(.585,.65,'M2',23,-35),@(.255,.365,'M3/4',-8,-26),@(.265,.65,'M5',0,-35),@(.10,.65,'M6/7',0,-35))
foreach($p in $pins){
    $px=22+760*$p[0]/.68
    # Crop y spans .20 to .93.
    $py=52+328*($p[1]-.20)/.73
    $cx=$px+$p[3]; $cy=$py+$p[4]
    $null=Line $px $py $cx $cy 'FFFFFF' 1.8
    $labelWidth=48
    $null=Rect ($cx-24) ($cy-13) $labelWidth 26 $(if($p[2] -eq 'M2'){'D15354'}else{'5E82A2'})
    $null=Txt ($cx-23) ($cy-10) 46 23 $p[2] 15 $true 2 'FFFFFF'
}

Section 10 410 1180 263 '(b)  Manufacturing route' '8887CB' 'FFFFFF'
$photos=@('camera_num02_rollerbedCNCPipeIntersectionCuttingMachine_part01_station.jpg','camera_num04_groovingMachineLarge_part01_large_fixed_base.jpg','camera_num08_workbench.jpg','camera_num01_weldingRobot_part02_robot_arm_and_base.jpg','camera_num00_rotaryPipeAutomaticWeldingMachine_part_01_station.jpg','camera_num08_workbench.jpg')
$names=@('Pipe cutting','Roll grooving','Assembly / spot weld','Argon-arc root weld','MIG surface weld','Rust-proof painting')
$ids=@('M1','M2','M3 / M4','M5','M6 / M7','M3 / M4')
$cols=@('ABD8E5','F9AD95','BFC7E5','ABD8E5','E8B86C','BFC7E5')
for($i=0;$i -lt 6;$i++){
    $x=24+196*$i
    $null=Picture ('figures/camera_views/'+$photos[$i]) $x 452 170 113.33
    $null=Rect $x 566 170 51 $cols[$i]
    $null=Txt ($x+3) 570 164 23 $names[$i] 16 $true 2
    $null=Txt ($x+3) 594 164 22 $ids[$i] 14 $false 2
    $null=Dot ($x+13) 464 11 ($i+1) '5E82A2' 14 'FFFFFF'
    if($i -lt 5){$null=Line ($x+173) 507 ($x+192) 507 'D15354' 2 $true}
}
$null=Txt 26 631 1150 26 'Raw pipe → cut / grooved pipe + flange + elbow → pipe assembly → welded pipe → finished product' 17 $false 2

Section 10 687 505 332 '(c)  Material handling and resource sharing' 'D15354' 'FEEEED'
$null=Txt 26 728 473 24 'Within one gantry zone' 17 $true
foreach($item in @(@(26,'Pickup'),@(191,'Gantry transfer'),@(356,'Placement'))){
    $null=Rect $item[0] 761 142 40 'F9AD95'
    $null=Txt ($item[0]+3) 771 136 22 $item[1] 16 $true 2
}
$null=Line 170 781 188 781 '5E82A2' 1.6 $true
$null=Line 335 781 353 781 '5E82A2' 1.6 $true
$null=Txt 26 815 473 24 'Across gantry zones' 17 $true
foreach($item in @(@(26,'Source gantry'),@(191,'Transport robot'),@(356,'Target gantry'))){
    $null=Rect $item[0] 849 142 40 $(if($item[0] -eq 191){'ABD8E5'}else{'E8B86C'})
    $null=Txt ($item[0]+3) 859 136 22 $item[1] 16 $true 2
}
$null=Line 170 869 188 869 '5E82A2' 1.6 $true
$null=Line 335 869 353 869 '5E82A2' 1.6 $true
$null=Txt 26 909 473 30 'Workers assist loading, control and placement.' 16
$null=Rect 26 951 473 47 'BFC7E5'
$null=Txt 34 963 457 26 'Steps 3 and 6 reuse the two workbenches.' 17 $true 2

Section 529 687 661 332 '(d)  Multi-entity structural graph' '5094D5' 'ECF6FD'
# Representative induced subgraph, using graph.py topology.
$mx=@(559,658,757,856,955,1054,1153)
$my=@(849,872,849,872,849,872,849)
$agents=@(@(632,777,'G','E8B86C'),@(858,777,'H','8887CB'),@(1084,777,'R','ABD8E5'))
foreach($ag in $agents){for($i=0;$i -lt 7;$i++){$null=Line $ag[0] ($ag[1]+13) $mx[$i] ($my[$i]-15) 'BFC7E5' .75}}
for($i=0;$i -lt 6;$i++){$null=Line ($mx[$i]+16) $my[$i] ($mx[$i+1]-16) $my[$i+1] '5094D5' 2}
$buffers=@(@(632,941,'B1',@(0,1)),@(858,941,'B2',@(0,1,2)),@(1084,941,'B3',@(2,3,4,5,6)))
foreach($bf in $buffers){foreach($i in $bf[3]){$null=Line $bf[0] ($bf[1]-14) $mx[$i] ($my[$i]+15) 'E8B86C' 1}}
foreach($ag in $agents){$null=Dot $ag[0] $ag[1] 15 $ag[2] $ag[3] 17}
for($i=0;$i -lt 7;$i++){$null=Dot $mx[$i] $my[$i] 17 ('M'+($i+1)) '5094D5' 14 'FFFFFF'}
foreach($bf in $buffers){$null=Dot $bf[0] $bf[1] 15 $bf[2] 'E8B86C' 14}
$null=Txt 547 727 625 24 'G: gantry (4)     H: worker (5)     R: transport robot (4)' 15 $false 2
$null=Txt 545 966 630 21 'B1: BlackStorage     B2: GroundStorage     B3: YellowStorage' 13 $false 2
$null=Txt 545 990 630 22 '38 nodes in total; representative nodes shown; self / within-type links omitted.' 13 $false 2

$s.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text='Evidence: cfg_machine.py lines 209-215 binds num04_groovingMachineLarge to pipe_grooving and logistic_for_pipe_grooving; lines 257-262 has none for num05_groovingMachineSmall. cfg_process_task_gallery.py defines the six-step sequence. cfg_process_subtask_gallery.py lines 190-230 routes input and process tasks to num04. cfg_gantry_zone.py assigns num04 to zone 2. factory_bn/graph.py defines the seven machine nodes, chain and resource affinities. M1 cutting, M2 large grooving, M3/4 workbenches, M5 root-welding robot, M6/7 rotary surface welders. Camera-specific images independently verify equipment identities; prior figure misplaced cutting and root welding and cropped out the active grooving machine. Graph edges are structural and undirected, not the production routing. Source images: figures/camera_views/. Palette is from user supplied image. Numbers in agent labels denote full-graph counts; B1-3 are representative buffers, not all 18 buffer nodes.'
$target=Join-Path $out 'fig_factory_process_entities_v3.pptx'
$deck.SaveAs($target,24)
$s.Export((Join-Path $out 'fig_factory_process_entities_v3.png'),'PNG',2400,2060)
$deck.SaveAs((Join-Path $out 'fig_factory_process_entities_v3.pdf'),32)
Write-Output "Saved $target; slide objects: $($s.Shapes.Count)"
$deck.Close()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($s) | Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($deck) | Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) | Out-Null


