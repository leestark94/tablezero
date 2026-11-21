# Play-mode capture tour for Case001_Room302 (needs the Editor open with Play Mode running).
# Usage: pwsh -File tools/qa_unity_tour.ps1 -Tag r2
# Each shot: place the investigator (Blender layout coords converted to Unity), optionally ask the
# SERVER to open/switch props (same path as a player key press), wait for motion, capture 1920x1080.
param([string]$Tag = "tour", [string]$OnlyCsv = "")
$Only = @(); if ($OnlyCsv) { $Only = $OnlyCsv.Split(",") }
$proj = Join-Path $PSScriptRoot "..\TableZero.Unity" | Resolve-Path
$out = Join-Path $PSScriptRoot "..\qa\screenshots\unity" | Resolve-Path
function Eval([string]$code) { unity command script eval --project-path $proj --caller plugin --skill unity-cli --code $code 2>&1 | Select-Object -Last 1 }
function U([double]$bx, [double]$by, [double]$bz) { "new UnityEngine.Vector3({0}f,{1}f,{2}f)" -f (-$bx), $bz, (-$by) }
function Shot($name, $bx, $by, $bz, $yaw, $pitch, [string[]]$props = @(), [string]$scene = "", [int]$wait = 2) {
    if ($Only.Count -gt 0 -and $Only -notcontains $name) { return }
    if ($scene) { Eval "TableZero.TZServer.I.Post(""/v1/scene"",""{\""scene\"":\""$scene\""}"",(ok,t)=>{ if(ok) TableZero.TZSceneZoneTrigger.ServerScene=""$scene""; UnityEngine.Debug.Log(""[qa] scene ""+t);}); return ""scene"";" | Out-Null; Start-Sleep 1 }
    Eval "var pc=UnityEngine.Object.FindAnyObjectByType<TableZero.TZPlayerController>(); pc.Place($(U $bx $by $bz),$yaw f,$pitch f); return ""placed"";".Replace(' f', 'f') | Out-Null
    foreach ($p in $props) {
        $id, $act = $p.Split(':')
        Eval "var pr=UnityEngine.GameObject.Find(""$id"").GetComponent<TableZero.TZInspectableProp>(); return pr.TryRequest(TableZero.TZPropAction.$act).ToString();" | Out-Null
        Start-Sleep -Milliseconds 900
    }
    Start-Sleep $wait
    $file = Join-Path $out "$($Tag)_$name.png"
    unity command capture game_view --project-path $proj --caller plugin --skill unity-cli --width 1920 --height 1080 --output-path $file 2>&1 | Out-Null
    Write-Output "shot $name -> $file"
}
# name, blender feet x,y,z, yaw (Unity deg), pitch
Shot "01_hall_door"      0.40 -1.30 -0.12  170  4
Shot "02_entrance_room"  0.60  0.70 -0.12 -156 10 @() "room302"
Shot "03_kitchen_line"   1.55  2.60  0.0   90  25
Shot "04_kitchen_open"   1.30  1.90  0.0   90  30 @("kitchen_drawer_utensils:Open","kitchen_under_sink_left:Open","kitchen_overhead_cabinet1:Open") "" 2
Shot "05_fridge_open"    1.25  4.10  0.0   90  12 @("kitchen_fridge_door:Open") "" 2
Shot "06_scene_table"    1.00  4.90  0.0  -40  42
Shot "07_scene_wide"     0.90  2.40  0.0  -143 22
Shot "08_bed_window"     1.30  3.00  0.0  -142  8
Shot "09_bath_door"      1.60  1.40  0.0  -70   8 @("bath_bath_door:Open") "" 2
Shot "10_bathroom"       2.45  1.55  0.0  -52  22 @("bath_light_switch:Activate","bath_toilet_lid:Open") "" 2
Shot "11_chest_drawer"   0.55  4.90  0.0   177 35 @("sleep_drawer_top:Open") "" 2
Shot "12_ceiling_on"     0.90  2.20  0.0  -150 15 @("living_wall_switch:Activate") "" 2

Shot "13_upper_cabinet"  1.05  2.00  0.0   90 -10 @("kitchen_overhead_cabinet1:Open","kitchen_overhead_cabinet2:Open") "" 2
Shot "14_drawer_open"    1.00  1.60  0.0   90  50 @("kitchen_drawer_utensils:Open") "" 2
Shot "15_undersink"      1.05  2.30  0.0   90  48 @("kitchen_under_sink_left:Open","kitchen_under_sink_right:Open") "" 2

# v4: food/blood close-ups, soft goods, night window, and evidence markers placed by real photographs
function Photo([string]$id) {
    Eval "var d=UnityEngine.Object.FindAnyObjectByType<TableZero.TZInteractionDirector>(); var p=UnityEngine.GameObject.Find(""$id"").GetComponent<TableZero.TZInspectableProp>(); typeof(TableZero.TZInteractionDirector).GetMethod(""Procedure"",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance).Invoke(d,new object[]{p,""photograph""}); return ""photo"";" | Out-Null
    Start-Sleep -Milliseconds 1500
}
Shot "16_table_food"     1.95  3.00  0.0  156 48
Shot "17_floor_blood"    2.90  3.20  0.0  139 40
Shot "19_gloves_sink"    1.00  2.27  0.0   90 48
Shot "20_hoodie_bed"     2.20  4.10  0.0 -120 30
Shot "21_window_night"   1.90  4.40  0.0  180 -4
if ($Only.Count -eq 0 -or $Only -contains "18_markers") {
    Eval "var pc=UnityEngine.Object.FindAnyObjectByType<TableZero.TZPlayerController>(); pc.Place($(U 2.6 3.1 0.0),140f,30f); return ""placed"";" | Out-Null
    Start-Sleep 1
    foreach ($id in @("living_floor_blood", "kitchen_mug", "living_food_bag", "xprop_blood_smear", "living_chair")) { Photo $id }
    Shot "18_markers"    2.95  2.85  0.0  142 36
}

# v5: bathroom floor clutter, printed labels, condensation mould, bed-head wall
Shot "22_bath_floor"     2.45  1.55  0.0  -18 45
Shot "23_condiments"     0.75  3.36  0.0   90 25
Shot "24_window_corner"  1.60  4.90  0.0  159 10
Shot "25_bed_wall"       2.60  4.60  0.0 -144 12
