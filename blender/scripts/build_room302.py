"""CASE 001 — 302호 원룸 v2 (wider, Korean one-room, staged per locked canon). Headless:
  blender -b --factory-startup -P blender/scripts/build_room302.py -- <out.fbx> <out.blend>

Story staging (CASE001_CANON_LOCKED + persona file):
- 20:47 delivery: 떡볶이 set on the low table, receipt stapled to the bag, partly eaten
- 21:12~21:21 강도현 came for his charger/coat: his packed box '도현 짐' by the entrance (charger already gone)
- 21:39~21:49 struggle at the low table: floor chair knocked over, water glass shattered, phone flung face down,
  blood at the table corner, partnership settlement printout on the table and scattered on the floor
- 22:07 report; 119 arrives first, moves her to open floor for CPR (smear trail, pad films, gloves, wrappers),
  transports; police cordon the hall (tape) and leave a PPE box (gloves/shoe covers) at the door
- Front door was found ajar (the neighbour saw it open) → door starts open in the game state
Naming contract: <prop_id> manifest | xprop_* registered extra | arch_* architecture | fix_* fixed furniture.
Layout: room X 0..4.2, Y 0..6.0 (Y+ north window). Walkways >= 0.65 m around the low table.
"""
import sys, os, math, random, json
sys.path.insert(0, os.path.dirname(__file__))
import bpy, bmesh
from mathutils import Vector, Matrix
from tzlib import *
from tzlib import _box_bm
import tzprops
from tzprops import (shoe, switch_plate, drawer, drawer_y, cab_door, plastic_bag, blood_decal, shards,
                     clock, papers, phone, book, pillow, knife, noodle)

random.seed(302)
reset()
H, T, ST = 2.30, 0.15, -0.12
WX, WY = 4.2, 6.0
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FONT = os.path.join(REPO, 'TableZero.Unity', 'Assets', 'TableZero', 'Art', 'Fonts', 'NotoSansKR-Variable.ttf')

M = {
 'wall': mat('M_WallPaper', (0.86, 0.84, 0.80, 1), 0.85), 'floor': mat('M_Floor', (0.62, 0.48, 0.32, 1), 0.35),
 'etile': mat('M_EntranceTile', (0.45, 0.43, 0.40, 1), 0.6), 'btile': mat('M_BathTile', (0.88, 0.88, 0.86, 1), 0.25),
 'bfloor': mat('M_BathFloor', (0.55, 0.55, 0.53, 1), 0.5), 'ceil': mat('M_Ceiling', (0.90, 0.90, 0.88, 1), 0.9),
 'cabw': mat('M_CabinetWhite', (0.90, 0.89, 0.86, 1), 0.35), 'cabwood': mat('M_CabinetWood', (0.62, 0.48, 0.34, 1), 0.5),
 'counter': mat('M_Counter', (0.20, 0.20, 0.21, 1), 0.4), 'steel': mat('M_Steel', (0.75, 0.75, 0.76, 1), 0.32, 1.0),
 'chrome': mat('M_Chrome', (0.9, 0.9, 0.92, 1), 0.08, 1.0), 'doorsteel': mat('M_DoorSteel', (0.24, 0.20, 0.18, 1), 0.45, 0.3),
 'doorwhite': mat('M_DoorWhite', (0.88, 0.87, 0.84, 1), 0.4), 'pw': mat('M_PlasticWhite', (0.92, 0.92, 0.90, 1), 0.4),
 'pb': mat('M_PlasticBlack', (0.03, 0.03, 0.035, 1), 0.35), 'pg': mat('M_PlasticGray', (0.45, 0.46, 0.47, 1), 0.5),
 'porc': mat('M_Porcelain', (0.95, 0.95, 0.94, 1), 0.08), 'glass': mat('M_Glass', (0.8, 0.88, 0.9, 0.25), 0.03),
 'mirror': mat('M_Mirror', (0.95, 0.95, 0.95, 1), 0.02, 1.0), 'rubber': mat('M_Rubber', (0.05, 0.05, 0.05, 1), 0.8),
 'linen': mat('M_FabricLinen', (0.62, 0.64, 0.66, 1), 0.95), 'cotton': mat('M_FabricCotton', (0.85, 0.83, 0.80, 1), 0.95),
 'sheet': mat('M_FabricSheet', (0.78, 0.80, 0.82, 1), 0.95), 'oak': mat('M_WoodOak', (0.60, 0.45, 0.30, 1), 0.55),
 'mattress': mat('M_Mattress', (0.93, 0.92, 0.88, 1), 0.9), 'hconc': mat('M_HallConcrete', (0.62, 0.61, 0.58, 1), 0.85),
 'hplaster': mat('M_HallPlaster', (0.80, 0.79, 0.74, 1), 0.85), 'stair': mat('M_StairTerrazzo', (0.58, 0.56, 0.52, 1), 0.55),
 'carpet': mat('M_Carpet', (0.35, 0.30, 0.27, 1), 1.0), 'paper': mat('M_Paper', (0.93, 0.92, 0.88, 1), 0.9),
 'card': mat('M_Cardboard', (0.62, 0.48, 0.32, 1), 0.9), 'blood': mat('M_BloodDried', (0.16, 0.02, 0.02, 1), 0.35),
 'bloodsmear': mat('M_BloodSmear', (0.22, 0.03, 0.03, 0.75), 0.45), 'led': mat('M_LEDPanel', (1.0, 0.98, 0.94, 1), 0.5),
 'trim': mat('M_WoodTrim', (0.40, 0.30, 0.22, 1), 0.5), 'bagw': mat('M_PlasticBagWhite', (0.92, 0.92, 0.90, 1), 0.45),
 'brass': mat('M_BrassDark', (0.55, 0.45, 0.28, 1), 0.35, 1.0), 'screen': mat('M_ScreenOff', (0.02, 0.02, 0.025, 1), 0.08),
 'alu': mat('M_Aluminum', (0.70, 0.71, 0.72, 1), 0.4, 1.0), 'red': mat('M_PlasticRed', (0.55, 0.06, 0.05, 1), 0.35),
 'green': mat('M_PlasticGreen', (0.20, 0.40, 0.22, 1), 0.4), 'blue': mat('M_PlasticBlue', (0.15, 0.35, 0.65, 1), 0.4),
 'nitrile': mat('M_NitrileBlue', (0.22, 0.42, 0.85, 1), 0.5), 'ink': mat('M_InkBlack', (0.04, 0.04, 0.05, 1), 0.6),
 'inkred': mat('M_InkRed', (0.65, 0.05, 0.05, 1), 0.6), 'marker': mat('M_MarkerBlack', (0.06, 0.06, 0.07, 1), 0.5),
 'tape': mat('M_PoliceTape', (0.95, 0.78, 0.05, 1), 0.35), 'tapeink': mat('M_PoliceTapeInk', (0.05, 0.05, 0.05, 1), 0.35),
 'sauce': mat('M_FoodSauce', (0.55, 0.10, 0.03, 1), 0.25), 'rice': mat('M_RiceCake', (0.95, 0.90, 0.80, 1), 0.4),
 'film': mat('M_ReleaseFilm', (0.92, 0.93, 0.95, 0.85), 0.2), 'clothA': mat('M_LaundryA', (0.25, 0.30, 0.42, 1), 0.95),
 'clothB': mat('M_LaundryB', (0.85, 0.84, 0.80, 1), 0.95), 'clothC': mat('M_LaundryC', (0.55, 0.20, 0.22, 1), 0.95),
 'vinylcover': mat('M_FloorChairFabric', (0.30, 0.32, 0.36, 1), 0.9), 'cushion': mat('M_CushionFabric', (0.58, 0.50, 0.42, 1), 0.95),
 'cosm': mat('M_CosmeticPink', (0.85, 0.65, 0.68, 1), 0.3), 'living_box': mat('M_LivingBox', (0.85, 0.86, 0.88, 0.7), 0.35),
}
tzprops.M.update(M)
import tzprops2
tzprops2.M.update(M)
M.update({
 'bloodpool': mat('M_BloodPool', (0.20, 0.02, 0.02, 0.95), 0.2), 'shoeprint': mat('M_ShoePrint', (0.25, 0.05, 0.04, 0.8), 0.6),
 'bloodspatter': mat('M_BloodSpatter', (0.20, 0.02, 0.02, 0.95), 0.3), 'printdoc': mat('M_PrintDoc', (0.93, 0.92, 0.88, 1), 0.9),
 'ricecake_sauced': mat('M_RiceCakeSauced', (0.78, 0.30, 0.16, 1), 0.3), 'fishcake': mat('M_FishCake', (0.72, 0.48, 0.28, 1), 0.5),
 'scallion': mat('M_Scallion', (0.35, 0.55, 0.20, 1), 0.4), 'sundae_casing': mat('M_SundaeCasing', (0.16, 0.08, 0.09, 1), 0.3),
 'sundae_cut': mat('M_SundaeCut', (0.40, 0.28, 0.30, 1), 0.6), 'liver': mat('M_Liver', (0.30, 0.16, 0.10, 1), 0.5),
 'saltpack': mat('M_SaltPack', (0.95, 0.94, 0.92, 1), 0.5), 'foodlid': mat('M_FoodLid', (0.8, 0.8, 0.78, 0.6), 0.2),
 'danmuji': mat('M_Danmuji', (0.95, 0.80, 0.20, 1), 0.3), 'woodstick': mat('M_WoodStick', (0.85, 0.75, 0.55, 1), 0.7),
 'marker_yellow': mat('M_MarkerYellow', (0.98, 0.78, 0.05, 1), 0.4), 'hoodie': mat('M_HoodieOatmeal', (0.70, 0.66, 0.60, 1), 0.95),
 'tissue': mat('M_Tissue', (0.96, 0.96, 0.95, 1), 0.95), 'canred': mat('M_CanRed', (0.62, 0.05, 0.05, 1), 0.3),
})
import tzprops3
tzprops3.M.update(M)
R90 = math.radians(90)

def W(name, mn, mx, m=None, col='Room302'):
    return box(name, mn, mx, m or M['wall'], bevel=0.0, collection=col)

def label(name, text, size, loc, rot, m=None, extrude=0.0003, collection='Room302'):
    return text_mesh(name, text, size, loc, rot, m or M['ink'], FONT, extrude, collection=collection)

