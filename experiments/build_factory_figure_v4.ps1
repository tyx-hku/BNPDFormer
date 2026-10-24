$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$out = Join-Path $root 'figures'
$ppt = New-Object -ComObject PowerPoint.Application
$deck = $ppt.Presentations.Add(0)
$deck.PageSetup.SlideWidth = 1200
$deck.PageSetup.SlideHeight = 1340
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

Section 10 10 1180 386 '(a)  Digital-twin production environment and entities' '5E82A2' 'ECF6FD'
$null=Picture 'figures/camera_views/env_screen_shot.png' 22 52 760 328 0 .20 .68 .93
$null=Txt 805 51 370 27 'Machine / workstation identifiers' 19 $true
$machineNames=@('M1   CNC pipe intersection cutting machine','M2   Large pipe roll-grooving machine','M3   Workbench 0','M4   Workbench 1','M5   Robotic root-welding station','M6   Rotary surface-welding station 0','M7   Rotary surface-welding station 1')
for($i=0;$i -lt 7;$i++){
    $null=Rect 801 (86+$i*33) 378 29 $(if($i%2 -eq 0){'FFFFFF'}else{'ECF6FD'})
    $null=Txt 809 (89+$i*33) 366 26 $machineNames[$i] 16 $false
}
$null=Line 805 326 1175 326 'BFC7E5' .9
$null=Txt 806 337 369 40 "M3 / M4 serve both spot welding and painting.`nAGV: automated guided vehicle." 15
$pins=@(@(.388,.65,'M1',0,-35),@(.585,.65,'M2',23,-35),@(.255,.365,'M3/4',-8,-26),@(.265,.65,'M5',0,-35),@(.10,.65,'M6/7',0,-35))
foreach($p in $pins){
    $px=22+760*$p[0]/.68; $py=52+328*($p[1]-.20)/.73
    $cx=$px+$p[3]; $cy=$py+$p[4]
    $null=Line $px $py $cx $cy 'FFFFFF' 1.8
    $null=Rect ($cx-24) ($cy-13) 48 26 '5E82A2'
    $null=Txt ($cx-23) ($cy-10) 46 23 $p[2] 15 $true 2 'FFFFFF'
}
# Label visible instances, not inferred positions or assignments.
$entityPins=@(
 @(.508,.363,'Human',-10,-37,'8887CB',65),
 @(.214,.764,'AGV',64,7,'ABD8E5',54),
 @(.11,.864,'Material',55,11,'F9AD95',79),
 @(.589,.35,'Buffer',-6,-30,'E8B86C',65),
 @(.321,.48,'Gantry',-65,9,'E8B86C',69)
)
foreach($p in $entityPins){
    $px=22+760*$p[0]/.68; $py=52+328*($p[1]-.20)/.73
    $cx=$px+$p[3]; $cy=$py+$p[4]; $w=$p[6]
    $null=Line $px $py $cx $cy 'FFFFFF' 1.8
    $null=Rect ($cx-$w/2) ($cy-12) $w 24 $p[5]
    $null=Txt ($cx-$w/2+2) ($cy-10) ($w-4) 22 $p[2] 15 $true 2
}

Section 10 410 1180 565 '(b)  Manufacturing stages (1–6) and shared handling subtasks (7–9)' 'D15354' 'FEEEED'
$tasks=@(
 @('1','Pipe cutting at M1','Deliver raw pipe to M1 → worker operates the cutting machine → cut pipe becomes available for transfer.'),
 @('2','Roll grooving at M2','Transfer the cut pipe to the large roll-grooving machine → worker operates M2 → grooved pipe proceeds to assembly.'),
 @('3','Assembly and spot welding at M3 / M4','Supply one pipe, one flange and one elbow → select a workbench → assemble and spot-weld → obtain a semi-finished pipe.'),
 @('4','Argon-arc root welding at M5','Deliver the semi-finished pipe to the welding robot → worker operates the station → perform root welding.'),
 @('5','MIG surface welding at M6 / M7','Transfer the root-welded pipe to a selected rotary welding station → perform surface welding → release it for painting.'),
 @('6','Rust-proof painting at M3 / M4','Return the welded pipe to a workbench → apply rust-proof treatment → produce the finished water pipe.'),
 @('7','Shared processing and outbound handling sequence','Worker approaches station → controls machine while it processes → waits for a free gantry → assists loading for outbound transfer.'),
 @('8','Material transfer within one gantry zone','Worker and gantry approach material → load onto gantry → carry to the destination → place at the target station or storage area.'),
 @('9','Material transfer across gantry zones','Source gantry loads an AGV → source gantry is released → AGV travels → a free destination gantry unloads and places the material.')
)
for($i=0;$i -lt $tasks.Count;$i++){
    $y=455+$i*56
    $null=Dot 34 ($y+10) 11 $tasks[$i][0] $(if($i -lt 6){'D15354'}else{'5E82A2'}) 15 'FFFFFF'
    $null=Txt 55 ($y-2) 1118 25 $tasks[$i][1] 19 $true
    $null=Txt 55 ($y+24) 1118 28 $tasks[$i][2] 17
}