# ======================= ARCHITECTURE =======================
def architecture():
    W('arch_wall_south_a', (-T, -T, ST - 0.03), (0.15, 0, H))
    W('arch_wall_south_b', (1.05, -T, ST - 0.03), (2.2, 0, H))
    W('arch_wall_south_head', (0.15, -T, ST + 2.05), (1.05, 0, H))
    W('arch_wall_south_bath', (2.2, -T, -0.05), (WX + T, 0, H), M['btile'])
    W('arch_wall_north_a', (-T, WY, 0), (1.2, WY + T, H))
    W('arch_wall_north_b', (2.7, WY, 0), (WX + T, WY + T, H))
    W('arch_wall_north_sill', (1.2, WY, 0), (2.7, WY + T, 0.9))
    W('arch_wall_north_head', (1.2, WY, 2.1), (2.7, WY + T, H))
    W('arch_wall_west', (-T, 0, ST - 0.03), (0, WY, H))
    W('arch_wall_east', (WX, 2.1, 0), (WX + T, WY, H))
    W('arch_wall_east_bath_a', (WX, 0, -0.05), (WX + T, 1.3, H), M['btile'])
    W('arch_wall_east_bath_b', (WX, 1.7, -0.05), (WX + T, 2.1, H), M['btile'])
    W('arch_wall_east_bath_sill', (WX, 1.3, -0.05), (WX + T, 1.7, 1.6), M['btile'])
    W('arch_wall_east_bath_head', (WX, 1.3, 2.0), (WX + T, 1.7, H), M['btile'])
    boxes('arch_wall_bath_north', [((2.2, 2.0, -0.05), (WX, 2.005, H), 1), ((2.1, 2.005, -0.05), (WX, 2.1, H), 0)],
          [M['wall'], M['btile']], bevel=0)
    boxes('arch_wall_bath_west_a', [((2.1, 0, -0.05), (2.195, 1.05, H), 0), ((2.195, 0, -0.05), (2.2, 1.05, H), 1)],
          [M['wall'], M['btile']], bevel=0)
    boxes('arch_wall_bath_west_b', [((2.1, 1.8, -0.05), (2.195, 2.0, H), 0), ((2.195, 1.8, -0.05), (2.2, 2.0, H), 1)],
          [M['wall'], M['btile']], bevel=0)
    W('arch_wall_bath_west_head', (2.1, 1.05, 2.0), (2.2, 1.8, H))
    box('arch_floor_main', (0, 2.1, -0.15), (WX, WY, 0), M['floor'], bevel=0)
    box('arch_floor_corridor', (1.2, 0, -0.15), (2.1, 2.1, 0), M['floor'], bevel=0)
    box('arch_floor_kitchen_front', (0, 1.2, -0.15), (1.2, 2.1, 0), M['floor'], bevel=0)
    box('arch_floor_entrance', (0, 0, -0.18), (1.2, 1.2, ST), M['etile'], bevel=0)
    box('arch_floor_bath', (2.2, 0, -0.18), (WX, 2.0, -0.045), M['bfloor'], bevel=0)
    box('arch_bath_threshold', (2.1, 1.05, -0.15), (2.2, 1.8, 0.012), M['porc'], bevel=0.004)
    box('arch_ceiling_main', (0, 0, H), (WX, WY, H + 0.05), M['ceil'], bevel=0)
    for nm, a, b in [('n', (0, WY - 0.03, H - 0.05), (WX, WY, H)), ('w', (0, 2.1, H - 0.05), (0.03, WY, H)),
                     ('e', (WX - 0.03, 2.1, H - 0.05), (WX, WY, H)), ('s', (0, 2.1, H - 0.05), (WX, 2.13, H))]:
        box('arch_crown_' + nm, a, b, M['pw'], bevel=0.004)
    for nm, a, b in [('n1', (0, WY - 0.015, 0), (1.2, WY, 0.07)), ('n2', (2.7, WY - 0.015, 0), (WX, WY, 0.07)),
                     ('e', (WX - 0.015, 3.35, 0), (WX, WY, 0.07)), ('w', (0, 4.45, 0), (0.015, WY, 0.07)),
                     ('bn', (2.1, 2.1, 0), (3.6, 2.115, 0.07)), ('bw', (2.085, 1.8, 0), (2.1, 2.1, 0.07)),
                     ('bw2', (2.085, 0.0, 0), (2.1, 1.05, 0.07))]:
        box('arch_baseboard_' + nm, a, b, M['trim'], bevel=0.002)
    boxes('arch_doorframe_bath', [((2.08, 1.02, -0.01), (2.22, 1.05, 2.03)), ((2.08, 1.80, -0.01), (2.22, 1.83, 2.03)),
                                  ((2.08, 1.02, 2.0), (2.22, 1.83, 2.03))], M['doorwhite'], bevel=0.003)
    boxes('arch_window_frame', [((1.2, WY, 0.9), (2.7, WY + 0.15, 0.95)), ((1.2, WY, 2.05), (2.7, WY + 0.15, 2.1)),
                                ((1.2, WY, 0.9), (1.25, WY + 0.15, 2.1)), ((2.65, WY, 0.9), (2.7, WY + 0.15, 2.1)),
                                ((1.2, WY + 0.07, 0.93), (2.7, WY + 0.08, 0.95))], M['pw'], bevel=0.004)
    box('arch_window_sill_inner', (1.18, WY - 0.08, 0.88), (2.72, WY + 0.02, 0.9), M['oak'], bevel=0.003)
    parts = [((1.2, WY + 0.2, 0.9), (2.7, WY + 0.22, 0.92)), ((1.2, WY + 0.2, 2.08), (2.7, WY + 0.22, 2.1))]
    for i in range(11):
        x = 1.24 + i * 0.14
        parts.append(((x, WY + 0.2, 0.9), (x + 0.012, WY + 0.212, 2.1)))
    boxes('arch_window_grille', parts, M['pg'], bevel=0.0)
    box('arch_kitchen_backsplash', (0, 1.35, 0.86), (0.006, 3.75, 1.45), M['btile'], bevel=0)
    # across the 3 m alley: the neighbouring red-brick 빌라 (what the window actually looks at at night)
    brick = mat('M_ExteriorBrick', (0.45, 0.25, 0.18, 1), 0.85)
    box('arch_exterior_building', (-3.0, WY + 3.2, -7.0), (8.0, WY + 3.6, 7.0), brick, bevel=0)
    lit = mat('M_WindowLitWarm', (1.0, 0.78, 0.5, 1), 0.3)
    dark = mat('M_WindowDark', (0.03, 0.035, 0.045, 1), 0.1)
    wins = []
    k = 0
    for i, (x, z, on) in enumerate([(-1.6, 0.9, True), (0.6, 0.9, False), (2.9, 0.9, True), (5.0, 0.9, False),
                                     (-1.6, 3.6, False), (0.6, 3.6, True), (2.9, 3.6, False), (5.0, 3.6, True),
                                     (-1.6, -1.8, False), (0.6, -1.8, True), (2.9, -1.8, True), (5.0, -1.8, False)]):
        col = (k % 3) if on else 3
        k += 1 if on else 0
        wins.append(tzprops3.wall_card(f'tmp_xwp{i}', (x + 0.6, WY + 3.168, z + 0.55), '-y', 1.2, 1.1, lit if on else dark,
                                       u_range=(col * 0.25, col * 0.25 + 0.25)))
        wins.append(boxes(f'tmp_xw{i}', [((x - 0.04, WY + 3.15, z - 0.04), (x + 1.24, WY + 3.17, z), 0),
                                          ((x - 0.04, WY + 3.15, z + 1.1), (x + 1.24, WY + 3.165, z + 1.14), 0),
                                          ((x + 0.59, WY + 3.155, z), (x + 0.61, WY + 3.166, z + 1.1), 0)], [M['pg']], bevel=0))
    join('arch_exterior_windows', wins, origin=(2.0, WY + 3.18, 0.0))
    tube('arch_exterior_gaspipe', [(-0.4, WY + 3.15, -6.0), (-0.4, WY + 3.15, 6.0)], 0.025, M['pg'])
    lathe('fix_ceiling_light', [(0, -0.002), (0.22, -0.002), (0.23, -0.02), (0.22, -0.045), (0.0, -0.045)], M['led'], 40,
          location=(2.1, 3.9, H))
    lathe('xprop_heat_detector', [(0, 0), (0.05, 0), (0.05, -0.02), (0.035, -0.035), (0, -0.04)], M['pw'], 28,
          location=(2.6, 4.6, H))
    box('arch_ceiling_bath', (2.2, 0, 2.2), (WX, 2.0, 2.25), M['pw'], bevel=0)
    boxes('xprop_aircon_unit', [((WX - 0.25, 4.3, 1.95), (WX, 5.2, 2.22)), ((WX - 0.27, 4.32, 1.97), (WX - 0.25, 5.18, 2.02), 1)],
          [M['pw'], M['pg']], bevel=0.02, seg=3)
    boxes('xprop_wallpad', [((1.3, 0.0, 1.32), (1.52, 0.025, 1.50), 0), ((1.32, 0.025, 1.36), (1.46, 0.027, 1.46), 1),
                            ((1.475, 0.025, 1.36), (1.505, 0.03, 1.46), 0)], [M['pw'], M['screen']], bevel=0.005)
    boxes('xprop_breaker_panel', [((1.25, 0.0, 1.82), (1.62, 0.05, 2.15), 0)], [M['pw']], bevel=0.004)
    boxes('living_heater_remote', [((1.62, 0.0, 1.35), (1.75, 0.025, 1.5), 0), ((1.64, 0.025, 1.40), (1.73, 0.027, 1.47), 1)],
          [M['pw'], M['screen']], bevel=0.004)

# ======================= ENTRANCE =======================
def entrance():
    d = boxes('entrance_door', [((0.17, -0.10, ST + 0.01), (1.03, -0.05, ST + 2.03), 0),
                                ((0.21, -0.051, ST + 0.15), (0.99, -0.049, ST + 1.95), 0)],
              [M['doorsteel']], origin=(1.03, -0.075, ST), bevel=0.006, seg=2)
    lock = boxes('entrance_lock', [((0.22, -0.05, ST + 0.95), (0.30, -0.02, ST + 1.30), 0),
                                   ((0.23, -0.021, ST + 1.0), (0.29, -0.016, ST + 1.12), 1),
                                   ((0.235, -0.03, ST + 1.15), (0.285, -0.0, ST + 1.24), 0)],
                 [M['pb'], M['screen']], origin=(0.26, -0.035, ST + 1.1), bevel=0.006, seg=2)
    lout = boxes('xprop_entrance_lock_outside', [((0.22, -0.13, ST + 0.95), (0.30, -0.10, ST + 1.30), 0),
                                                 ((0.23, -0.134, ST + 1.0), (0.29, -0.129, ST + 1.22), 1)],
                 [M['pb'], M['screen']], origin=(0.26, -0.115, ST + 1.1), bevel=0.006, seg=2)
    parent(lock, d); parent(lout, d)
    boxes('entrance_doorframe', [((0.12, -T, ST), (0.17, 0.0, ST + 2.08)), ((1.03, -T, ST), (1.08, 0.0, ST + 2.08)),
                                 ((0.12, -T, ST + 2.03), (1.08, 0.0, ST + 2.08))], M['doorsteel'], bevel=0.003)
    boxes('fix_shoe_cabinet', [((0.0, 0.25, ST + 0.06), (0.36, 0.27, ST + 1.0)), ((0.0, 0.83, ST + 0.06), (0.36, 0.85, ST + 1.0)),
                               ((0.0, 0.25, ST + 0.98), (0.37, 0.85, ST + 1.02)), ((0.0, 0.25, ST + 0.06), (0.36, 0.85, ST + 0.08)),
                               ((0.0, 0.25, ST + 0.06), (0.02, 0.85, ST + 1.0)), ((0.02, 0.27, ST), (0.33, 0.83, ST + 0.06))],
          M['cabw'], bevel=0.002)
    boxes('entrance_shoe_shelf', [((0.02, 0.27, ST + 0.38), (0.34, 0.83, ST + 0.395)), ((0.02, 0.27, ST + 0.68), (0.34, 0.83, ST + 0.695))],
          M['cabw'], bevel=0.002)
    boxes('entrance_shoe_cabinet', [((0.36, 0.252, ST + 0.08), (0.38, 0.848, ST + 0.98), 0),
                                    ((0.38, 0.79, ST + 0.45), (0.395, 0.80, ST + 0.62), 1)],
          [M['cabw'], M['alu']], origin=(0.37, 0.252, ST), bevel=0.003)
    shoe('entrance_shoes1', (0.62, 0.55, ST), 0.25, M['pw'], M['rubber'], rot=0.25)
    shoe('entrance_shoes2', (0.88, 0.95, ST), 0.25, M['pg'], M['rubber'], rot=-0.6, slipper=True)
    shoe('entrance_shoes3', (0.20, 0.55, ST + 0.395), 0.24, M['pb'], M['rubber'], rot=1.57)
    box('entrance_mat', (0.2, 0.98, ST), (1.0, 1.18, ST + 0.008), M['carpet'], bevel=0.002)
    box('entrance_floor_trim', (0.0, 1.19, ST), (1.2, 1.22, 0.004), M['trim'], bevel=0.003)
    box('xprop_entrance_floor_trim_side', (1.19, 0.0, ST), (1.22, 1.22, 0.004), M['trim'], bevel=0.003)
    boxes('entrance_entry_mirror', [((0.0, 0.35, 1.05), (0.02, 0.75, 1.75), 0), ((0.02, 0.36, 1.06), (0.022, 0.74, 1.74), 1)],
          [M['alu'], M['mirror']], bevel=0.003)
    boxes('entrance_key_hook', [((0.0, 0.92, 1.45), (0.012, 1.10, 1.49)), ((0.012, 0.95, 1.455), (0.04, 0.955, 1.465)),
                                ((0.012, 1.0, 1.455), (0.04, 1.005, 1.465)), ((0.012, 1.05, 1.455), (0.04, 1.055, 1.465))],
          M['oak'], bevel=0.002)
    lan = tube('tmp_lanyard', [(0.035, 1.0, 1.46), (0.04, 0.99, 1.33), (0.04, 1.0, 1.26), (0.035, 1.01, 1.33), (0.035, 1.0, 1.46)], 0.003, M['blue'])
    card = boxes('tmp_badgecard', [((0.03, 0.965, 1.15), (0.036, 1.035, 1.26))], M['pw'], bevel=0.002)
    join('xprop_employee_badge', [lan, card], origin=(0.035, 1.0, 1.46))
    switch_plate('entrance_switch', (1.12, 0.0, 1.2), facing='+y')
    tube('entrance_umbrella', [(0.06, 1.14, ST + 0.01), (0.07, 1.12, ST + 0.35), (0.08, 1.10, ST + 0.62)], 0.03, M['pb'])
    box('entrance_delivery_box', (0.65, 0.12, ST), (1.0, 0.40, ST + 0.22), M['card'], bevel=0.004)
    # 강도현's packed box (came for charger + coat; the charger is already gone from it)
    bm = bmesh.new()
    _box_bm(bm, (1.28, 1.62, 0.0), (1.70, 1.98, 0.30))
    top = max(bm.faces, key=lambda f: f.calc_center_median().z)
    bmesh.ops.delete(bm, geom=[top], context='FACES_ONLY')
    bx = mesh_obj('tmp_dbox', bm, M['card'], origin=(1.49, 1.8, 0.0))
    sm = bx.modifiers.new('s', 'SOLIDIFY'); sm.thickness = 0.004; bake(bx)
    flap1 = box('tmp_flap1', (1.28, 1.62, 0.30), (1.70, 1.625, 0.48), M['card'], bevel=0)
    flap2 = box('tmp_flap2', (1.28, 1.975, 0.30), (1.70, 1.98, 0.45), M['card'], bevel=0)
    contents = boxes('tmp_dcont', [((1.31, 1.66, 0.0), (1.67, 1.94, 0.12), 0), ((1.33, 1.68, 0.12), (1.52, 1.90, 0.17), 1),
                                   ((1.54, 1.70, 0.12), (1.64, 1.86, 0.27), 2)],
                     [M['clothA'], M['clothB'], M['pb']], bevel=0.01)
    txt = label('tmp_dtxt', '도현 짐', 0.07, (1.49, 1.617, 0.17), (R90, 0, 0), M['marker'])
    join('xprop_box_dohyun', [bx, flap1, flap2, contents, txt], origin=(1.49, 1.8, 0.0))

# ======================= KITCHEN =======================
def kitchen():
    y0, y1, D = 1.35, 3.75, 0.60
    boxes('fix_kitchen_carcass', [((0.0, y0, 0.1), (D - 0.02, y0 + 0.02, 0.82)), ((0.0, y1 - 0.02, 0.1), (D - 0.02, y1, 0.82)),
                                  ((0.0, y0, 0.1), (0.02, y1, 0.82)), ((0.0, y0, 0.1), (D - 0.02, 2.69, 0.12)),
                                  ((0.04, y0 + 0.02, 0.0), (D - 0.06, 2.67, 0.1)),
                                  ((0.0, 1.85, 0.1), (D - 0.02, 1.87, 0.82)), ((0.0, 2.67, 0.1), (D - 0.02, 2.69, 0.82)),
                                  ((0.0, 3.29, 0.1), (D - 0.02, 3.31, 0.82)), ((D - 0.02, 2.69, 0.80), (D, 3.29, 0.82)),
                                  ((0.0, 3.31, 0.0), (D - 0.02, y1, 0.1))],
          M['cabw'], bevel=0.002)
    top = box('fix_kitchen_counter', (0.0, y0, 0.82), (D + 0.02, y1, 0.86), M['counter'], bevel=0.003)
    cutter = box('tmp_cut', (0.08, 2.02, 0.7), (0.50, 2.52, 0.95), None, bevel=0.03, seg=3)
    boolean_cut(top, cutter); rewrap_uv(top)
    bm = bmesh.new()
    _box_bm(bm, (0.085, 2.025, 0.64), (0.495, 2.515, 0.86))
    t = max(bm.faces, key=lambda f: f.calc_center_median().z)
    bmesh.ops.delete(bm, geom=[t], context='FACES_ONLY')
    bmesh.ops.bevel(bm, geom=[e for e in bm.edges if not e.is_boundary], offset=0.035, segments=4, affect='EDGES')
    sink = mesh_obj('kitchen_sink', bm, M['steel'], origin=(0.29, 2.27, 0.64))
    sm = sink.modifiers.new('s', 'SOLIDIFY'); sm.thickness = 0.008; sm.offset = 1
    bake(sink); shade_smooth_auto(sink)
    lathe('kitchen_drain_cover', [(0, 0.004), (0.045, 0.004), (0.05, 0.0), (0.0, 0.0)], M['steel'], 32, location=(0.29, 2.27, 0.642))
    base = lathe('tmp_fb', [(0, 0.0), (0.028, 0.0), (0.026, 0.05), (0.018, 0.06), (0, 0.06)], M['chrome'], 32, location=(0.06, 2.27, 0.86))
    neck = tube('tmp_fn', [(0.06, 2.27, 0.9), (0.06, 2.27, 1.12), (0.14, 2.27, 1.16), (0.22, 2.27, 1.08)], 0.012, M['chrome'])
    lev = boxes('tmp_fl', [((0.03, 2.264, 0.92), (0.10, 2.276, 0.932))], M['chrome'], bevel=0.003)
    join('kitchen_faucet', [base, neck, lev], origin=(0.06, 2.27, 0.86))
    drawer('kitchen_drawer_utensils', (0.02, y0 + 0.02, 0.58), (D, 1.85, 0.80), M['cabw'], M['cabw'], axis='x')
    drawer('kitchen_drawer_misc', (0.02, y0 + 0.02, 0.13), (D, 1.85, 0.57), M['cabw'], M['cabw'], axis='x')
    cab_door('kitchen_under_sink_left', (D, 1.89, 0.13), (D + 0.018, 2.28, 0.80), hinge='ymin')
    cab_door('kitchen_under_sink_right', (D, 2.28, 0.13), (D + 0.018, 2.67, 0.80), hinge='ymax')
    # under-counter drum washer (원룸 빌트인 옵션)
    boxes('xprop_washing_machine', [((0.03, 2.71, 0.0), (0.58, 3.27, 0.79), 0), ((0.40, 2.73, 0.66), (0.585, 3.25, 0.78), 1),
                                    ((0.55, 2.75, 0.70), (0.586, 2.92, 0.75), 2)], [M['pw'], M['pg'], M['screen']], bevel=0.012, seg=2)
    wd = lathe('xprop_washer_door', [(0, 0.0), (0.17, 0.0), (0.19, 0.02), (0.185, 0.045), (0.12, 0.05), (0.0, 0.03)],
               [M['pg']], 40, location=(0.0, 0.0, 0.0))
    wd.data.transform(Matrix.Rotation(R90, 4, 'Y'))
    wd.location = (0.585, 2.99, 0.36)
    bpy.context.view_layer.update()
    set_origin(wd, (0.585, 2.80, 0.36))
    rng = boxes('tmp_range', [((0.08, 2.72, 0.86), (0.54, 3.30, 0.875), 0)], [M['pb']], origin=(0.31, 3.01, 0.86), bevel=0.004)
    burners = [lathe(f'tmp_burner{i}', [(0, 0.018), (0.06, 0.018), (0.075, 0.012), (0.075, 0.0), (0, 0)], M['steel'], 28, location=(0.3, yy, 0.875))
               for i, yy in enumerate((2.87, 3.15))]
    join('kitchen_stove', [rng] + burners, origin=(0.31, 3.01, 0.86))
    boxes('xprop_stove_knobs', [((D + 0.0, 2.95, 0.83), (D + 0.03, 2.99, 0.85)), ((D + 0.0, 3.03, 0.83), (D + 0.03, 3.07, 0.85))],
          M['pb'], bevel=0.006)
    boxes('kitchen_hood', [((0.0, 2.70, 1.55), (0.50, 3.32, 1.70), 0), ((0.38, 2.72, 1.545), (0.48, 3.30, 1.552), 1)],
          [M['steel'], M['pg']], bevel=0.006, seg=2)
    boxes('fix_kitchen_upper', [((0.0, 1.35, 1.45), (0.33, 1.37, 2.15)), ((0.0, 2.65, 1.45), (0.33, 2.67, 2.15)),
                                ((0.0, 1.35, 1.45), (0.33, 2.67, 1.47)), ((0.0, 1.35, 2.13), (0.33, 2.67, 2.15)),
                                ((0.0, 1.35, 1.45), (0.02, 2.67, 2.15)), ((0.02, 1.37, 1.80), (0.31, 2.65, 1.815))],
          M['cabw'], bevel=0.002)
    cab_door('kitchen_overhead_cabinet1', (0.33, 1.352, 1.452), (0.348, 2.008, 2.148), hinge='ymin', handle_low=True)
    cab_door('kitchen_overhead_cabinet2', (0.33, 2.012, 1.452), (0.348, 2.668, 2.148), hinge='ymax', handle_low=True)
    boxes('kitchen_dish_rack', [((0.05, 2.53, 0.86), (0.40, 2.57, 0.87)), ((0.05, 2.53, 0.86), (0.06, 2.66, 1.0)),
                                ((0.39, 2.53, 0.86), (0.40, 2.66, 1.0))], M['steel'], bevel=0.002)
    pl = lathe('kitchen_plate', [(0, 0), (0.08, 0), (0.11, 0.02), (0.105, 0.022), (0.075, 0.004), (0, 0.004)], M['porc'], 40,
               location=(0.22, 2.60, 0.87))
    pl.rotation_euler = (math.radians(75), 0, 0)
    boxes('kitchen_spoon', [((0.30, 2.57, 0.87), (0.31, 2.59, 1.02))], M['steel'], bevel=0.003)
    boxes('kitchen_chopsticks', [((0.33, 2.57, 0.87), (0.335, 2.575, 1.08)), ((0.34, 2.57, 0.87), (0.345, 2.575, 1.08))], M['steel'], bevel=0.001)
    boxes('kitchen_cutting_board', [((0.10, 1.45, 0.86), (0.42, 1.71, 0.875))], M['oak'], bevel=0.004)
    knife('kitchen_kitchen_knife', (0.20, 1.58, 0.876))
    boxes('kitchen_knife_rack', [((0.04, 3.62, 0.86), (0.13, 3.70, 1.08))], M['oak'], bevel=0.006)
    lathe('kitchen_dish_soap', [(0, 0), (0.03, 0), (0.032, 0.15), (0.012, 0.17), (0.012, 0.2), (0, 0.2)], M['green'], 24, location=(0.08, 2.0, 0.86))
    boxes('kitchen_sponge', [((0.12, 1.98, 0.86), (0.19, 2.07, 0.885), 0), ((0.12, 1.98, 0.885), (0.19, 2.07, 0.892), 1)],
          [mat('M_SpongeYellow', (0.85, 0.7, 0.2, 1), 0.95), M['green']], bevel=0.004)
    pot = lathe('tmp_pot', [(0, 0), (0.10, 0), (0.105, 0.005), (0.105, 0.12), (0.1, 0.12), (0.098, 0.006), (0, 0.006)],
                M['steel'], 40, location=(0.30, 2.87, 0.89))
    potlid = lathe('tmp_potlid', [(0, 0.135), (0.108, 0.122), (0.11, 0.118), (0.0, 0.118)], [M['glass']], 40, location=(0.30, 2.87, 0.89))
    knob = lathe('tmp_potknob', [(0, 0.135), (0.018, 0.135), (0.014, 0.155), (0, 0.158)], [M['pb']], 16, location=(0.30, 2.87, 0.89))
    h1 = boxes('tmp_poth1', [((0.18, 2.86, 0.99), (0.20, 2.88, 1.0)), ((0.40, 2.86, 0.99), (0.42, 2.88, 1.0))], M['pb'], bevel=0.004)
    join('kitchen_pot', [pot, potlid, knob, h1], origin=(0.30, 2.87, 0.89))
    lathe('kitchen_pan', [(0, 0), (0.11, 0), (0.13, 0.04), (0.125, 0.042), (0.105, 0.006), (0, 0.006)], M['pb'], 40,
          location=(0.30, 3.15, 0.89))
    noodle('kitchen_instant_noodle1', (0.22, 4.02, 1.73))
    noodle('kitchen_instant_noodle2', (0.22, 4.16, 1.73))
    tzprops2.rice_cooker('xprop_rice_cooker', (0.30, 3.53, 0.86), rot=0.0)
    tzprops2.kettle('xprop_kettle', (0.26, 1.86, 0.86), rot=0.4)
    tzprops2.spoon_holder('xprop_spoon_holder', (0.48, 3.70, 0.86))
    tzprops3.rubber_gloves_cloth('xprop_rubber_gloves', [(0.27, 1.47, math.radians(80), False), (0.55, 1.93, math.radians(-98), True)], 0.86,
                                 mat('M_RubberGlovePink', (0.85, 0.35, 0.45, 1), 0.45), [bpy.data.objects[n] for n in ('fix_kitchen_counter', 'kitchen_cutting_board', 'kitchen_kitchen_knife')])
    tzprops2.condiments('xprop_condiments', (0.06, 3.36, 0.86))
    lathe('kitchen_bin', [(0, 0), (0.12, 0), (0.13, 0.36), (0.0, 0.36)], M['pg'], 32, location=(0.30, 3.52, 0.10))
    lathe('kitchen_bin_liner', [(0.125, 0.29), (0.135, 0.37), (0.125, 0.38)], M['bagw'], 32, location=(0.30, 3.52, 0.10))
    fridge()