# Keep v3 graph geometry and edges, then translate the complete group.
$graphStart=$s.Shapes.Count+1
Section 529 687 661 332 '(c)  Multi-entity structural graph' '5094D5' 'ECF6FD'
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
$null=Txt 547 727 625 24 'G: gantry (4)     H: human (5)     R: AGV (4)' 15 $false 2
$null=Txt 545 966 630 21 'B1: BlackStorage     B2: GroundStorage     B3: YellowStorage' 13 $false 2
$null=Txt 545 990 630 22 '38 nodes: 7 workstations + 4 gantries + 5 humans + 4 AGVs + 18 buffers.' 13 $false 2
$graphEnd=$s.Shapes.Count
for($j=$graphStart;$j -le $graphEnd;$j++){
    $sh=$s.Shapes.Item($j); $sh.Left=[single]($sh.Left-519); $sh.Top=[single]($sh.Top+303)
}
Section 685 990 505 332 'Graph interpretation' '5E82A2' 'FFFFFF'
$null=Line 701 1042 733 1042 '5094D5' 2
$null=Txt 743 1032 432 22 'Blue: workstation backbone links.' 16
$null=Line 701 1073 733 1073 'BFC7E5' 1.2
$null=Txt 743 1063 432 22 'Lavender: human / transport–station links.' 16
$null=Line 701 1104 733 1104 'E8B86C' 1.2
$null=Txt 743 1094 432 22 'Ochre: buffer–station affinities.' 16
$null=Txt 701 1133 473 47 'M1–M7 match the workstation list in (a). G, H, R and B1–B3 each represent one node of their resource family.' 16
$null=Txt 701 1188 473 47 'Edges are undirected structural associations, not task precedence. Repeated nodes, self-loops and within-type transport links are omitted.' 16
$null=Txt 701 1244 473 64 'Material is visible in the scene but is not a separate graph node. Its effects enter resource features, including supply, waiting and buffer occupancy.' 16

$s.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text='Sources: env_asset_cfg/cfg_process_task_gallery.py six-stage sequence; cfg_process_subtask_gallery.py process_prefix and outbound_same_zone / outbound_cross_zone; cfg_machine.py workstation counts and assignments; PDFormer/factory_bn/graph.py graph relations; raw_data/dense_i1/node_map.json and meta.json resource composition; FactoryBN.geo and FactoryBN.rel confirm exported entities and relationships. Scene labels identify visible representative instances, not the full resource population. Material is not a graph node. Workbench / rotary resources are alternatives within their families, not additional serial operations. Layout follows user reference and retains v3 graph topology. Full-size original image is embedded with native cropping. All labels, nodes, lines and panels remain native editable PowerPoint objects.'
$target=Join-Path $out 'fig_factory_process_entities_v4.pptx'
$deck.SaveAs($target,24)
$s.Export((Join-Path $out 'fig_factory_process_entities_v4.png'),'PNG',2400,2680)
$deck.SaveAs((Join-Path $out 'fig_factory_process_entities_v4.pdf'),32)
Write-Output "Saved $target; slide objects: $($s.Shapes.Count)"
$deck.Close()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($s) | Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($deck) | Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) | Out-Null