def fridge():
    x0, x1, y0, y1 = 0.0, 0.57, 3.82, 4.42
    th = 0.03
    boxes('fix_fridge_body', [((x0, y0, 0.02), (x1, y0 + th, 1.45)), ((x0, y1 - th, 0.02), (x1, y1, 1.45)),
                              ((x0, y0, 1.42), (x1, y1, 1.45)), ((x0, y0, 0.02), (x1, y1, 0.06)),
                              ((x0, y0, 0.02), (x0 + th, y1, 1.45)), ((x0, y0, 0.96), (x1, y1, 1.0)),
                              ((x0 + 0.08, y0 + 0.08, 0.0), (x1 - 0.05, y1 - 0.08, 0.02), 1)],
          [M['pw'], M['pb']], bevel=0.008, seg=2)
    boxes('fix_fridge_interior', [((x0 + th, y0 + th, 0.06), (x1 - 0.005, y1 - th, 0.062)),
                                  ((x0 + th + 0.02, y0 + th, 0.36), (x1 - 0.04, y1 - th, 0.366), 1),
                                  ((x0 + th + 0.02, y0 + th, 0.66), (x1 - 0.04, y1 - th, 0.666), 1),
                                  ((x0 + th + 0.02, y0 + th, 1.18), (x1 - 0.04, y1 - th, 1.186), 1)],
          [M['pw'], M['glass']], bevel=0.002)
    def door(z0, z1, handle_low):
        hz = (z1 - 0.28, z1 - 0.04) if handle_low else (z0 + 0.03, z0 + 0.22)
        return [((x1, y0, z0), (x1 + 0.05, y1, z1), 0),
                ((x1 - 0.06, y0 + 0.05, z0 + 0.12), (x1, y1 - 0.05, z0 + 0.135), 1),
                ((x1 + 0.05, y0 + 0.02, hz[0]), (x1 + 0.065, y0 + 0.045, hz[1]), 2)]
    boxes('kitchen_fridge_door', door(0.03, 0.95, True), [M['pw'], M['pw'], M['pg']], origin=(x1 + 0.025, y1, 0.03), bevel=0.008, seg=2)
    fz = door(1.01, 1.44, False)
    boxes('kitchen_fridge_freezer', [fz[0], fz[2]], [M['pw'], M['pw'], M['pg']], origin=(x1 + 0.025, y1, 1.01), bevel=0.008, seg=2)
    lathe('kitchen_fridge_bottle', [(0, 0), (0.035, 0), (0.037, 0.2), (0.015, 0.26), (0.014, 0.29), (0, 0.29)], M['glass'], 24,
          location=(0.30, 3.92, 0.366))
    boxes('kitchen_fridge_milk', [((0.25, 4.02, 0.366), (0.32, 4.09, 0.56), 0), ((0.25, 4.02, 0.56), (0.32, 4.09, 0.59), 1)],
          [M['pw'], mat('M_MilkPrint', (0.25, 0.45, 0.75, 1), 0.6)], bevel=0.003)
    boxes('kitchen_fridge_container', [((0.12, 4.15, 0.666), (0.30, 4.35, 0.74), 0), ((0.12, 4.15, 0.74), (0.30, 4.35, 0.755), 1)],
          [M['glass'], M['red']], bevel=0.008)
    boxes('kitchen_fridge_egg', [((0.32, 4.15, 0.666), (0.46, 4.35, 0.71))], M['pw'], bevel=0.005)
    note = boxes('tmp_fnote', [((x1 + 0.05, 4.0, 0.78), (x1 + 0.052, 4.13, 0.90))], M['paper'], bevel=0.0)
    ntx = label('tmp_fntx', '관리비 25일\n분리수거 화 목', 0.011, (x1 + 0.0525, 4.065, 0.84), (R90, 0, R90), M['ink'])
    join('kitchen_fridge_note', [note, ntx], origin=(x1 + 0.051, 4.065, 0.78))
    m = lathe('kitchen_fridge_magnet', [(0, 0), (0.015, 0), (0.015, 0.008), (0, 0.008)], M['red'], 20, location=(x1 + 0.052, 4.065, 0.89))
    m.rotation_euler = (0, R90, 0)
    boxes('fix_microwave_body', [((0.05, 3.86, 1.45), (0.42, 4.38, 1.73), 0), ((0.05, 4.23, 1.47), (0.425, 4.37, 1.71), 1)],
          [M['pw'], M['pg']], bevel=0.008, seg=2)
    boxes('kitchen_microwave_door', [((0.42, 3.87, 1.47), (0.44, 4.22, 1.71), 0), ((0.44, 3.92, 1.51), (0.442, 4.17, 1.67), 1)],
          [M['pw'], M['screen']], origin=(0.43, 3.87, 1.47), bevel=0.005)
    boxes('kitchen_microwave_buttons', [((0.425, 4.26, 1.60), (0.432, 4.34, 1.68), 0), ((0.425, 4.28, 1.52), (0.435, 4.32, 1.56), 1)],
          [M['screen'], M['pg']], bevel=0.003)
    parts = []
    for i in range(3):
        for j in range(2):
            parts.append(lathe(f'tmp_w{i}{j}', [(0, 0), (0.045, 0), (0.046, 0.26), (0.016, 0.31), (0.014, 0.33), (0, 0.33)], M['glass'], 16,
                               location=(0.10 + j * 0.095, 4.50 + i * 0.0 + 0.0, 0.0) if False else (0.10 + j * 0.095, 4.50 - 0.0 + 0.0, 0.0)))
    # simpler: 2x3 grid next to the bookshelf front
    for o in parts:
        bpy.data.objects.remove(o, do_unlink=True)
    parts = []
    for i in range(3):
        for j in range(2):
            parts.append(lathe(f'tmp_w{i}{j}', [(0, 0), (0.045, 0), (0.046, 0.26), (0.016, 0.31), (0.014, 0.33), (0, 0.33)], M['glass'], 16,
                               location=(0.40 + j * 0.095, 4.60 + i * 0.095, 0.0)))
    join('xprop_water_bundle', parts, origin=(0.45, 4.70, 0.0))

# ======================= LIVING / SLEEP + SCENE STAGING =======================
def living():
    tx0, tx1, ty0, ty1 = 1.3, 2.1, 3.3, 3.85
    boxes('living_table', [((tx0, ty0, 0.30), (tx1, ty1, 0.33)), ((tx0 + 0.04, ty0 + 0.04, 0.0), (tx0 + 0.07, ty0 + 0.07, 0.30)),
                           ((tx1 - 0.07, ty0 + 0.04, 0.0), (tx1 - 0.04, ty0 + 0.07, 0.30)), ((tx0 + 0.04, ty1 - 0.07, 0.0), (tx0 + 0.07, ty1 - 0.04, 0.30)),
                           ((tx1 - 0.07, ty1 - 0.07, 0.0), (tx1 - 0.04, ty1 - 0.04, 0.30))], M['oak'], bevel=0.004)
    drawer_y('living_table_drawer', (1.55, ty0 + 0.02, 0.245), (1.85, ty0 + 0.30, 0.298), M['oak'], M['oak'])
    tzprops2.floor_chair('living_chair', (2.62, 4.34, 0.0), rot_z=0.95)
    box('xprop_floor_cushion', (1.48, 2.86, 0.0), (1.90, 3.24, 0.06), M['cushion'], bevel=0.025, seg=3)
    tzprops3.delivery_bag_open('living_food_bag', (1.44, 3.46, 0.338), rot=0.25, font=FONT)
    rc = boxes('tmp_rcp', [((1.36, 3.372, 0.36), (1.44, 3.373, 0.45))], M['paper'], bevel=0.0)
    rct = label('tmp_rc', '배달완료\n20:47\n떡볶이 1\n순대 1', 0.009, (1.40, 3.3715, 0.405), (R90, 0, 0), M['ink'])
    join('xprop_delivery_receipt', [rc, rct], origin=(1.40, 3.372, 0.36))
    tb, tlid = tzprops3.tteokbokki('living_food_container1', (1.70, 3.47, 0.33), rot=0.12)
    tlid.name = 'xprop_tteok_lid'
    tlid.rotation_euler = (math.pi, 0, 0.45); tlid.location = (2.02, 3.56, 0.339)
    tzprops3.sundae('living_food_container2', (1.89, 3.44, 0.3335), rot=-0.1)
    tzprops3.danmuji('xprop_danmuji', (1.86, 3.585, 0.33))
    tzprops3.chopsticks('xprop_chopsticks_used', (1.71, 3.47, 0.392), 0.35, split=True)
    tzprops3.chopsticks('xprop_chopsticks_unused', (1.78, 3.61, 0.3335), -0.25, split=False)
    boxes('living_disposable_spoon', [((1.52, 3.585, 0.3405), (1.68, 3.60, 0.3465))], M['pw'], bevel=0.002)
    tzprops3.soda_can('living_cola_can', (2.05, 3.37, 0.33), M['canred'])
    box('living_napkin', (1.32, 3.66, 0.33), (1.40, 3.74, 0.37), M['paper'], bevel=0.02, seg=3)
    mug = lathe('tmp_mug', [(0, 0), (0.038, 0), (0.042, 0.004), (0.043, 0.095), (0.039, 0.095), (0.038, 0.008), (0, 0.008)],
                M['porc'], 36, location=(2.00, 3.72, 0.33))
    coffee = lathe('tmp_coffee', [(0, 0.05), (0.038, 0.05), (0.038, 0.052), (0, 0.052)], [mat('M_CoffeeCold', (0.12, 0.07, 0.04, 1), 0.85)], 24,
                   location=(2.00, 3.72, 0.33))
    hnd = tube('tmp_mh', [(2.042, 3.72, 0.39), (2.07, 3.72, 0.38), (2.07, 3.72, 0.36), (2.042, 3.72, 0.35)], 0.006, M['porc'])
    join('kitchen_mug', [mug, coffee, hnd], origin=(2.00, 3.72, 0.33))
    stack = [tzprops3.sheet(f'tmp_pst{i}', 1.60 + random.uniform(-0.006, 0.006), 3.72 + random.uniform(-0.006, 0.006), 0.3305 + i * 0.0007,
                            math.pi + random.uniform(-0.04, 0.04), page=(0 if i == 4 else 1), curl=0.0015) for i in range(5)]
    join('living_paper_stack', stack, origin=(1.60, 3.72, 0.33))
    label('xprop_settlement_title', '담다공방 3분기 정산', 0.0095, (1.60, 3.598, 0.3343), (0, 0, math.pi), M['ink'])
    sheets = []
    for i, (x, y, r, pg, cu, lc) in enumerate([(1.95, 4.15, 0.4, 0, 0.004, 0.0), (2.55, 3.45, -0.9, 1, 0.006, 0.012),
                                                (1.55, 4.35, 1.2, 1, 0.003, 0.0), (2.55, 4.45, 0.2, 0, 0.008, 0.02)]):
        sheets.append(tzprops3.sheet(f'tmp_sheet{i}', x, y, 0.0009 + i * 0.0003, r, page=pg, curl=cu, lift_corner=lc))
    join('xprop_scattered_papers', sheets, origin=(2.05, 4.1, 0.0))
    boxes('living_envelope', [((1.86, 3.36, 0.33), (2.06, 3.46, 0.333))], mat('M_EnvelopeKraft', (0.75, 0.62, 0.42, 1), 0.85), bevel=0.0005)
    boxes('living_pen', [((1.45, 3.79, 0.333), (1.59, 3.80, 0.342))], M['pb'], bevel=0.003)
    boxes('living_notepad', [((1.33, 3.35, 0.33), (1.42, 3.47, 0.338))], mat('M_NotepadYellow', (0.95, 0.88, 0.55, 1), 0.85), bevel=0.001)
    # struggle traces
    tzprops3.blood_pool('living_floor_blood', (2.24, 3.97, 0.0015))
    tzprops3.spatter_cards('xprop_table_edge_stain', [('h', 2.055, 3.815, 0.3306, 0.09, 0.6),
                                                      ('v', (2.1003, 3.80, 0.312), '+x', 0.07, 0.035),
                                                      ('v', (2.0606, 3.795, 0.18), '+x', 0.03, 0.22)], origin=(2.08, 3.82, 0.3))
    tzprops3.spatter_cards('xprop_blood_drops', [('h', 2.02, 3.93, 0.0017, 0.16, 0.3), ('h', 2.44, 3.80, 0.0017, 0.14, 2.2),
                                                 ('h', 2.40, 4.22, 0.0017, 0.12, 4.0), ('h', 1.99, 4.12, 0.0026, 0.10, 1.1)], origin=(2.2, 3.97, 0.0))
    tzprops3.blood_smear('xprop_blood_smear', [(2.18, 4.02), (2.12, 4.16), (2.03, 4.32), (1.95, 4.48), (1.90, 4.62)], 0.11)
    tzprops3.shoeprints('living_footprint', [(2.40, 3.62, math.pi + 0.05, True, 0), (2.50, 3.33, math.pi - 0.04, False, 1),
                                             (2.41, 3.04, math.pi + 0.08, True, 2), (2.49, 2.74, math.pi, False, 3)])
    shards('living_broken_glass', (1.15, 4.0, 0.0))
    ph = phone('living_phone', (2.55, 3.72, 0.0))
    ph.rotation_euler = (math.pi, 0, 0.6); ph.location.z = 0.0085
    ems_debris('xprop_ems_debris', (1.85, 4.80))
    lathe('living_lamp', [(0, 0), (0.12, 0), (0.12, 0.02), (0.012, 0.03), (0.012, 1.35), (0.11, 1.38), (0.16, 1.55), (0.0, 1.55)],
          [M['pb']], 32, location=(2.80, 5.30, 0.0))
    def sash(x0, x1, y0, y1, z0=0.95, z1=2.05, f=0.045):
        ym = (y0 + y1) / 2
        return [((x0, y0, z0), (x1, y1, z0 + f), 0), ((x0, y0, z1 - f), (x1, y1, z1), 0),
                ((x0, y0, z0), (x0 + f, y1, z1), 0), ((x1 - f, y0, z0), (x1, y1, z1), 0),
                ((x0 + f, ym - 0.003, z0 + f), (x1 - f, ym + 0.003, z1 - f), 1)]
    boxes('living_window', sash(1.25, 2.0, WY + 0.09, WY + 0.12), [M['pw'], M['glass']], origin=(1.625, WY + 0.105, 0.95), bevel=0.003)
    boxes('xprop_window_fixed_sash', sash(1.95, 2.65, WY + 0.05, WY + 0.08), [M['pw'], M['glass']], bevel=0.003)
    boxes('living_window_latch', [((1.96, WY + 0.085, 1.45), (1.99, WY + 0.09, 1.55))], M['pw'], bevel=0.002)
    curtain_at('living_curtain_left', 1.0, 1.4)
    curtain_at('living_curtain_right', 2.5, 2.9)
    clock('living_wall_clock', (3.05, 2.1, 1.95))
    switch_plate('living_wall_switch', (2.1, 1.93, 1.2), facing='-x')
    boxes('living_aircon_remote', [((3.30, 4.2, 0.50), (3.34, 4.34, 0.518))], M['pw'], bevel=0.008)
    boxes('living_laptop', [((3.25, 4.45, 0.53), (3.57, 4.67, 0.548), 0), ((3.26, 4.46, 0.548), (3.56, 4.66, 0.552), 1)],
          [M['alu'], M['alu']], bevel=0.004)
    tube('living_laptop_charger', [(3.57, 4.56, 0.54), (3.75, 4.6, 0.5), (4.0, 4.7, 0.3), (4.12, 4.8, 0.02)], 0.003, M['pb'])
    boxes('living_power_strip', [((4.05, 4.9, 0.0), (4.18, 5.25, 0.04), 0), ((4.07, 4.94, 0.04), (4.16, 5.21, 0.042), 1)],
          [M['pw'], M['red']], bevel=0.008)
    tube('living_power_cable', [(4.1, 5.25, 0.01), (4.0, 5.6, 0.008), (3.6, 5.9, 0.008)], 0.004, M['pw'])
    boxes('living_bookshelf', [((0.0, 4.52, 0.0), (0.30, 4.54, 1.2)), ((0.0, 5.08, 0.0), (0.30, 5.10, 1.2)),
                               ((0.0, 4.52, 0.0), (0.02, 5.10, 1.2)), ((0.0, 4.52, 0.0), (0.30, 5.10, 0.03)),
                               ((0.0, 4.52, 0.40), (0.30, 5.10, 0.42)), ((0.0, 4.52, 0.80), (0.30, 5.10, 0.82)),
                               ((0.0, 4.52, 1.18), (0.30, 5.10, 1.2))], M['pw'], bevel=0.002)
    book('living_book1', (0.05, 4.60, 0.42), (0.22, 0.035, 0.28), mat('M_BookCoverA', (0.18, 0.25, 0.38, 1), 0.6))
    book('living_book2', (0.05, 4.64, 0.42), (0.20, 0.03, 0.25), mat('M_BookCoverB', (0.55, 0.20, 0.15, 1), 0.6))
    boxes('living_box_storage', [((0.03, 4.65, 0.03), (0.28, 5.05, 0.30), 0)], [M['living_box']], bevel=0.01)
    cal = boxes('tmp_cal', [((0.0, 4.60, 1.35), (0.004, 5.00, 1.85))], M['paper'], bevel=0)
    grid = []
    for r in range(5):
        for c in range(7):
            grid.append(((0.0045, 4.62 + c * 0.052, 1.40 + r * 0.06), (0.0050, 4.623 + c * 0.052, 1.455 + r * 0.06)))
    grid_o = boxes('tmp_grid', grid, M['ink'], bevel=0)
    note = label('tmp_calnote', '정산 마감!!', 0.022, (0.0055, 4.85, 1.55), (R90, 0, -R90), M['inkred'])
    join('xprop_wall_calendar', [cal, grid_o, note], origin=(0.002, 4.80, 1.35))
    stock = []
    for i, (z, w) in enumerate([(0.0, 0.42), (0.30, 0.40), (0.58, 0.36)]):
        stock.append(box(f'tmp_stock{i}', (3.65, 3.40, z), (3.65 + w, 3.86, z + 0.29), M['card'], bevel=0.004))
    stock.append(boxes('tmp_waybill', [((3.70, 3.398, 0.62), (3.82, 3.399, 0.70))], M['paper'], bevel=0))
    stock.append(label('tmp_wbtxt', '보내는 분: 담다공방', 0.008, (3.76, 3.3975, 0.66), (R90, 0, 0), M['ink']))
    join('xprop_stock_boxes', stock, origin=(3.85, 3.63, 0.0))
    rack = [tube('tmp_rk1', [(1.35, 5.45, 0.0), (1.45, 5.55, 1.05)], 0.008, M['alu']), tube('tmp_rk2', [(2.55, 5.45, 0.0), (2.45, 5.55, 1.05)], 0.008, M['alu']),
            tube('tmp_rk3', [(1.35, 5.75, 0.0), (1.45, 5.65, 1.05)], 0.008, M['alu']), tube('tmp_rk4', [(2.55, 5.75, 0.0), (2.45, 5.65, 1.05)], 0.008, M['alu'])]
    for k in range(4):
        rack.append(tube(f'tmp_rkb{k}', [(1.45, 5.55 + k * 0.035, 1.05), (2.45, 5.55 + k * 0.035, 1.05)], 0.005, M['alu']))
    for i, (x, w, h, mm) in enumerate([(1.55, 0.35, 0.55, 'clothA'), (1.95, 0.25, 0.35, 'clothB'), (2.22, 0.18, 0.18, 'clothC')]):
        rack.append(box(f'tmp_cl{i}', (x, 5.57 + i * 0.03, 1.05 - h), (x + w, 5.585 + i * 0.03, 1.06), M[mm], bevel=0.006))
    join('xprop_drying_rack', rack, origin=(1.95, 5.6, 0.0))
    bed()
    boxes('sleep_bedside_table', [((2.6, 5.5, 0.0), (3.0, 5.9, 0.04)), ((2.6, 5.5, 0.46), (3.0, 5.9, 0.5)),
                                  ((2.6, 5.5, 0.0), (2.62, 5.9, 0.5)), ((2.98, 5.5, 0.0), (3.0, 5.9, 0.5)),
                                  ((2.6, 5.88, 0.0), (3.0, 5.9, 0.5))], M['oak'], bevel=0.003)
    drawer_y('sleep_bedside_drawer', (2.62, 5.5, 0.30), (2.98, 5.88, 0.46), M['oak'], M['oak'])
    tzprops2.tissue_box('xprop_tissue_box', (2.80, 5.70, 0.50), rot=0.25)
    tzprops3.crumpled_tissues('xprop_crumpled_tissues', [(2.70, 5.40, 0.0, 0.028), (2.86, 5.33, 0.0, 0.024), (3.02, 5.45, 0.0, 0.03)], M['tissue'])
    tube('sleep_bedside_phone', [(2.70, 5.62, 0.345), (2.8, 5.66, 0.343), (2.9, 5.6, 0.343)], 0.003, M['pw'])
    wardrobe()
    chest()
    boxes('sleep_mirror', [((2.25, 2.1, 0.3), (2.70, 2.125, 1.85), 0), ((2.27, 2.125, 0.32), (2.68, 2.127, 1.83), 1)],
          [M['pw'], M['mirror']], bevel=0.004)
    lathe('sleep_laundry', [(0, 0), (0.18, 0), (0.2, 0.45), (0.19, 0.45), (0.17, 0.02), (0, 0.02)], [M['pg']], 28, location=(3.35, 2.42, 0.0))
    boxes('sleep_suitcase', [((2.75, 2.15, 0.0), (3.40, 2.40, 0.45), 0), ((3.0, 2.40, 0.32), (3.15, 2.42, 0.35), 1)],
          [mat('M_SuitcaseNavy', (0.10, 0.13, 0.22, 1), 0.4), M['pb']], origin=(3.075, 2.40, 0.0), bevel=0.02, seg=3)
    plastic_bag('living_trash_bag', (1.92, 0.30, 0.0), (0.30, 0.26, 0.40), mat('M_VolumeBag', (0.93, 0.93, 0.90, 0.95), 0.4), knot=True, seed=7)
    plastic_bag('xprop_recycle_bag', (1.92, 0.68, 0.0), (0.30, 0.24, 0.32), mat('M_ClearBag', (0.85, 0.88, 0.9, 0.45), 0.6), knot=False, seed=9)

def floor_chair(name, at):
    """좌식의자 knocked over (seat + folding backrest), lying on its side."""
    x, y, z = at
    seat = box('tmp_fcseat', (x - 0.22, y - 0.22, 0.0), (x + 0.22, y + 0.22, 0.07), M['vinylcover'], bevel=0.025, seg=3)
    bm = bmesh.new()
    _box_bm(bm, (x - 0.21, y + 0.17, 0.05), (x + 0.21, y + 0.23, 0.50))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.02, segments=3, affect='EDGES')
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(x, y + 0.20, 0.05), matrix=Matrix.Rotation(math.radians(-20), 3, 'X'))
    back = mesh_obj('tmp_fcback', bm, M['vinylcover'], origin=(x, y, 0.0))
    c = join(name, [seat, back], origin=(x, y, 0.0))
    c.rotation_euler = (0, math.radians(88), math.radians(30))
    c.location.z = 0.22
    return c

def smear(name, pts, width):
    bm = bmesh.new()
    left, right = [], []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        ax, ay = pts[max(i - 1, 0)]; bx, by = pts[min(i + 1, n - 1)]
        nx, ny = (by - ay), -(bx - ax)
        l = math.hypot(nx, ny) or 1
        w = width * (1.0 - 0.6 * i / n)
        left.append(bm.verts.new((x + nx / l * w, y + ny / l * w, 0.0014)))
        right.append(bm.verts.new((x - nx / l * w, y - ny / l * w, 0.0014)))
    for i in range(n - 1):
        bm.faces.new((left[i], right[i], right[i + 1], left[i + 1]))
    return mesh_obj(name, bm, M['bloodsmear'], origin=(pts[0][0], pts[0][1], 0.0))

def ems_debris(name, at):
    """119 CPR leftovers: defib pad release films, torn wrappers, a blue nitrile glove, an airway cap."""
    x, y = at
    parts = []
    for i, (dx, dy, r) in enumerate([(0.0, 0.0, 0.3), (0.25, 0.15, -0.5), (-0.2, 0.25, 1.0)]):
        f = box(f'tmp_film{i}', (x + dx - 0.07, y + dy - 0.11, 0.0006), (x + dx + 0.07, y + dy + 0.11, 0.0012), M['film'], bevel=0)
        f.rotation_euler = (0, 0, r); parts.append(f)
    for i, (dx, dy) in enumerate([(0.35, -0.1), (-0.3, -0.05)]):
        parts.append(box(f'tmp_wrap{i}', (x + dx - 0.05, y + dy - 0.035, 0.0), (x + dx + 0.05, y + dy + 0.035, 0.003), M['pw'], bevel=0.0005))
    g = box('tmp_glove', (x + 0.1, y - 0.3, 0.0), (x + 0.24, y - 0.22, 0.015), M['nitrile'], bevel=0.006, seg=2)
    g.rotation_euler = (0, 0, 0.7); parts.append(g)
    parts.append(lathe('tmp_cap', [(0, 0), (0.012, 0), (0.012, 0.02), (0, 0.02)], M['pw'], 12, location=(x - 0.12, y - 0.25, 0.0)))
    return join(name, parts, origin=(x, y, 0.0))

def curtain_at(name, x0, x1):
    bm = bmesh.new()
    n = 18
    top, bot = [], []
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = WY - 0.06 + 0.03 * math.sin(t * math.pi * 7)
        top.append(bm.verts.new((x, y, 2.18)))
        bot.append(bm.verts.new((x, y + 0.01 * math.sin(t * 11), 0.02)))
    for i in range(n):
        bm.faces.new((bot[i], bot[i + 1], top[i + 1], top[i]))
    o = mesh_obj('tmp_curt', bm, mat('M_CurtainFabric', (0.42, 0.44, 0.46, 1), 0.95), origin=((x0 + x1) / 2, WY - 0.06, 2.18), smooth=True)
    sm = o.modifiers.new('s', 'SOLIDIFY'); sm.thickness = 0.004
    bake(o)
    rail = tube('tmp_rail', [(x0 - 0.05, WY - 0.06, 2.2), (x1 + 0.05, WY - 0.06, 2.2)], 0.008, M['alu'])
    return join(name, [o, rail], origin=((x0 + x1) / 2, WY - 0.06, 2.18))

def bed():
    x0, x1, y0, y1 = 3.05, 4.15, 3.90, 5.90
    boxes('sleep_bed', [((x0, y0, 0.18), (x1, y1, 0.28)), ((x0 + 0.03, y0 + 0.03, 0.0), (x0 + 0.08, y0 + 0.08, 0.18)),
                        ((x1 - 0.08, y0 + 0.03, 0.0), (x1 - 0.03, y0 + 0.08, 0.18)), ((x0 + 0.03, y1 - 0.08, 0.0), (x0 + 0.08, y1 - 0.03, 0.18)),
                        ((x1 - 0.08, y1 - 0.08, 0.0), (x1 - 0.03, y1 - 0.03, 0.18)), ((x0, y1 - 0.04, 0.18), (x1, y1, 0.85))],
          M['oak'], bevel=0.006)
    boxes('xprop_underbed_livingbox', [((x0 + 0.12, 4.55, 0.0), (x0 + 0.72, 5.15, 0.16), 0)], [M['living_box']], bevel=0.012)
    m = box('fix_mattress', (x0 + 0.03, y0 + 0.03, 0.28), (x1 - 0.03, y1 - 0.06, 0.50), M['mattress'], bevel=0.04, seg=4)
    shade_smooth_auto(m, 50)
    box('sleep_sheet', (x0 + 0.025, y0 + 0.025, 0.50), (x1 - 0.025, y1 - 0.055, 0.506), M['sheet'], bevel=0.003)
    pad = box('tmp_epad', (x0 + 0.10, y0 + 0.30, 0.506), (x1 - 0.10, y1 - 0.55, 0.510), mat('M_HeatingPad', (0.75, 0.62, 0.55, 1), 0.9), bevel=0.004)
    cord = tube('tmp_epcord', [(x0 + 0.1, y0 + 0.4, 0.51), (x0 - 0.02, y0 + 0.45, 0.45), (x0 - 0.04, y0 + 0.6, 0.05)], 0.003, M['pw'])
    join('xprop_electric_blanket', [pad, cord], origin=((x0 + x1) / 2, y0 + 1.0, 0.506))
    # duvet: real cloth simulation dropped onto mattress/sheet/frame (natural folds, drape over the sides)
    rnd = random.Random(17)
    bm = bmesh.new()
    nx, ny = 34, 40
    X0, X1, Y0, Y1 = x0 - 0.06, x1 + 0.05, y0 + 0.06, y0 + 1.45
    grid = [[bm.verts.new((X0 + (X1 - X0) * i / nx, Y0 + (Y1 - Y0) * j / ny,
                          0.585 + 0.012 * math.sin(i * 0.45 + j * 0.25) * math.sin(j * 0.17 + 1.0) + rnd.uniform(0, 0.004)))
             for i in range(nx + 1)] for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    o = mesh_obj('tmp_duvet', bm, M['linen'], origin=(0, 0, 0), smooth=True)
    colliders = [bpy.data.objects[n] for n in ('fix_mattress', 'sleep_sheet', 'sleep_bed', 'xprop_electric_blanket')]
    for c in colliders:
        cm = c.modifiers.new('col', 'COLLISION')
        c.collision.cloth_friction = 40.0
        c.collision.thickness_outer = 0.006
    cl = o.modifiers.new('cloth', 'CLOTH')
    st = cl.settings
    st.quality = 10; st.mass = 0.6; st.tension_stiffness = 25; st.compression_stiffness = 25
    st.shear_stiffness = 10; st.bending_stiffness = 6.0; st.air_damping = 4
    cl.collision_settings.distance_min = 0.012
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 45
    cl.point_cache.frame_start, cl.point_cache.frame_end = 1, 45
    cl.collision_settings.friction = 20
    for f in range(1, 46):
        sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    o.modifiers.clear()
    old = o.data; o.data = me; bpy.data.meshes.remove(old)
    sc.frame_set(1)
    for c in colliders:
        for m_ in list(c.modifiers):
            if m_.type == 'COLLISION':
                c.modifiers.remove(m_)
    sm = o.modifiers.new('s', 'SOLIDIFY'); sm.thickness = 0.028; sm.offset = 1
    ss = o.modifiers.new('sub', 'SUBSURF'); ss.levels = 1
    bake(o)
    o.name = 'sleep_blanket'
    set_origin(o, ((x0 + x1) / 2, y0 + 0.7, 0.5))
    shade_smooth_auto(o, 70)
    tzprops3.hoodie_on_bed('xprop_hoodie', (x0, 4.62, 0.56), M['hoodie'],
                           [bpy.data.objects[n] for n in ('fix_mattress', 'sleep_sheet', 'sleep_bed', 'sleep_blanket', 'arch_floor_main')])
    pillow('sleep_pillow1', (x0 + 0.42, y1 - 0.26, 0.56))
    pillow('sleep_pillow2', (x1 - 0.30, y1 - 0.62, 0.55))

def wardrobe():
    x0, x1, y0, y1 = 3.6, 4.2, 2.15, 3.35
    boxes('fix_wardrobe_body', [((x0 + 0.02, y0, 0.0), (x1, y0 + 0.02, 2.0)), ((x0 + 0.02, y1 - 0.02, 0.0), (x1, y1, 2.0)),
                                ((x0 + 0.02, y0, 1.98), (x1, y1, 2.0)), ((x0 + 0.02, y0, 0.0), (x1, y1, 0.08)),
                                ((x1 - 0.02, y0, 0.0), (x1, y1, 2.0)), ((x0 + 0.02, 2.74, 0.08), (x1, 2.76, 1.98)),
                                ((x0 + 0.02, 2.76, 1.2), (x1 - 0.02, y1 - 0.02, 1.22)), ((x0 + 0.02, 2.76, 0.6), (x1 - 0.02, y1 - 0.02, 0.62))],
          M['cabwood'], bevel=0.003)
    tube('xprop_wardrobe_rod', [(3.90, 2.17, 1.78), (3.90, 2.72, 1.78)], 0.012, M['chrome'])
    for name, ya, yb, hinge in (('sleep_wardrobe_left', 2.152, 2.748, 'ymin'), ('sleep_wardrobe_right', 2.752, 3.348, 'ymax')):
        hy = (yb - 0.06, yb - 0.045) if hinge == 'ymin' else (ya + 0.045, ya + 0.06)
        boxes(name, [((x0, ya, 0.082), (x0 + 0.02, yb, 1.978), 0), ((x0 - 0.02, hy[0], 0.9), (x0, hy[1], 1.15), 1)],
              [M['cabwood'], M['alu']], origin=(x0 + 0.01, ya if hinge == 'ymin' else yb, 0.082), bevel=0.003)
    tube('sleep_hanger', [(3.90, 2.30, 1.78), (3.90, 2.30, 1.72), (3.90, 2.17, 1.64), (3.90, 2.45, 1.64), (3.90, 2.30, 1.72)], 0.004, M['pb'])
    coat = box('sleep_coat', (3.72, 2.35, 0.95), (4.08, 2.60, 1.70), mat('M_CoatWool', (0.16, 0.16, 0.18, 1), 0.9), bevel=0.05, seg=3)
    shade_smooth_auto(coat)
    boxes('sleep_shirt', [((3.75, 2.90, 1.22), (4.05, 3.18, 1.27))], mat('M_ShirtCotton', (0.72, 0.78, 0.85, 1), 0.9), bevel=0.012, seg=2)

def chest():
    x0, x1, y0, y1 = 0.2, 0.8, 5.55, 6.0
    boxes('fix_drawer_chest', [((x0, y0 + 0.02, 0.0), (x0 + 0.02, y1, 0.78)), ((x1 - 0.02, y0 + 0.02, 0.0), (x1, y1, 0.78)),
                               ((x0, y0 + 0.02, 0.76), (x1, y1, 0.78)), ((x0, y0 + 0.02, 0.0), (x1, y1, 0.05)),
                               ((x0, y1 - 0.02, 0.0), (x1, y1, 0.78))], M['pw'], bevel=0.006)
    for nm, za, zb in (('sleep_drawer_top', 0.52, 0.755), ('sleep_drawer_mid', 0.285, 0.515), ('sleep_drawer_bottom', 0.05, 0.28)):
        drawer_y(nm, (x0 + 0.02, y0, za), (x1 - 0.02, y1 - 0.02, zb), M['living_box'], M['pw'])
    boxes('living_photo_frame', [((0.62, 5.88, 0.78), (0.76, 5.90, 0.96), 0), ((0.63, 5.879, 0.79), (0.75, 5.88, 0.95), 1)],
          [M['oak'], mat('M_PhotoPrint', (0.55, 0.5, 0.45, 1), 0.3)], bevel=0.003)
    cos = []
    for i, (x, h, r) in enumerate([(0.28, 0.14, 0.025), (0.34, 0.10, 0.03), (0.40, 0.17, 0.02), (0.47, 0.06, 0.035)]):
        cos.append(lathe(f'tmp_cos{i}', [(0, 0), (r, 0), (r, h), (r * 0.5, h + 0.02), (0, h + 0.02)], M['cosm'] if i % 2 == 0 else M['pw'], 16,
                         location=(x, 5.75, 0.78)))
    join('xprop_cosmetics', cos, origin=(0.38, 5.75, 0.78))

# ======================= BATHROOM =======================
def bathroom():
    boxes('bath_bath_door', [((2.13, 1.055, 0.012), (2.17, 1.795, 1.995), 0),
                             ((2.10, 1.10, 0.98), (2.13, 1.13, 1.0), 1), ((2.10, 1.10, 0.98), (2.112, 1.22, 0.995), 1),
                             ((2.17, 1.10, 0.98), (2.2, 1.13, 1.0), 1), ((2.188, 1.10, 0.98), (2.2, 1.22, 0.995), 1),
                             ((2.125, 1.25, 0.05), (2.13, 1.6, 0.25), 2)],
          [M['doorwhite'], M['chrome'], M['pg']], origin=(2.15, 1.795, 0.012), bevel=0.004)
    switch_plate('bath_light_switch', (2.1, 0.92, 1.2), facing='-x')
    switch_plate('bath_vent_fan', (2.1, 0.82, 1.2), facing='-x')
    tx, ty = 3.74, 0.50
    parts = tzprops2.toilet('fix_toilet', (tx, ty, -0.045), facing=-1)
    join('fix_toilet_bowl', parts, origin=(tx, ty, -0.045))
    boxes('fix_toilet_tank', [((3.98, ty - 0.20, 0.36), (4.18, ty + 0.20, 0.76), 0), ((3.975, ty - 0.21, 0.76), (4.185, ty + 0.21, 0.785), 0)],
          [M['porc']], bevel=0.02, seg=3)
    tzprops2.toilet_seat_and_lid('bath_toilet_seat', 'bath_toilet_lid', (tx, ty, -0.045), hinge_x=3.93, facing=-1)
    boxes('bath_flush_handle', [((4.05, ty - 0.03, 0.785), (4.11, ty + 0.03, 0.792))], M['chrome'], bevel=0.003)
    tube('bath_toilet_brush', [(4.1, 0.10, -0.04), (4.1, 0.10, 0.38)], 0.015, M['pw'])
    tp = lathe('bath_toilet_paper', [(0, -0.05), (0.055, -0.05), (0.055, 0.05), (0, 0.05)], M['paper'], 24, location=(0, 0, 0))
    tp.data.transform(Matrix.Rotation(R90, 4, 'Y')); tp.location = (4.12, 0.92, 0.70)
    bm = bmesh.new()
    _box_bm(bm, (2.95, 1.60, 0.70), (3.49, 2.00, 0.84))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.04, segments=4, affect='EDGES')
    sink = mesh_obj('bath_sink', bm, M['porc'], origin=(3.22, 1.8, 0.70), smooth=True)
    cut = box('tmp_bcut', (3.0, 1.65, 0.73), (3.44, 1.92, 0.9), None, bevel=0.06, seg=4)
    boolean_cut(sink, cut); shade_smooth_auto(sink, 45)
    base = lathe('tmp_bfb', [(0, 0), (0.022, 0), (0.02, 0.09), (0, 0.09)], M['chrome'], 24, location=(3.22, 1.95, 0.84))
    spout = tube('tmp_bfs', [(3.22, 1.95, 0.91), (3.22, 1.86, 0.93), (3.22, 1.82, 0.90)], 0.01, M['chrome'])
    lev = boxes('tmp_bfl', [((3.215, 1.94, 0.93), (3.225, 2.0, 0.94))], M['chrome'], bevel=0.003)
    join('bath_sink_faucet', [base, spout, lev], origin=(3.22, 1.95, 0.84))
    boxes('bath_lower_cabinet', [((3.03, 1.66, 0.10), (3.41, 2.0, 0.66), 0), ((3.19, 1.655, 0.55), (3.25, 1.66, 0.57), 1)],
          [M['pw'], M['chrome']], origin=(3.03, 1.66, 0.10), bevel=0.006)
    boxes('fix_mirror_cabinet_body', [((2.92, 1.86, 1.15), (3.52, 2.0, 1.80)), ((2.94, 1.88, 1.47), (3.50, 2.0, 1.48))], M['pw'], bevel=0.003)
    boxes('bath_mirror_cabinet', [((2.92, 1.84, 1.15), (3.52, 1.86, 1.80), 0), ((2.93, 1.838, 1.16), (3.51, 1.84, 1.79), 1)],
          [M['pw'], M['mirror']], origin=(2.92, 1.85, 1.15), bevel=0.004)
    lathe('bath_toothpaste', [(0, 0), (0.018, 0), (0.018, 0.15), (0.01, 0.17), (0, 0.17)], M['pw'], 16, location=(2.99, 1.93, 1.48))
    tube('bath_toothbrush', [(3.07, 1.93, 1.49), (3.07, 1.93, 1.66)], 0.006, M['blue'])
    lathe('bath_cup', [(0, 0), (0.035, 0), (0.04, 0.10), (0.037, 0.10), (0.032, 0.004), (0, 0.004)], M['blue'], 24, location=(3.42, 1.65, 0.84))
    boxes('bath_soap', [((3.03, 1.67, 0.84), (3.11, 1.72, 0.865))], mat('M_Soap', (0.9, 0.85, 0.72, 1), 0.5), bevel=0.01, seg=2)
    tube('xprop_shower_riser', [(2.6, 0.03, 1.0), (2.6, 0.03, 1.95)], 0.011, M['chrome'])
    hd = lathe('bath_shower_head', [(0, 0), (0.05, 0), (0.055, 0.02), (0.018, 0.04), (0.015, 0.2), (0, 0.2)], M['chrome'], 28, location=(2.6, 0.07, 1.7))
    hd.rotation_euler = (math.radians(200), 0, 0)
    tube('xprop_shower_hose', [(2.6, 0.06, 0.95), (2.65, 0.2, 0.6), (2.62, 0.12, 1.2), (2.6, 0.08, 1.55)], 0.008, M['chrome'])
    boxes('bath_shower_tap', [((2.52, 0.0, 0.92), (2.68, 0.06, 0.98)), ((2.59, 0.06, 0.94), (2.61, 0.12, 0.96))], M['chrome'], bevel=0.006)
    lathe('bath_shampoo', [(0, 0), (0.035, 0), (0.035, 0.18), (0.012, 0.21), (0.012, 0.24), (0, 0.24)], M['pw'], 20, location=(2.35, 0.12, -0.045))
    lathe('bath_body_wash', [(0, 0), (0.035, 0), (0.035, 0.2), (0.012, 0.22), (0.012, 0.25), (0, 0.25)], M['green'], 20, location=(2.44, 0.10, -0.045))
    lathe('bath_drain', [(0, 0.0), (0.06, 0.0), (0.06, 0.003), (0.0, 0.003)], M['steel'], 32, location=(2.6, 0.55, -0.045))
    tube('xprop_towel_bar', [(2.30, 1.97, 1.35), (2.75, 1.97, 1.35)], 0.008, M['chrome'])
    tzprops3.towel_on_bar('bath_towel1', (2.32, 1.97, 1.35), (2.50, 1.97, 1.35), 0.80, mat('M_TowelGray', (0.55, 0.56, 0.58, 1), 1.0))
    tzprops3.towel_on_bar('bath_towel2', (2.53, 1.97, 1.35), (2.73, 1.97, 1.35), 0.66, mat('M_TowelBeige', (0.78, 0.72, 0.62, 1), 1.0))
    lathe('bath_laundry_bin', [(0, 0), (0.14, 0), (0.15, 0.4), (0.14, 0.4), (0.13, 0.02), (0, 0.02)], [M['pw']], 24, location=(4.0, 1.75, -0.045))
    tzprops2.dipper('xprop_dipper', (2.42, 0.32, -0.045))
    tzprops3.bath_stool('xprop_bath_stool', (2.82, 0.78, -0.045), mat('M_StoolPink', (0.92, 0.55, 0.62, 1), 0.45))
    tzprops3.wash_basin('xprop_wash_basin', (3.10, 0.30, -0.045), mat('M_BasinRed', (0.75, 0.12, 0.12, 1), 0.45))
    tzprops3.drain_hair('xprop_drain_hair', (2.6, 0.55, -0.045), mat('M_HairDark', (0.035, 0.025, 0.02, 1), 0.6))
    tzprops2.detergent('xprop_detergent', (4.05, 1.25, -0.045), rot=0.3)
    box('bath_floor_mat', (2.25, 1.15, -0.045), (2.70, 1.60, -0.035), mat('M_BathMat', (0.45, 0.55, 0.6, 1), 1.0), bevel=0.004)
    shoe('xprop_bath_slippers', (2.40, 0.95, -0.045), 0.26, mat('M_BathSlipper', (0.35, 0.55, 0.62, 1), 0.5), M['rubber'], rot=0.2, slipper=True)
    boxes('bath_window', [((WX + 0.02, 1.31, 1.61), (WX + 0.06, 1.69, 1.64), 0), ((WX + 0.02, 1.31, 1.96), (WX + 0.06, 1.69, 1.99), 0),
                          ((WX + 0.02, 1.31, 1.61), (WX + 0.06, 1.34, 1.99), 0), ((WX + 0.02, 1.66, 1.61), (WX + 0.06, 1.69, 1.99), 0),
                          ((WX + 0.037, 1.34, 1.64), (WX + 0.043, 1.66, 1.96), 1)],
          [M['pw'], mat('M_FrostedGlass', (0.85, 0.88, 0.9, 0.7), 0.6)], origin=(WX + 0.04, 1.5, 1.61), bevel=0.004)
    boxes('bath_ceiling', [((3.20, 0.85, 2.19), (3.65, 1.30, 2.2))], M['pw'], origin=(3.20, 1.075, 2.2), bevel=0.003)
    lathe('xprop_bath_light', [(0, -0.0), (0.12, 0.0), (0.12, -0.03), (0.0, -0.05)], M['led'], 32, location=(2.75, 1.3, 2.2))
    boxes('xprop_bath_vent_grille', [((3.85, 1.55, 2.19), (4.05, 1.75, 2.2))], M['pw'], bevel=0.003)

# ======================= HALLWAY + POLICE CORDON =======================
def hallway():
    C = 'Hall3F'
    box('arch_hall_floor', (-1.6, -1.8, -0.30), (6.6, -0.15, ST), M['stair'], bevel=0, collection=C)
    box('arch_hall_ceiling', (-1.6, -1.8, H - 0.05), (6.6, -0.15, H), M['ceil'], bevel=0, collection=C)
    box('arch_hall_wall_s', (-1.6, -1.95, ST), (6.6, -1.8, H), M['hconc'], bevel=0, collection=C)
    box('arch_hall_wall_e', (6.6, -1.95, ST), (6.75, -0.15, H), M['hconc'], bevel=0, collection=C)
    box('arch_hall_wall_302_ext', (2.2, -0.15, ST), (6.6, -0.14, H), M['hplaster'], bevel=0, collection=C)
    box('arch_hall_wall_west_ext', (-1.6, -0.15, ST), (0.12, -0.14, H), M['hplaster'], bevel=0, collection=C)
    for i in range(6):
        box(f'arch_hall_stair_{i}', (-1.6, -1.75 + i * 0.27, ST - 0.17 * (i + 1) - 0.02), (-0.4, -1.48 + i * 0.27, ST - 0.17 * (i + 1)),
            M['stair'], bevel=0.004, collection=C)
    tube('hall_stairs', [(-0.42, -1.75, ST + 0.9), (-0.42, -0.2, ST + 0.9 - 1.0)], 0.02, M['alu'], collection=C)
    boxes('hall_neighbor_door', [((4.9, -0.20, ST + 0.01), (5.8, -0.15, ST + 2.03), 0), ((5.0, -0.21, ST + 0.95), (5.08, -0.20, ST + 1.30), 1)],
          [M['doorsteel'], M['pb']], origin=(5.8, -0.175, ST), bevel=0.006, collection=C)
    lathe('hall_sensor', [(0, 0), (0.07, 0), (0.06, -0.04), (0, -0.05)], M['pw'], 28, location=(1.6, -0.9, H - 0.05), collection=C)
    lathe('hall_cctv', [(0, 0), (0.06, 0), (0.06, -0.02), (0.05, -0.07), (0, -0.08)], [M['pb']], 24, location=(6.3, -1.6, H - 0.05), collection=C)
    boxes('hall_mailbox', [((-1.58, -1.2, ST + 0.9), (-1.48, -0.6, ST + 1.3))], M['alu'], bevel=0.004, collection=C)
    boxes('hall_intercom', [((-1.58, -0.5, ST + 1.3), (-1.555, -0.36, ST + 1.52), 0), ((-1.556, -0.48, ST + 1.42), (-1.553, -0.38, ST + 1.5), 1)],
          [M['pw'], M['screen']], bevel=0.004, collection=C)
    # 빌라 복도 생활감: 소화기, 계량기함, 문에 붙은 전단지·스티커
    ext = [tzprops2.loft('tmp_fe', [(0, 0.07, 0.07, 0, 0), (0.42, 0.07, 0.07, 0, 0), (0.47, 0.04, 0.04, 0, 0), (0.50, 0.02, 0.02, 0, 0)],
                         [M['red']], steps=24, cap_top=True, location=(-1.45, -1.62, ST)),
           tube('tmp_feh', [(-1.45, -1.62, ST + 0.50), (-1.45, -1.55, ST + 0.55), (-1.45, -1.50, ST + 0.40)], 0.008, M['pb'])]
    join('xprop_fire_extinguisher', ext, origin=(-1.45, -1.62, ST))
    boxes('xprop_meter_box', [((2.6, -0.16, ST + 1.5), (3.2, -0.10, ST + 2.0), 0), ((2.62, -0.161, ST + 1.75), (3.18, -0.16, ST + 1.98), 1)],
          [M['pg'], M['glass']], bevel=0.004, collection=C)
    flyer = [box('tmp_fl1', (0.55, -0.1015, ST + 1.35), (0.75, -0.1005, ST + 1.62), mat('M_FlyerYellow', (0.95, 0.85, 0.35, 1), 0.7), bevel=0),
             label('tmp_fl1t', '치킨\n1588', 0.05, (0.65, -0.1018, ST + 1.50), (R90, 0, 0), M['inkred'], 0.0002, C),
             box('tmp_st1', (0.82, -0.1012, ST + 1.75), (0.90, -0.1005, ST + 1.80), mat('M_StickerWhite', (0.95, 0.95, 0.93, 1), 0.6), bevel=0),
             label('tmp_st1t', '가스점검', 0.012, (0.86, -0.1015, ST + 1.775), (R90, 0, 0), M['ink'], 0.0002, C)]
    j = join('xprop_door_flyers', flyer, origin=(0.7, -0.101, ST + 1.5), collection=C)
    parent(j, bpy.data.objects['entrance_door'])
    plate = box('tmp_plate', (0.40, -0.161, ST + 2.12), (0.60, -0.15, ST + 2.2), M['brass'], bevel=0.002, collection=C)
    ptx = label('tmp_302', '302', 0.045, (0.50, -0.1615, ST + 2.16), (R90, 0, 0), M['ink'], collection=C)
    join('xprop_hall_302_plate', [plate, ptx], origin=(0.5, -0.155, ST + 2.12), collection=C)
    tapes = []
    for (a, b) in [((-0.05, -0.16, ST + 1.0), (-0.6, -1.78, ST + 1.05)), ((1.25, -0.16, ST + 1.0), (1.9, -1.78, ST + 0.98))]:
        A, B = Vector(a), Vector(b)
        d = (B - A)
        bm = bmesh.new()
        k = 10
        prev = None
        for i in range(k + 1):
            t = i / k
            p = A + d * t; p.z -= 0.06 * math.sin(math.pi * t)
            v1 = bm.verts.new(p + Vector((0, 0, 0.035))); v2 = bm.verts.new(p - Vector((0, 0, 0.035)))
            if prev:
                bm.faces.new((prev[0], prev[1], v2, v1))
            prev = (v1, v2)
        tp = mesh_obj(f'tmp_tape{len(tapes)}', bm, M['tape'], collection=C, origin=a)
        sm = tp.modifiers.new('s', 'SOLIDIFY'); sm.thickness = 0.0015; bake(tp)
        tapes.append(tp)
    ang = math.atan2(-1.62, -0.55)
    tapes.append(label('tmp_tapetxt', '폴리스라인  출입금지', 0.026, (-0.33, -0.98, ST + 0.97), (R90, 0, ang + R90), M['tapeink'], 0.0003, C))
    join('xprop_police_tape', tapes, origin=(0.6, -0.9, ST + 1.0), collection=C)
    ppe = [box('tmp_ppe1', (1.20, -0.48, ST), (1.44, -0.20, ST + 0.10), M['pw'], bevel=0.004, collection=C),
           box('tmp_ppe2', (1.21, -0.46, ST + 0.10), (1.43, -0.33, ST + 0.16), M['nitrile'], bevel=0.004, collection=C),
           label('tmp_ppetxt', '니트릴 장갑 · 덧신', 0.016, (1.32, -0.481, ST + 0.05), (R90, 0, 0), M['ink'], 0.0003, C)]
    join('xprop_ppe_box', ppe, origin=(1.32, -0.34, ST), collection=C)

# ======================= CONTAINER CONTENTS (no empty interiors) =======================
def contents():
    L = tzprops2.loft
    def bowl(tag, x, y, z, r=0.06, h=0.055, m=None):
        return L(tag, [(0, r * 0.55, r * 0.55, 0, 0), (0.008, r * 0.6, r * 0.6, 0, 0), (h, r, r, 0, 0), (h, r * 0.95, r * 0.95, 0, 0), (0.01, r * 0.5, r * 0.5, 0, 0)],
                 [m or M['porc']], steps=28, location=(x, y, z))
    p = []
    for i in range(3):
        p.append(bowl(f'tmp_bb{i}', 0.17, 1.50, 1.47 + i * 0.03, 0.055))
        p.append(bowl(f'tmp_sb{i}', 0.17, 1.66, 1.47 + i * 0.035, 0.07))
    for i in range(6):
        p.append(L(f'tmp_pl{i}', [(0, 0.08, 0.08, 0, 0), (0.012, 0.11, 0.11, 0, 0), (0.014, 0.10, 0.10, 0, 0)], [M['porc']], steps=28, cap_bottom=True,
                   location=(0.17, 1.86, 1.47 + i * 0.016)))
    for i, yy in enumerate((1.50, 1.62, 1.74)):
        p.append(lathe(f'tmp_cup{i}', [(0, 0), (0.035, 0), (0.038, 0.09), (0.035, 0.09), (0.032, 0.006), (0, 0.006)], [M['porc'] if i else M['blue']], 24,
                       location=(0.17, yy, 1.815)))
    join('xprop_contents_upper1', p, origin=(0.17, 1.7, 1.47))
    p = []
    for i in range(4):
        p.append(boxes(f'tmp_hb{i}', [((0.07, 2.08, 1.47 + i * 0.035), (0.20, 2.20, 1.50 + i * 0.035))], [mat('M_InstantRice', (0.95, 0.93, 0.90, 1), 0.5)], bevel=0.006))
    for i in range(3):
        p.append(L(f'tmp_tc{i}', [(0, 0.042, 0.042, 0, 0), (0.035, 0.042, 0.042, 0, 0)], [mat('M_TunaCan', (0.75, 0.62, 0.20, 1), 0.4, 1.0)], steps=24,
                   cap_top=True, location=(0.24, 2.10 + i * 0.09, 1.47)))
    p.append(boxes('tmp_ram', [((0.06, 2.35, 1.815), (0.30, 2.60, 1.93))], [mat('M_RamyeonPack', (0.80, 0.15, 0.10, 1), 0.5)], bevel=0.02, seg=2))
    join('xprop_contents_upper2', p, origin=(0.17, 2.3, 1.47))
    p = [tube('tmp_trap', [(0.29, 2.27, 0.64), (0.29, 2.27, 0.48), (0.29, 2.32, 0.40), (0.29, 2.38, 0.46), (0.12, 2.38, 0.47), (0.02, 2.38, 0.47)], 0.02, M['pg']),
         tzprops2.detergent('tmp_ud', (0.45, 2.00, 0.12), rot=1.2),
         boxes('tmp_sp', [((0.40, 2.50, 0.12), (0.52, 2.62, 0.18))], [mat('M_SpongeYellow', (0.85, 0.7, 0.2, 1), 0.95)], bevel=0.005)]
    join('xprop_contents_undersink', p, origin=(0.3, 2.28, 0.12))
    p = [boxes('tmp_org', [((0.08, 1.40, 0.62), (0.54, 1.82, 0.625)), ((0.08, 1.54, 0.62), (0.54, 1.545, 0.67)), ((0.08, 1.68, 0.62), (0.54, 1.685, 0.67))], M['pg'], bevel=0.0)]
    for i in range(5):
        p.append(boxes(f'tmp_spn{i}', [((0.12, 1.43 + i * 0.022, 0.626), (0.30, 1.44 + i * 0.022, 0.632))], M['steel'], bevel=0.002))
        p.append(boxes(f'tmp_chp{i}', [((0.12, 1.58 + i * 0.016, 0.626), (0.34, 1.585 + i * 0.016, 0.631))], M['steel'], bevel=0.001))
    p.append(boxes('tmp_scis', [((0.14, 1.72, 0.626), (0.30, 1.76, 0.634))], [M['pb']], bevel=0.003))
    c = join('xprop_contents_drawer_utensils', p, origin=(0.3, 1.6, 0.62)); parent(c, bpy.data.objects['kitchen_drawer_utensils'])
    w = L('tmp_wrap', [(0, 0.03, 0.03, 0, 0), (0.30, 0.03, 0.03, 0, 0)], [mat('M_WrapBox', (0.85, 0.25, 0.2, 1), 0.5)], steps=6, cap_top=True)
    w.data.transform(Matrix.Rotation(math.radians(90), 4, 'Y')); w.location = (0.12, 1.47, 0.20)
    p = [w, boxes('tmp_bags', [((0.10, 1.62, 0.17), (0.40, 1.80, 0.23))], [M['bagw']], bevel=0.02, seg=2)]
    c = join('xprop_contents_drawer_misc', p, origin=(0.3, 1.6, 0.17)); parent(c, bpy.data.objects['kitchen_drawer_misc'])
    for nm, z0 in (('sleep_drawer_top', 0.56), ('sleep_drawer_mid', 0.325), ('sleep_drawer_bottom', 0.09)):
        p = []
        for i, (x, mm) in enumerate([(0.30, 'clothA'), (0.48, 'clothB'), (0.64, 'clothC')]):
            for k in range(2 if nm != 'sleep_drawer_bottom' else 3):
                p.append(box(f'tmp_fold{i}{k}', (x - 0.07, 5.62, z0 + k * 0.035), (x + 0.07, 5.86, z0 + k * 0.035 + 0.03), M[mm], bevel=0.008, seg=2))
        c = join('xprop_contents_' + nm, p, origin=(0.5, 5.74, z0)); parent(c, bpy.data.objects[nm])
    p = [box('tmp_rc1', (1.60, 3.36, 0.28), (1.68, 3.46, 0.2805), M['paper'], bevel=0), box('tmp_rc2', (1.70, 3.40, 0.28), (1.80, 3.48, 0.2805), M['paper'], bevel=0),
         L('tmp_band', [(0, 0.02, 0.02, 0, 0), (0.003, 0.02, 0.02, 0, 0)], [mat('M_RubberBand', (0.7, 0.45, 0.25, 1), 0.6)], steps=16, cap_bottom=False, location=(1.75, 3.52, 0.281))]
    c = join('xprop_contents_table_drawer', p, origin=(1.7, 3.45, 0.28)); parent(c, bpy.data.objects['living_table_drawer'])
    p = [lathe(f'tmp_tr{i}', [(0, -0.05), (0.055, -0.05), (0.055, 0.05), (0, 0.05)], M['paper'], 20, location=(3.12 + i * 0.12, 1.85, 0.16)) for i in range(2)]
    p.append(lathe('tmp_cln', [(0, 0), (0.04, 0), (0.04, 0.22), (0.015, 0.26), (0, 0.26)], M['blue'], 16, location=(3.33, 1.78, 0.11)))
    join('xprop_contents_bath_cabinet', p, origin=(3.2, 1.83, 0.11))

architecture(); entrance(); kitchen(); living(); bathroom(); hallway(); contents()

def labels_v5():
    """Printed product words on packaging (generic product names only, no brands)."""
    ink_w = mat('M_InkWhite', (0.95, 0.95, 0.94, 1), 0.5)
    def add_to(name, parts):
        o = bpy.data.objects[name]
        assert o.parent is None, name
        join(name, [o] + parts, origin=tuple(o.location))
    cx, cy, cz = 0.06, 3.36, 0.86
    parts = tzprops3.bottle_label('soy', cx, cy, cz + 0.05, cz + 0.12, 0.035, mat('M_LabelSoy', (0.50, 0.07, 0.05, 1), 0.5), '진간장', ink_w, FONT, 0.021)
    parts += tzprops3.bottle_label('oil', cx + 0.08, cy, cz + 0.06, cz + 0.15, 0.032, mat('M_LabelOil', (0.95, 0.82, 0.25, 1), 0.5), '식용유', M['inkred'], FONT, 0.021)
    parts += tzprops3.bottle_label('ses', cx + 0.04, cy + 0.07, cz + 0.035, cz + 0.10, 0.025, mat('M_LabelSesame', (0.55, 0.32, 0.08, 1), 0.5), '참기름', ink_w, FONT, 0.015)
    add_to('xprop_condiments', parts)
    add_to('bath_shampoo', tzprops3.bottle_label('sh', 2.35, 0.12, -0.045 + 0.05, -0.045 + 0.14, 0.035, mat('M_LabelShampoo', (0.48, 0.30, 0.60, 1), 0.5),
                                                 '샴푸', ink_w, FONT, 0.028, facing='+y'))
    add_to('bath_body_wash', tzprops3.bottle_label('bw', 2.44, 0.10, -0.045 + 0.05, -0.045 + 0.15, 0.035, mat('M_LabelBodyWash', (0.92, 0.92, 0.86, 1), 0.5),
                                                   '바디워시', M['green'], FONT, 0.017, facing='+y'))
    rm = [box('tmp_rmband', (0.3001, 2.36, 1.83), (0.3006, 2.59, 1.855), mat('M_LabelOrange', (0.95, 0.55, 0.10, 1), 0.5), bevel=0),
          label('tmp_rmtxt', '얼큰라면', 0.03, (0.3009, 2.475, 1.885), (R90, 0, R90), ink_w)]
    add_to('xprop_contents_upper2', rm + [label('tmp_rice', '즉석밥', 0.018, (0.2006, 2.14, 1.588), (R90, 0, R90), M['inkred'])])

labels_v5()
tzprops3.evidence_markers(FONT)

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
fbx = args[0] if args else os.path.join(os.path.dirname(__file__), '..', 'out', 'Room302.fbx')
blend = args[1] if len(args) > 1 else None
for o in list(bpy.data.objects):
    if o.name.startswith('tmp_'):
        print('WARN leftover', o.name)
        bpy.data.objects.remove(o, do_unlink=True)
names = sorted(o.name for o in bpy.data.objects)
print('OBJECTS', len(names))
open(os.path.splitext(fbx)[0] + '_objects.txt', 'w', encoding='utf-8').write('\n'.join(names))
export_fbx(fbx)
if blend:
    bpy.ops.wm.save_as_mainfile(filepath=blend)
print('EXPORTED', fbx)
