"""CASE 001 — 302호 원룸 + 3층 복도. Headless:
  blender -b -P blender/scripts/build_room302.py -- <out.fbx> <out.blend>

Object naming contract (Unity builder + TZPropCoverageAudit rely on it):
  <prop_id>        exact id from data/room302_interaction_manifest.json (interactive prop)
  arch_*           architecture (walls/floors/ceilings): collision + sound, not grabbable
  fix_*            fixed furniture body/carcass that hosts props
  xprop_*          extra interactive renderer not in the 140 manifest (must be registered)
Pivots: doors = hinge edge, drawers = front-center (slide along +X/-Y local), lids = hinge.
Layout (m): room X 0..3.6, Y 0..5.4 (Y+ = north window), ceiling 2.3, entrance step -0.12.
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(__file__))
import bpy, bmesh
from mathutils import Vector
from tzlib import *
from tzlib import _box_bm

random.seed(302)
reset()
H = 2.30          # ceiling height
T = 0.15          # exterior wall thickness
ST = -0.12        # entrance step level

# ---------------- materials (names are the Unity contract) ----------------
M = {
 'wall': mat('M_WallPaper', (0.86, 0.84, 0.80, 1), 0.85),
 'floor': mat('M_Floor', (0.55, 0.42, 0.30, 1), 0.45),
 'etile': mat('M_EntranceTile', (0.45, 0.43, 0.40, 1), 0.6),
 'btile': mat('M_BathTile', (0.88, 0.88, 0.86, 1), 0.25),
 'bfloor': mat('M_BathFloor', (0.55, 0.55, 0.53, 1), 0.5),
 'ceil': mat('M_Ceiling', (0.90, 0.90, 0.88, 1), 0.9),
 'cabw': mat('M_CabinetWhite', (0.90, 0.89, 0.86, 1), 0.35),
 'cabwood': mat('M_CabinetWood', (0.62, 0.48, 0.34, 1), 0.5),
 'counter': mat('M_Counter', (0.20, 0.20, 0.21, 1), 0.4),
 'steel': mat('M_Steel', (0.75, 0.75, 0.76, 1), 0.32, 1.0),
 'chrome': mat('M_Chrome', (0.9, 0.9, 0.92, 1), 0.08, 1.0),
 'doorsteel': mat('M_DoorSteel', (0.24, 0.20, 0.18, 1), 0.45, 0.3),
 'doorwhite': mat('M_DoorWhite', (0.88, 0.87, 0.84, 1), 0.4),
 'pw': mat('M_PlasticWhite', (0.92, 0.92, 0.90, 1), 0.4),
 'pb': mat('M_PlasticBlack', (0.03, 0.03, 0.035, 1), 0.35),
 'pg': mat('M_PlasticGray', (0.45, 0.46, 0.47, 1), 0.5),
 'porc': mat('M_Porcelain', (0.95, 0.95, 0.94, 1), 0.08),
 'glass': mat('M_Glass', (0.8, 0.88, 0.9, 0.25), 0.03),
 'mirror': mat('M_Mirror', (0.95, 0.95, 0.95, 1), 0.02, 1.0),
 'rubber': mat('M_Rubber', (0.05, 0.05, 0.05, 1), 0.8),
 'linen': mat('M_FabricLinen', (0.62, 0.64, 0.66, 1), 0.95),
 'cotton': mat('M_FabricCotton', (0.85, 0.83, 0.80, 1), 0.95),
 'sheet': mat('M_FabricSheet', (0.78, 0.80, 0.82, 1), 0.95),
 'oak': mat('M_WoodOak', (0.60, 0.45, 0.30, 1), 0.55),
 'mattress': mat('M_Mattress', (0.93, 0.92, 0.88, 1), 0.9),
 'hconc': mat('M_HallConcrete', (0.62, 0.61, 0.58, 1), 0.85),
 'hplaster': mat('M_HallPlaster', (0.80, 0.79, 0.74, 1), 0.85),
 'stair': mat('M_StairTerrazzo', (0.58, 0.56, 0.52, 1), 0.55),
 'carpet': mat('M_Carpet', (0.35, 0.30, 0.27, 1), 1.0),
 'paper': mat('M_Paper', (0.93, 0.92, 0.88, 1), 0.9),
 'card': mat('M_Cardboard', (0.62, 0.48, 0.32, 1), 0.9),
 'blood': mat('M_BloodDried', (0.16, 0.02, 0.02, 1), 0.35),
 'led': mat('M_LEDPanel', (1.0, 0.98, 0.94, 1), 0.5),
 'trim': mat('M_WoodTrim', (0.40, 0.30, 0.22, 1), 0.5),
 'food': mat('M_FoodSauce', (0.45, 0.12, 0.04, 1), 0.3),
 'bagw': mat('M_PlasticBagWhite', (0.92, 0.92, 0.90, 1), 0.45),
 'label': mat('M_LabelPrint', (0.80, 0.78, 0.72, 1), 0.7),
 'brass': mat('M_BrassDark', (0.55, 0.45, 0.28, 1), 0.35, 1.0),
 'screen': mat('M_ScreenOff', (0.02, 0.02, 0.025, 1), 0.08),
 'alu': mat('M_Aluminum', (0.70, 0.71, 0.72, 1), 0.4, 1.0),
 'red': mat('M_PlasticRed', (0.55, 0.06, 0.05, 1), 0.35),
 'green': mat('M_PlasticGreen', (0.20, 0.40, 0.22, 1), 0.4),
}

def W(name, mn, mx, m=None, col='Room302'):
    return box(name, mn, mx, m or M['wall'], bevel=0.0, collection=col)

# ======================= ARCHITECTURE =======================
def architecture():
    # south wall with entrance door opening X 0.1..1.0 (h 2.05 above step)
    W('arch_wall_south_a', (-T, -T, ST - 0.03), (0.1, 0, H))
    W('arch_wall_south_b', (1.0, -T, ST - 0.03), (2.0, 0, H))
    W('arch_wall_south_head', (0.1, -T, ST + 2.05), (1.0, 0, H))
    W('arch_wall_south_bath', (2.0, -T, -0.05), (3.6 + T, 0, H), M['btile'])
    # north wall with window X 0.9..2.4, z 0.9..2.1
    W('arch_wall_north_a', (-T, 5.4, 0), (0.9, 5.4 + T, H))
    W('arch_wall_north_b', (2.4, 5.4, 0), (3.6 + T, 5.4 + T, H))
    W('arch_wall_north_sill', (0.9, 5.4, 0), (2.4, 5.4 + T, 0.9))
    W('arch_wall_north_head', (0.9, 5.4, 2.1), (2.4, 5.4 + T, H))
    # west wall (kitchen line) and east wall
    W('arch_wall_west', (-T, 0, ST - 0.03), (0, 5.4, H))
    W('arch_wall_east', (3.6, 1.9, 0), (3.6 + T, 5.4, H))
    W('arch_wall_east_bath_a', (3.6, 0, -0.05), (3.6 + T, 1.2, H), M['btile'])
    W('arch_wall_east_bath_b', (3.6, 1.6, -0.05), (3.6 + T, 1.9, H), M['btile'])
    W('arch_wall_east_bath_sill', (3.6, 1.2, -0.05), (3.6 + T, 1.6, 1.6), M['btile'])
    W('arch_wall_east_bath_head', (3.6, 1.2, 2.0), (3.6 + T, 1.6, H), M['btile'])
    # bathroom partition: north (Y 1.8..1.9) and west (X 1.9..2.0) with door Y 0.95..1.7
    boxes('arch_wall_bath_north', [((2.0, 1.8, -0.05), (3.6, 1.805, H), 1), ((1.9, 1.805, -0.05), (3.6, 1.9, H), 0)],
          [M['wall'], M['btile']], bevel=0)
    boxes('arch_wall_bath_west_a', [((1.9, 0, -0.05), (1.995, 0.95, H), 0), ((1.995, 0, -0.05), (2.0, 0.95, H), 1)],
          [M['wall'], M['btile']], bevel=0)
    boxes('arch_wall_bath_west_b', [((1.9, 1.7, -0.05), (1.995, 1.8, H), 0), ((1.995, 1.7, -0.05), (2.0, 1.8, H), 1)],
          [M['wall'], M['btile']], bevel=0)
    W('arch_wall_bath_west_head', (1.9, 0.95, 2.0), (2.0, 1.7, H))
    # floors: main laminate, entrance tile step, bathroom tile (lower, with threshold)
    box('arch_floor_main', (0, 1.9, -0.15), (3.6, 5.4, 0), M['floor'], bevel=0)
    box('arch_floor_corridor', (1.1, 0, -0.15), (1.9, 1.9, 0), M['floor'], bevel=0)
    box('arch_floor_kitchen_front', (0, 1.2, -0.15), (1.1, 1.9, 0), M['floor'], bevel=0)
    box('arch_floor_entrance', (0, 0, -0.18), (1.1, 1.2, ST), M['etile'], bevel=0)
    box('arch_floor_bath', (2.0, 0, -0.18), (3.6, 1.8, -0.045), M['bfloor'], bevel=0)
    box('arch_bath_threshold', (1.9, 0.95, -0.15), (2.0, 1.7, 0.012), M['porc'], bevel=0.004)
    # ceilings
    box('arch_ceiling_main', (0, 0, H), (3.6, 5.4, H + 0.05), M['ceil'], bevel=0)
    # baseboards (걸레받이)
    for nm, a, b in [('n1', (0, 5.385, 0), (0.9, 5.4, 0.07)), ('n2', (2.4, 5.385, 0), (3.6, 5.4, 0.07)),
                     ('e', (3.585, 3.15, 0), (3.6, 5.4, 0.07)), ('w', (0, 3.6, 0), (0.015, 5.4, 0.07)),
                     ('bn', (1.9, 1.9, 0), (3.0, 1.915, 0.07)), ('bw', (1.885, 1.7, 0), (1.9, 1.9, 0.07)),
                     ('bw2', (1.885, 0.0, 0), (1.9, 0.95, 0.07))]:
        box('arch_baseboard_' + nm, a, b, M['trim'], bevel=0.002)
    # door frames
    boxes('arch_doorframe_bath', [((1.88, 0.92, -0.01), (2.02, 0.95, 2.03)), ((1.88, 1.70, -0.01), (2.02, 1.73, 2.03)),
                                  ((1.88, 0.92, 2.0), (2.02, 1.73, 2.03))], M['doorwhite'], bevel=0.003)
    # window frame (PVC 이중창) — sashes are the interactive prop
    boxes('arch_window_frame', [((0.9, 5.40, 0.9), (2.4, 5.55, 0.95)), ((0.9, 5.40, 2.05), (2.4, 5.55, 2.1)),
                                ((0.9, 5.40, 0.9), (0.95, 5.55, 2.1)), ((2.35, 5.40, 0.9), (2.4, 5.55, 2.1)),
                                ((0.9, 5.47, 0.93), (2.4, 5.48, 0.95))], M['pw'], bevel=0.004)
    box('arch_window_sill_inner', (0.88, 5.32, 0.88), (2.42, 5.42, 0.9), M['oak'], bevel=0.003)
    # backsplash tile on kitchen wall
    box('arch_kitchen_backsplash', (0, 1.35, 0.86), (0.006, 3.55, 1.45), M['btile'], bevel=0)
    # ceiling LED panel (fixture, light source anchor) and bathroom ceiling
    lathe('fix_ceiling_light', [(0, -0.002), (0.22, -0.002), (0.23, -0.02), (0.22, -0.045), (0.0, -0.045)],
          M['led'], 40, location=(1.8, 3.4, H))
    box('arch_ceiling_bath', (2.0, 0, 2.2), (3.6, 1.8, 2.25), M['pw'], bevel=0)
    # aircon unit (wall mounted) — extra renderer, registered as xprop
    boxes('xprop_aircon_unit', [((3.35, 3.4, 1.95), (3.6, 4.3, 2.22)), ((3.33, 3.42, 1.97), (3.35, 4.28, 2.02), 1)],
          [M['pw'], M['pg']], bevel=0.02, seg=3)

# ======================= ENTRANCE =======================
def entrance():
    # steel front door, hinge at X 1.0 (east jamb), opens outward (-Y)
    d = boxes('entrance_door', [((0.12, -0.10, ST + 0.01), (0.98, -0.05, ST + 2.03), 0),
                                ((0.16, -0.051, ST + 0.15), (0.94, -0.049, ST + 1.95), 0)],
              [M['doorsteel']], origin=(0.98, -0.075, ST), bevel=0.006, seg=2)
    lock = boxes('entrance_lock', [((0.17, -0.05, ST + 0.95), (0.25, -0.02, ST + 1.30), 0),
                                   ((0.18, -0.021, ST + 1.0), (0.24, -0.016, ST + 1.12), 1),
                                   ((0.185, -0.03, ST + 1.15), (0.235, -0.0, ST + 1.24), 0)],
                 [M['pb'], M['screen']], origin=(0.21, -0.035, ST + 1.1), bevel=0.006, seg=2)
    lock_out = boxes('xprop_entrance_lock_outside', [((0.17, -0.13, ST + 0.95), (0.25, -0.10, ST + 1.30), 0),
                                                     ((0.18, -0.134, ST + 1.0), (0.24, -0.129, ST + 1.22), 1)],
                     [M['pb'], M['screen']], origin=(0.21, -0.115, ST + 1.1), bevel=0.006, seg=2)
    parent(lock, d); parent(lock_out, d)
    boxes('entrance_doorframe', [((0.07, -T, ST), (0.12, 0.0, ST + 2.08)), ((0.98, -T, ST), (1.03, 0.0, ST + 2.08)),
                                 ((0.07, -T, ST + 2.03), (1.03, 0.0, ST + 2.08))], M['doorsteel'], bevel=0.003)
    # shoe cabinet carcass + door (hinge at Y 0.15 side)
    boxes('fix_shoe_cabinet', [((0.0, 0.15, ST + 0.06), (0.36, 0.17, ST + 1.0)), ((0.0, 0.73, ST + 0.06), (0.36, 0.75, ST + 1.0)),
                               ((0.0, 0.15, ST + 0.98), (0.37, 0.75, ST + 1.02)), ((0.0, 0.15, ST + 0.06), (0.36, 0.75, ST + 0.08)),
                               ((0.0, 0.15, ST + 0.06), (0.02, 0.75, ST + 1.0)), ((0.02, 0.17, ST), (0.33, 0.73, ST + 0.06))],
          M['cabw'], bevel=0.002)
    boxes('entrance_shoe_shelf', [((0.02, 0.17, ST + 0.38), (0.34, 0.73, ST + 0.395)), ((0.02, 0.17, ST + 0.68), (0.34, 0.73, ST + 0.695))],
          M['cabw'], bevel=0.002)
    boxes('entrance_shoe_cabinet', [((0.36, 0.152, ST + 0.08), (0.38, 0.748, ST + 0.98), 0),
                                    ((0.38, 0.69, ST + 0.45), (0.395, 0.70, ST + 0.62), 1)],
          [M['cabw'], M['alu']], origin=(0.37, 0.152, ST), bevel=0.003)
    # shoes inside the cabinet shelf and on the tile floor
    shoe('entrance_shoes1', (0.55, 0.45, ST), 0.27, M['pw'], M['rubber'], rot=0.25)
    shoe('entrance_shoes2', (0.80, 0.82, ST), 0.25, M['pg'], M['rubber'], rot=-0.35, slipper=True)
    shoe('entrance_shoes3', (0.20, 0.45, ST + 0.395), 0.26, M['pb'], M['rubber'], rot=1.57)
    box('entrance_mat', (0.15, 0.95, ST), (0.95, 1.18, ST + 0.008), M['carpet'], bevel=0.002)
    box('entrance_floor_trim', (0.0, 1.19, ST), (1.1, 1.22, 0.004), M['trim'], bevel=0.003)
    box('xprop_entrance_floor_trim_side', (1.09, 0.0, ST), (1.12, 1.22, 0.004), M['trim'], bevel=0.003)
    boxes('entrance_entry_mirror', [((0.0, 0.25, 1.05), (0.02, 0.65, 1.75), 0), ((0.02, 0.26, 1.06), (0.022, 0.64, 1.74), 1)],
          [M['alu'], M['mirror']], bevel=0.003)
    boxes('entrance_key_hook', [((0.0, 0.90, 1.45), (0.012, 1.05, 1.49)), ((0.012, 0.93, 1.455), (0.04, 0.935, 1.465)),
                                ((0.012, 0.98, 1.455), (0.04, 0.985, 1.465)), ((0.012, 1.02, 1.455), (0.04, 1.025, 1.465))],
          M['oak'], bevel=0.002)
    switch_plate('entrance_switch', (1.15, 0.0, 1.2), facing='+y')
    boxes('living_heater_remote', [((1.45, 0.0, 1.35), (1.58, 0.025, 1.5), 0), ((1.47, 0.025, 1.40), (1.56, 0.027, 1.47), 1)],
          [M['pw'], M['screen']], bevel=0.004)
    # umbrella leaning in corner, delivery box on tile
    tube('entrance_umbrella', [(0.06, 1.12, ST + 0.01), (0.07, 1.10, ST + 0.35), (0.08, 1.08, ST + 0.62)], 0.03, M['pb'])
    box('entrance_delivery_box', (0.55, 0.12, ST), (0.90, 0.40, ST + 0.22), M['card'], bevel=0.004)

def shoe(name, at, length, upper, sole, rot=0.0, slipper=False):
    """Low-poly-but-proper shoe: sole + rounded upper (subdivided), for 1~2m read distance."""
    x, y, z = at
    bm = bmesh.new()
    w = length * 0.38
    vs = _box_bm(bm, (-length / 2, -w / 2, 0), (length / 2, w / 2, 0.025))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.01, segments=2, affect='EDGES')
    for f in bm.faces:
        f.material_index = 1
    up = bmesh.new()
    h = 0.03 if slipper else 0.075
    _box_bm(up, (-length * 0.48, -w * 0.46, 0.02), ((0.15 if slipper else 0.48) * length, w * 0.46, 0.02 + h))
    bmesh.ops.subdivide_edges(up, edges=list(up.edges), cuts=2, use_grid_fill=True)
    bmesh.ops.bevel(up, geom=list(up.edges), offset=0.008, segments=1, affect='EDGES')
    for v in up.verts:
        t = (v.co.x + length / 2) / length
        if v.co.z > 0.03:
            v.co.z -= (0.035 * max(0, t - 0.55)) if not slipper else 0
            v.co.y *= 0.85 + 0.15 * math.sin(math.pi * min(1, t + 0.1))
    me = bpy.data.meshes.new('t'); up.to_mesh(me); up.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=__import__('mathutils').Matrix.Rotation(rot, 3, 'Z'))
    for v in bm.verts:
        v.co += Vector((x, y, z))
    o = mesh_obj(name, bm, [upper, sole], origin=(x, y, z))
    # second shoe of the pair
    return o

def switch_plate(name, at, facing='+y', double=False):
    x, y, z = at
    if facing in ('+y', '-y'):
        s = 1 if facing == '+y' else -1
        parts = [((x - 0.04, y, z - 0.06), (x + 0.04, y + s * 0.012, z + 0.06), 0) if s > 0 else
                 ((x - 0.04, y + s * 0.012, z - 0.06), (x + 0.04, y, z + 0.06), 0)]
        rk = ((x - 0.015, min(y + s * 0.012, y + s * 0.02), z - 0.03), (x + 0.015, max(y + s * 0.012, y + s * 0.02), z + 0.03), 0)
    else:
        s = 1 if facing == '+x' else -1
        parts = [((x, y - 0.04, z - 0.06), (x + s * 0.012, y + 0.04, z + 0.06), 0) if s > 0 else
                 ((x + s * 0.012, y - 0.04, z - 0.06), (x, y + 0.04, z + 0.06), 0)]
        rk = ((min(x + s * 0.012, x + s * 0.02), y - 0.015, z - 0.03), (max(x + s * 0.012, x + s * 0.02), y + 0.015, z + 0.03), 0)
    parts.append(rk)
    return boxes(name, parts, M['pw'], origin=at, bevel=0.003)

# ======================= KITCHEN =======================
def kitchen():
    y0, y1 = 1.35, 3.55
    D = 0.60
    # carcass: sides, back, bottom, toe kick, partitions (fixed)
    boxes('fix_kitchen_carcass', [((0.0, y0, 0.1), (D - 0.02, y0 + 0.02, 0.82)), ((0.0, y1 - 0.02, 0.1), (D - 0.02, y1, 0.82)),
                                  ((0.0, y0, 0.1), (0.02, y1, 0.82)), ((0.0, y0, 0.1), (D - 0.02, y1, 0.12)),
                                  ((0.04, y0 + 0.02, 0.0), (D - 0.06, y1 - 0.02, 0.1)),
                                  ((0.0, 1.85, 0.1), (D - 0.02, 1.87, 0.82)), ((0.0, 2.65, 0.1), (D - 0.02, 2.67, 0.82)),
                                  ((0.02, 2.67, 0.46), (D - 0.03, 3.53, 0.48)),
                                  ((D - 0.02, 2.67, 0.12), (D, 3.53, 0.80))],  # stove section false front
          M['cabw'], bevel=0.002)
    # countertop with sink cut-out
    top = box('fix_kitchen_counter', (0.0, y0, 0.82), (D + 0.02, y1, 0.86), M['counter'], bevel=0.003)
    cutter = box('tmp_cut', (0.08, 2.00, 0.7), (0.50, 2.50, 0.95), None, bevel=0.03, seg=3)
    boolean_cut(top, cutter); rewrap_uv(top)
    # stainless basin: open box, solidified
    bm = bmesh.new()
    _box_bm(bm, (0.085, 2.005, 0.64), (0.495, 2.495, 0.86))
    top_face = max(bm.faces, key=lambda f: f.calc_center_median().z)
    bmesh.ops.delete(bm, geom=[top_face], context='FACES_ONLY')
    bmesh.ops.bevel(bm, geom=[e for e in bm.edges if not e.is_boundary], offset=0.035, segments=4, affect='EDGES')
    sink = mesh_obj('kitchen_sink', bm, M['steel'], origin=(0.29, 2.25, 0.64))
    sm = sink.modifiers.new('s', 'SOLIDIFY'); sm.thickness = 0.008; sm.offset = 1
    bake(sink); shade_smooth_auto(sink)
    lathe('kitchen_drain_cover', [(0, 0.004), (0.045, 0.004), (0.05, 0.0), (0.0, 0.0)], M['steel'], 32, location=(0.29, 2.25, 0.642))
    # faucet: base + gooseneck + lever (switch prop)
    base = lathe('tmp_fb', [(0, 0.0), (0.028, 0.0), (0.026, 0.05), (0.018, 0.06), (0, 0.06)], M['chrome'], 32, location=(0.06, 2.25, 0.86))
    neck = tube('tmp_fn', [(0.06, 2.25, 0.9), (0.06, 2.25, 1.12), (0.14, 2.25, 1.16), (0.22, 2.25, 1.08)], 0.012, M['chrome'])
    lever = boxes('tmp_fl', [((0.03, 2.244, 0.92), (0.10, 2.256, 0.932))], M['chrome'], bevel=0.003)
    join('kitchen_faucet', [base, neck, lever], origin=(0.06, 2.25, 0.86))
    # drawers (front-center pivot, slide +X). Real tray interiors.
    drawer('kitchen_drawer_utensils', (0.02, y0 + 0.02, 0.58), (D, 1.85, 0.80), M['cabw'], M['cabw'], axis='x')
    drawer('kitchen_drawer_misc', (0.02, y0 + 0.02, 0.13), (D, 1.85, 0.57), M['cabw'], M['cabw'], axis='x')
    # under-sink doors: hinge at outer edges
    cab_door('kitchen_under_sink_left', (D, 1.87, 0.13), (D + 0.018, 2.26, 0.80), hinge='ymin')
    cab_door('kitchen_under_sink_right', (D, 2.26, 0.13), (D + 0.018, 2.65, 0.80), hinge='ymax')
    # gas range (2구) inset + knobs; it's the switch prop
    rng = boxes('kitchen_stove', [((0.08, 2.82, 0.86), (0.54, 3.42, 0.875), 0),
                                  ((D - 0.005, 2.95, 0.70), (D + 0.012, 3.30, 0.80), 1)], [M['pb'], M['steel']],
                origin=(0.31, 3.12, 0.86), bevel=0.004)
    for i, yy in enumerate((2.97, 3.27)):
        b = lathe(f'tmp_burner{i}', [(0, 0.018), (0.06, 0.018), (0.075, 0.012), (0.075, 0.0), (0, 0)], M['pb'], 28, location=(0.3, yy, 0.875))
        parent(b, rng)
    # hood
    boxes('kitchen_hood', [((0.0, 2.80, 1.55), (0.50, 3.44, 1.70), 0), ((0.38, 2.82, 1.545), (0.48, 3.42, 1.552), 1)],
          [M['steel'], M['pg']], bevel=0.006, seg=2)
    # upper cabinets (carcass fixed + 2 doors)
    boxes('fix_kitchen_upper', [((0.0, 1.35, 1.45), (0.33, 1.37, 2.15)), ((0.0, 2.43, 1.45), (0.33, 2.45, 2.15)),
                                ((0.0, 1.35, 1.45), (0.33, 2.45, 1.47)), ((0.0, 1.35, 2.13), (0.33, 2.45, 2.15)),
                                ((0.0, 1.35, 1.45), (0.02, 2.45, 2.15)), ((0.02, 1.37, 1.80), (0.31, 2.43, 1.815))],
          M['cabw'], bevel=0.002)
    cab_door('kitchen_overhead_cabinet1', (0.33, 1.352, 1.452), (0.348, 1.898, 2.148), hinge='ymin', handle_low=True)
    cab_door('kitchen_overhead_cabinet2', (0.33, 1.902, 1.452), (0.348, 2.448, 2.148), hinge='ymax', handle_low=True)
    # countertop items
    dish_rack()
    lathe('kitchen_mug', [(0, 0), (0.038, 0), (0.042, 0.004), (0.043, 0.095), (0.039, 0.095), (0.038, 0.008), (0, 0.008)],
          M['porc'], 36, location=(0.42, 1.62, 0.86))
    handle = tube('tmp_mh', [(0.462, 1.62, 0.835 + 0.06), (0.49, 1.62, 0.835 + 0.05), (0.49, 1.62, 0.835 + 0.0 + 0.03), (0.462, 1.62, 0.835 + 0.02)], 0.006, M['porc'])
    join('kitchen_mug', [bpy.data.objects['kitchen_mug'], handle], origin=(0.42, 1.62, 0.86))
    boxes('kitchen_cutting_board', [((0.10, 2.62, 0.86), (0.42, 2.88, 0.875))], M['oak'], bevel=0.004)
    knife('kitchen_kitchen_knife', (0.20, 2.75, 0.876))
    boxes('kitchen_knife_rack', [((0.04, 3.46, 0.86), (0.13, 3.53, 1.08))], M['oak'], bevel=0.006)
    lathe('kitchen_dish_soap', [(0, 0), (0.03, 0), (0.032, 0.15), (0.012, 0.17), (0.012, 0.2), (0, 0.2)], M['green'], 24, location=(0.08, 2.58, 0.86))
    boxes('kitchen_sponge', [((0.08, 1.98, 0.86), (0.15, 2.07, 0.885), 0), ((0.08, 1.98, 0.885), (0.15, 2.07, 0.892), 1)],
          [mat('M_SpongeYellow', (0.85, 0.7, 0.2, 1), 0.95), M['green']], bevel=0.004)
    lathe('kitchen_pot', [(0, 0), (0.10, 0), (0.105, 0.005), (0.105, 0.12), (0.1, 0.12), (0.098, 0.006), (0, 0.006)],
          M['steel'], 40, location=(0.30, 2.97, 0.89))
    lathe('kitchen_pan', [(0, 0), (0.11, 0), (0.13, 0.04), (0.125, 0.042), (0.105, 0.006), (0, 0.006)], M['pb'], 40,
          location=(0.30, 3.27, 0.89))
    noodle('kitchen_instant_noodle1', (0.47, 3.22, 0.86))
    noodle('kitchen_instant_noodle2', (0.47, 3.36, 0.86))
    lathe('kitchen_bin', [(0, 0), (0.12, 0), (0.135, 0.38), (0.0, 0.38)], M['pg'], 32, location=(0.85, 1.55, 0))
    lathe('kitchen_bin_liner', [(0.128, 0.30), (0.14, 0.39), (0.13, 0.40)], M['bagw'], 32, location=(0.85, 1.55, 0))
    fridge()

def dish_rack():
    parts = []
    for i in range(8):
        yy = 2.55 + i * 0.012
    rack = boxes('kitchen_dish_rack', [((0.05, 2.46, 0.86), (0.40, 2.50, 0.87)), ((0.05, 2.46, 0.86), (0.06, 2.62, 1.0)),
                                       ((0.39, 2.46, 0.86), (0.40, 2.62, 1.0))], M['steel'], bevel=0.002)
    lathe('kitchen_plate', [(0, 0), (0.08, 0), (0.11, 0.02), (0.105, 0.022), (0.075, 0.004), (0, 0.004)], M['porc'], 40,
          location=(0.22, 2.54, 0.87))
    pl = bpy.data.objects['kitchen_plate']; pl.rotation_euler = (math.radians(75), 0, 0)
    boxes('kitchen_spoon', [((0.30, 2.50, 0.87), (0.31, 2.52, 1.02))], M['steel'], bevel=0.003)
    boxes('kitchen_chopsticks', [((0.33, 2.50, 0.87), (0.335, 2.505, 1.08)), ((0.34, 2.50, 0.87), (0.345, 2.505, 1.08))], M['steel'], bevel=0.001)

def knife(name, at):
    x, y, z = at
    bm = bmesh.new()
    pts = [(0, 0), (0.17, 0.0), (0.2, 0.012), (0.17, 0.035), (0.0, 0.032)]
    vs_top = [bm.verts.new((x + px, y + py - 0.016, z + 0.004)) for px, py in pts]
    vs_bot = [bm.verts.new((x + px, y + py - 0.016, z)) for px, py in pts]
    bm.faces.new(vs_top); bm.faces.new(list(reversed(vs_bot)))
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((vs_bot[i], vs_bot[j], vs_top[j], vs_top[i]))
    bm.normal_update()
    blade = mesh_obj('tmp_blade', bm, M['steel'], origin=at)
    hnd = boxes('tmp_handle', [((x - 0.12, y - 0.012, z - 0.004), (x, y + 0.012, z + 0.018))], M['pb'], bevel=0.006)
    return join(name, [blade, hnd], origin=at)

def noodle(name, at):
    x, y, z = at
    o = lathe(name, [(0, 0), (0.04, 0), (0.055, 0.075), (0.056, 0.08), (0, 0.08)], [M['red']], 32, location=at)
    return o

def drawer(name, mn, mx, front_mat, box_mat, axis='x'):
    """Drawer = front panel + real tray (bottom, sides, back) with handle. Pivot front-center."""
    x0, y0, z0 = mn; x1, y1, z1 = mx
    ft = 0.018
    parts = [((x1 - ft, y0 + 0.002, z0 + 0.002), (x1, y1 - 0.002, z1 - 0.002), 0),     # front
             ((x0 + 0.03, y0 + 0.03, z0 + 0.03), (x1 - ft, y1 - 0.03, z0 + 0.042), 1),  # bottom
             ((x0 + 0.03, y0 + 0.03, z0 + 0.03), (x1 - ft, y0 + 0.042, z1 - 0.06), 1),  # side
             ((x0 + 0.03, y1 - 0.042, z0 + 0.03), (x1 - ft, y1 - 0.03, z1 - 0.06), 1),  # side
             ((x0 + 0.03, y0 + 0.03, z0 + 0.03), (x0 + 0.042, y1 - 0.03, z1 - 0.06), 1),  # back
             ((x1, (y0 + y1) / 2 - 0.08, z1 - 0.06), (x1 + 0.022, (y0 + y1) / 2 + 0.08, z1 - 0.045), 2)]  # handle
    return boxes(name, parts, [front_mat, box_mat, M['alu']], origin=(x1, (y0 + y1) / 2, (z0 + z1) / 2), bevel=0.002)

def drawer_y(name, mn, mx, front_mat, box_mat):
    """Drawer facing -Y (front at y0)."""
    x0, y0, z0 = mn; x1, y1, z1 = mx
    ft = 0.018
    parts = [((x0 + 0.002, y0, z0 + 0.002), (x1 - 0.002, y0 + ft, z1 - 0.002), 0),
             ((x0 + 0.03, y0 + ft, z0 + 0.03), (x1 - 0.03, y1 - 0.03, z0 + 0.042), 1),
             ((x0 + 0.03, y0 + ft, z0 + 0.03), (x0 + 0.042, y1 - 0.03, z1 - 0.05), 1),
             ((x1 - 0.042, y0 + ft, z0 + 0.03), (x1 - 0.03, y1 - 0.03, z1 - 0.05), 1),
             ((x0 + 0.03, y1 - 0.042, z0 + 0.03), (x1 - 0.03, y1 - 0.03, z1 - 0.05), 1),
             (((x0 + x1) / 2 - 0.06, y0 - 0.018, (z0 + z1) / 2 - 0.008), ((x0 + x1) / 2 + 0.06, y0, (z0 + z1) / 2 + 0.008), 2)]
    return boxes(name, parts, [front_mat, box_mat, M['alu']], origin=((x0 + x1) / 2, y0, (z0 + z1) / 2), bevel=0.002)

def drawer_y_plus(name, mn, mx, front_mat, box_mat):
    """Drawer facing +Y (front at y1)."""
    x0, y0, z0 = mn; x1, y1, z1 = mx
    ft = 0.018
    parts = [((x0 + 0.002, y1 - ft, z0 + 0.002), (x1 - 0.002, y1, z1 - 0.002), 0),
             ((x0 + 0.03, y0 + 0.03, z0 + 0.03), (x1 - 0.03, y1 - ft, z0 + 0.042), 1),
             ((x0 + 0.03, y0 + 0.03, z0 + 0.03), (x0 + 0.042, y1 - ft, z1 - 0.05), 1),
             ((x1 - 0.042, y0 + 0.03, z0 + 0.03), (x1 - 0.03, y1 - ft, z1 - 0.05), 1),
             ((x0 + 0.03, y0 + 0.03, z0 + 0.03), (x1 - 0.03, y0 + 0.042, z1 - 0.05), 1),
             (((x0 + x1) / 2 - 0.06, y1, (z0 + z1) / 2 - 0.008), ((x0 + x1) / 2 + 0.06, y1 + 0.018, (z0 + z1) / 2 + 0.008), 2)]
    return boxes(name, parts, [front_mat, box_mat, M['alu']], origin=((x0 + x1) / 2, y1, (z0 + z1) / 2), bevel=0.002)

def cab_door(name, mn, mx, hinge='ymin', handle_low=False, material=None, handle=True):
    x0, y0, z0 = mn; x1, y1, z1 = mx
    parts = [(mn, mx, 0)]
    if handle:
        hz = (z0 + 0.06, z0 + 0.20) if handle_low else (z1 - 0.20, z1 - 0.06)
        hy = (y1 - 0.05, y1 - 0.04) if hinge == 'ymin' else (y0 + 0.04, y0 + 0.05)
        parts.append(((x1, hy[0], hz[0]), (x1 + 0.02, hy[1], hz[1]), 1))
    piv = (x0, y0 if hinge == 'ymin' else y1, z0)
    return boxes(name, parts, [material or M['cabw'], M['alu']], origin=piv, bevel=0.003)

def fridge():
    x0, x1, y0, y1 = 0.0, 0.57, 3.62, 4.22
    th = 0.03
    # hollow body: outer shell open at +X, divider between freezer/fridge
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
    # doors hinge on north edge (y1), open toward -Y... realistic: hinge right side when facing fridge
    door_parts = lambda z0, z1: [((x1, y0, z0), (x1 + 0.05, y1, z1), 0),
                                 ((x1 - 0.06, y0 + 0.05, z0 + 0.12), (x1, y1 - 0.05, z0 + 0.135), 1),
                                 ((x1 - 0.06, y0 + 0.05, z0 + 0.12), (x1, y0 + 0.06, z0 + 0.2), 1),
                                 ((x1 - 0.06, y1 - 0.06, z0 + 0.12), (x1, y1 - 0.05, z0 + 0.2), 1),
                                 ((x1 + 0.05, y0 + 0.02, z1 - 0.25 if z1 < 1 else z0 + 0.03), (x1 + 0.065, y0 + 0.045, (z1 - 0.03) if z1 < 1 else z0 + 0.2), 2)]
    boxes('kitchen_fridge_door', door_parts(0.03, 0.95), [M['pw'], M['pw'], M['pg']], origin=(x1 + 0.025, y1, 0.03), bevel=0.008, seg=2)
    boxes('kitchen_fridge_freezer', door_parts(1.01, 1.44)[:1] + [door_parts(1.01, 1.44)[4]], [M['pw'], M['pw'], M['pg']],
          origin=(x1 + 0.025, y1, 1.01), bevel=0.008, seg=2)
    # fridge contents (children of fridge door container in manifest: inside body)
    lathe('kitchen_fridge_bottle', [(0, 0), (0.035, 0), (0.037, 0.2), (0.015, 0.26), (0.014, 0.29), (0, 0.29)], M['glass'], 24,
          location=(0.30, 3.72, 0.366))
    boxes('kitchen_fridge_milk', [((0.25, 3.82, 0.366), (0.32, 3.89, 0.56), 0), ((0.25, 3.82, 0.56), (0.32, 3.89, 0.59), 1)],
          [M['pw'], mat('M_MilkPrint', (0.25, 0.45, 0.75, 1), 0.6)], bevel=0.003)
    boxes('kitchen_fridge_container', [((0.12, 3.95, 0.666), (0.30, 4.15, 0.74), 0), ((0.12, 3.95, 0.74), (0.30, 4.15, 0.755), 1)],
          [M['glass'], M['red']], bevel=0.008)
    boxes('kitchen_fridge_egg', [((0.32, 3.95, 0.666), (0.46, 4.15, 0.71))], M['pw'], bevel=0.005)
    boxes('kitchen_fridge_note', [((x1 + 0.05, 3.80, 0.78), (x1 + 0.052, 3.93, 0.90))], M['paper'], bevel=0.0)
    lathe('kitchen_fridge_magnet', [(0, 0), (0.015, 0), (0.015, 0.008), (0, 0.008)], M['red'], 20, location=(x1 + 0.052, 3.865, 0.89))
    bpy.data.objects['kitchen_fridge_magnet'].rotation_euler = (0, math.radians(90), 0)
    # microwave on top of fridge
    boxes('fix_microwave_body', [((0.05, 3.66, 1.45), (0.42, 4.18, 1.73), 0), ((0.05, 4.03, 1.47), (0.425, 4.17, 1.71), 1)],
          [M['pw'], M['pg']], bevel=0.008, seg=2)
    boxes('kitchen_microwave_door', [((0.42, 3.67, 1.47), (0.44, 4.02, 1.71), 0), ((0.44, 3.72, 1.51), (0.442, 3.97, 1.67), 1)],
          [M['pw'], M['screen']], origin=(0.43, 3.67, 1.47), bevel=0.005)
    boxes('kitchen_microwave_buttons', [((0.425, 4.06, 1.60), (0.432, 4.14, 1.68), 0), ((0.425, 4.08, 1.52), (0.435, 4.12, 1.56), 1)],
          [M['screen'], M['pg']], bevel=0.003)

# ======================= LIVING / SLEEP =======================
def living():
    # folding low table with small drawer
    boxes('living_table', [((1.0, 2.7, 0.30), (1.8, 3.3, 0.33)), ((1.04, 2.74, 0.0), (1.07, 2.77, 0.30)),
                           ((1.73, 2.74, 0.0), (1.76, 2.77, 0.30)), ((1.04, 3.23, 0.0), (1.07, 3.26, 0.30)),
                           ((1.73, 3.23, 0.0), (1.76, 3.26, 0.30))], M['oak'], bevel=0.004)
    drawer_y('living_table_drawer', (1.25, 2.72, 0.245), (1.55, 3.0, 0.298), M['oak'], M['oak'])
    # overturned chair (on its side)
    chair('living_chair', (1.95, 3.55, 0.0))
    # delivery: bag + two containers + spoon + can + napkin
    plastic_bag('living_food_bag', (1.22, 2.87, 0.33), (0.30, 0.20, 0.22), M['bagw'], knot=True)
    lathe('living_food_container1', [(0, 0), (0.075, 0), (0.085, 0.06), (0.088, 0.065), (0, 0.065)], [M['pb']], 32, location=(1.47, 2.90, 0.33))
    lathe('living_food_container2', [(0, 0), (0.06, 0), (0.07, 0.05), (0.072, 0.054), (0, 0.054)], [mat('M_FoodLid', (0.8, 0.8, 0.78, 0.6), 0.2)], 32,
          location=(1.62, 3.05, 0.33))
    boxes('living_disposable_spoon', [((1.40, 3.12, 0.33), (1.56, 3.135, 0.336))], M['pw'], bevel=0.002)
    lathe('living_cola_can', [(0, 0), (0.026, 0), (0.033, 0.01), (0.033, 0.11), (0.027, 0.122), (0, 0.122)], M['red'], 28,
          location=(1.70, 2.82, 0.33))
    napkin = box('living_napkin', (1.25, 3.10, 0.33), (1.33, 3.18, 0.37), M['paper'], bevel=0.02, seg=3)
    # floor evidence traces: decal-like thin meshes (not auto-identifying)
    blood_decal('living_floor_blood', (1.55, 3.75, 0.0015), 0.22)
    box('living_footprint', (1.25, 3.95, 0.0), (1.33, 4.22, 0.0012), mat('M_FootprintDust', (0.35, 0.32, 0.30, 0.5), 0.9), bevel=0)
    shards('living_broken_glass', (1.75, 3.45, 0.0))
    # stand lamp
    lathe('living_lamp', [(0, 0), (0.12, 0), (0.12, 0.02), (0.012, 0.03), (0.012, 1.35), (0.11, 1.38), (0.16, 1.55), (0.0, 1.55)],
          [M['pb']], 32, location=(2.15, 3.40, 0.0))
    # window sashes (sliding, two panes) + latch
    boxes('living_window', [((0.95, 5.49, 0.95), (1.70, 5.52, 2.05), 0), ((0.98, 5.50, 0.98), (1.67, 5.51, 2.02), 1)],
          [M['pw'], M['glass']], origin=(1.325, 5.505, 0.95), bevel=0.004)
    boxes('xprop_window_fixed_sash', [((1.65, 5.45, 0.95), (2.35, 5.48, 2.05), 0), ((1.68, 5.46, 0.98), (2.32, 5.47, 2.02), 1)],
          [M['pw'], M['glass']], bevel=0.004)
    boxes('living_window_latch', [((1.66, 5.485, 1.45), (1.69, 5.49, 1.55))], M['pw'], bevel=0.002)
    curtain('living_curtain_left', 0.78, 1.15)
    curtain('living_curtain_right', 2.15, 2.55)
    boxes('living_aircon_remote', [((1.70, 3.18, 0.33), (1.74, 3.32, 0.348))], M['pw'], bevel=0.008)
    clock('living_wall_clock', (2.8, 1.9, 1.95))
    switch_plate('living_wall_switch', (2.15, 1.9, 1.2), facing='+y')
    # paperwork on table
    papers('living_paper_stack', (1.38, 3.02, 0.33))
    boxes('living_envelope', [((1.50, 3.16, 0.33), (1.72, 3.27, 0.333))], mat('M_EnvelopeKraft', (0.75, 0.62, 0.42, 1), 0.85), bevel=0.0005)
    boxes('living_pen', [((1.30, 3.24, 0.333), (1.44, 3.25, 0.342))], M['pb'], bevel=0.003)
    # laptop on the floor-table corner, charger on floor
    boxes('living_laptop', [((1.08, 3.00, 0.33), (1.36, 3.20, 0.345), 0), ((1.08, 3.19, 0.345), (1.36, 3.20, 0.54), 0),
                            ((1.10, 3.188, 0.36), (1.34, 3.19, 0.53), 1)], [M['alu'], M['screen']], bevel=0.003)
    tube('living_laptop_charger', [(1.08, 3.10, 0.335), (1.0, 3.12, 0.2), (0.95, 3.2, 0.01), (0.7, 3.5, 0.01), (0.3, 3.6, 0.01)], 0.003, M['pb'])
    boxes('living_power_strip', [((0.08, 3.62, 0.0), (0.38, 3.68, 0.04), 0), ((0.12, 3.635, 0.04), (0.34, 3.665, 0.042), 1)],
          [M['pw'], M['red']], bevel=0.008)
    tube('living_power_cable', [(0.38, 3.65, 0.01), (0.9, 3.9, 0.008), (1.3, 4.6, 0.008), (2.0, 4.9, 0.008)], 0.004, M['pw'])
    phone('living_phone', (1.62, 3.62, 0.0))
    boxes('living_notepad', [((1.60, 2.74, 0.33), (1.72, 2.90, 0.338))], mat('M_NotepadYellow', (0.95, 0.88, 0.55, 1), 0.85), bevel=0.001)
    boxes('living_photo_frame', [((0.25, 4.98, 0.8), (0.40, 5.0, 0.98), 0), ((0.26, 4.979, 0.81), (0.39, 4.98, 0.97), 1)],
          [M['oak'], mat('M_PhotoPrint', (0.55, 0.5, 0.45, 1), 0.3)], bevel=0.003)
    # bookshelf (west wall, north of fridge)
    boxes('living_bookshelf', [((0.0, 4.32, 0.0), (0.30, 4.34, 1.2)), ((0.0, 4.88, 0.0), (0.30, 4.90, 1.2)),
                               ((0.0, 4.32, 0.0), (0.02, 4.90, 1.2)), ((0.0, 4.32, 0.0), (0.30, 4.90, 0.03)),
                               ((0.0, 4.32, 0.40), (0.30, 4.90, 0.42)), ((0.0, 4.32, 0.80), (0.30, 4.90, 0.82)),
                               ((0.0, 4.32, 1.18), (0.30, 4.90, 1.2))], M['pw'], bevel=0.002)
    book('living_book1', (0.05, 4.40, 0.42), (0.22, 0.035, 0.28), mat('M_BookCoverA', (0.18, 0.25, 0.38, 1), 0.6))
    book('living_book2', (0.05, 4.44, 0.42), (0.20, 0.03, 0.25), mat('M_BookCoverB', (0.55, 0.20, 0.15, 1), 0.6))
    boxes('living_box_storage', [((0.03, 4.45, 0.03), (0.28, 4.85, 0.30), 0)], [mat('M_StorageBox', (0.7, 0.7, 0.68, 0.9), 0.3)], bevel=0.01)
    plastic_bag('living_trash_bag', (0.85, 1.98, 0.0), (0.42, 0.34, 0.40), mat('M_TrashBagVolume', (0.55, 0.62, 0.70, 1), 0.35), knot=True, seed=7)
    # bedroom zone
    bed()
    boxes('sleep_bedside_table', [((2.0, 4.9, 0.0), (2.42, 5.3, 0.04)), ((2.0, 4.9, 0.46), (2.42, 5.3, 0.5)),
                                  ((2.0, 4.9, 0.0), (2.02, 5.3, 0.5)), ((2.40, 4.9, 0.0), (2.42, 5.3, 0.5)),
                                  ((2.0, 5.28, 0.0), (2.42, 5.3, 0.5))], M['oak'], bevel=0.003)
    drawer_y('sleep_bedside_drawer', (2.02, 4.9, 0.30), (2.40, 5.28, 0.46), M['oak'], M['oak'])
    tube('sleep_bedside_phone', [(2.10, 5.05, 0.345), (2.2, 5.1, 0.343), (2.3, 5.02, 0.343)], 0.003, M['pw'])
    wardrobe()
    chest()
    boxes('sleep_mirror', [((1.875, 0.2, 0.3), (1.9, 0.65, 1.85), 0), ((1.873, 0.22, 0.32), (1.875, 0.63, 1.83), 1)],
          [M['pw'], M['mirror']], bevel=0.004)
    lathe('sleep_laundry', [(0, 0), (0.18, 0), (0.2, 0.45), (0.19, 0.45), (0.17, 0.02), (0, 0.02)], [M['pg']], 28, location=(2.75, 2.12, 0.0))
    boxes('sleep_suitcase', [((2.25, 2.0, 0.0), (2.9, 2.25, 0.45), 0), ((2.5, 2.25, 0.32), (2.65, 2.27, 0.35), 1)],
          [mat('M_SuitcaseNavy', (0.10, 0.13, 0.22, 1), 0.4), M['pb']], origin=(2.575, 2.25, 0.0), bevel=0.02, seg=3)

def plastic_bag(name, at, size, material, knot=True, seed=3):
    """Filled plastic bag: subdivided block, sagging sides, crumpled jitter, gathered top + tied ears."""
    rnd = random.Random(seed)
    x, y, z = at
    sx, sy, sz = size
    bm = bmesh.new()
    _box_bm(bm, (x - sx / 2, y - sy / 2, z), (x + sx / 2, y + sy / 2, z + sz))
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=7, use_grid_fill=True)
    for v in bm.verts:
        u = (v.co.z - z) / sz
        dx, dy = (v.co.x - x) / (sx / 2), (v.co.y - y) / (sy / 2)
        bulge = 1.0 + 0.10 * math.sin(math.pi * min(1, u * 1.2))
        pinch = 1.0 - 0.75 * max(0.0, u - 0.7) / 0.3
        v.co.x = x + dx * sx / 2 * bulge * pinch
        v.co.y = y + dy * sy / 2 * bulge * pinch
        if u < 0.05:
            v.co.z = z + 0.002
        j = 0.008 if u > 0.15 else 0.003
        v.co += Vector((rnd.uniform(-j, j), rnd.uniform(-j, j), rnd.uniform(-j, j) * 0.6))
    parts = [mesh_obj('tmp_bagbody', bm, material, origin=at, smooth=True)]
    if knot:
        for s in (-1, 1):
            parts.append(tube('tmp_ear%d' % s, [(x + s * 0.02, y, z + sz - 0.01), (x + s * 0.07, y + 0.01, z + sz + 0.05),
                                                  (x + s * 0.04, y - 0.01, z + sz + 0.09), (x, y, z + sz + 0.02)], 0.012, material))
    o = join(name, parts, origin=at)
    shade_smooth_auto(o, 60)
    return o

def chair(name, at):
    x, y, z = at
    parts = [((-0.21, -0.21, 0.42), (0.21, 0.21, 0.45)), ((-0.2, -0.2, 0), (-0.17, -0.17, 0.42)), ((0.17, -0.2, 0), (0.2, -0.17, 0.42)),
             ((-0.2, 0.17, 0), (-0.17, 0.2, 0.42)), ((0.17, 0.17, 0), (0.2, 0.2, 0.42)), ((-0.2, 0.17, 0.45), (-0.17, 0.2, 0.85)),
             ((0.17, 0.17, 0.45), (0.2, 0.2, 0.85)), ((-0.2, 0.17, 0.62), (0.2, 0.2, 0.82))]
    c = boxes(name, [((a[0] + x, a[1] + y, a[2] + z), (b[0] + x, b[1] + y, b[2] + z)) for a, b in parts], M['oak'], origin=at, bevel=0.004)
    c.rotation_euler = (math.radians(90), 0, math.radians(25))
    c.location.z = 0.21
    return c

def blood_decal(name, at, r):
    x, y, z = at
    bm = bmesh.new()
    ctr = bm.verts.new((x, y, z))
    ring = []
    for i in range(28):
        a = 2 * math.pi * i / 28
        rr = r * (0.6 + 0.4 * random.random()) * (1.0 + 0.5 * math.sin(3 * a))
        ring.append(bm.verts.new((x + rr * math.cos(a) * 1.3, y + rr * math.sin(a), z)))
    for i in range(28):
        bm.faces.new((ctr, ring[i], ring[(i + 1) % 28]))
    return mesh_obj(name, bm, M['blood'], origin=at)

def shards(name, at):
    x, y, z = at
    bm = bmesh.new()
    for i in range(9):
        cx, cy = x + random.uniform(-0.15, 0.15), y + random.uniform(-0.12, 0.12)
        s = random.uniform(0.012, 0.035)
        vs = [bm.verts.new((cx + s * math.cos(a + random.random()), cy + s * math.sin(a + random.random()), z + 0.002)) for a in (0, 2.1, 4.2)]
        bm.faces.new(vs)
    return mesh_obj(name, bm, M['glass'], origin=at)

def curtain(name, x0, x1):
    bm = bmesh.new()
    n = 18
    top, bot = [], []
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = 5.36 + 0.03 * math.sin(t * math.pi * 7)
        top.append(bm.verts.new((x, y, 2.18)))
        bot.append(bm.verts.new((x, y + 0.01 * math.sin(t * 11), 0.85)))
    for i in range(n):
        bm.faces.new((bot[i], bot[i + 1], top[i + 1], top[i]))
    o = mesh_obj(name, bm, mat('M_CurtainFabric', (0.72, 0.70, 0.64, 1), 0.95), origin=((x0 + x1) / 2, 5.36, 2.18), smooth=True)
    sm = o.modifiers.new('s', 'SOLIDIFY'); sm.thickness = 0.004
    bake(o)
    return o

def clock(name, at):
    x, y, z = at
    o = lathe(name, [(0, 0), (0.15, 0), (0.15, 0.035), (0.14, 0.04), (0, 0.04)], [M['pw']], 40, location=(0, 0, 0))
    o.location = (x, y, z)
    o.rotation_euler = (math.radians(-90), 0, 0)
    return o

def papers(name, at):
    x, y, z = at
    parts = []
    for i in range(6):
        dx, dy = random.uniform(-0.01, 0.01), random.uniform(-0.01, 0.01)
        parts.append(((x - 0.105 + dx, y - 0.148 + dy, z + i * 0.0012), (x + 0.105 + dx, y + 0.148 + dy, z + i * 0.0012 + 0.0008)))
    return boxes(name, parts, M['paper'], origin=at, bevel=0.0)

def phone(name, at):
    x, y, z = at
    return boxes(name, [((x - 0.037, y - 0.077, z), (x + 0.037, y + 0.077, z + 0.008), 0),
                        ((x - 0.034, y - 0.073, z + 0.008), (x + 0.034, y + 0.073, z + 0.0085), 1)],
                 [M['pb'], M['screen']], origin=at, bevel=0.006, seg=3)

def book(name, at, size, cover):
    x, y, z = at
    w, t, h = size
    return boxes(name, [((x, y, z), (x + w, y + t, z + h), 0), ((x + 0.004, y + 0.003, z + 0.004), (x + w - 0.002, y + t - 0.003, z + h - 0.004), 1)],
                 [cover, M['paper']], origin=(x + w / 2, y + t / 2, z), bevel=0.002)

def bed():
    x0, x1, y0, y1 = 2.45, 3.55, 3.30, 5.30
    boxes('sleep_bed', [((x0, y0, 0.08), (x1, y1, 0.28)), ((x0 + 0.03, y0 + 0.03, 0.0), (x0 + 0.08, y0 + 0.08, 0.08)),
                        ((x1 - 0.08, y0 + 0.03, 0.0), (x1 - 0.03, y0 + 0.08, 0.08)), ((x0 + 0.03, y1 - 0.08, 0.0), (x0 + 0.08, y1 - 0.03, 0.08)),
                        ((x1 - 0.08, y1 - 0.08, 0.0), (x1 - 0.03, y1 - 0.03, 0.08)), ((x0, y1 - 0.04, 0.08), (x1, y1, 0.85))],
          M['oak'], bevel=0.006)
    # mattress: subdivided rounded block
    m = box('fix_mattress', (x0 + 0.03, y0 + 0.03, 0.28), (x1 - 0.03, y1 - 0.06, 0.50), M['mattress'], bevel=0.04, seg=4)
    shade_smooth_auto(m, 50)
    sheet = box('sleep_sheet', (x0 + 0.025, y0 + 0.025, 0.50), (x1 - 0.025, y1 - 0.055, 0.506), M['sheet'], bevel=0.003)
    # blanket: cloth-like rumpled duvet via displaced grid (cloth sim is run in build_cloth step)
    bm = bmesh.new()
    nx, ny = 26, 40
    grid = [[bm.verts.new((x0 - 0.05 + (x1 - x0 + 0.1) * i / nx, y0 - 0.05 + 1.55 * j / ny, 0.0)) for i in range(nx + 1)] for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    for j in range(ny + 1):
        for i in range(nx + 1):
            v = grid[j][i]
            u, w = i / nx, j / ny
            edge = min(u, 1 - u)
            z = 0.53 + 0.02 * math.sin(w * 13 + u * 4) + 0.012 * math.sin(u * 23) * (1 - w)
            if edge < 0.08:
                z -= (0.08 - edge) / 0.08 * 0.22  # drape over the sides
                v.co.x += (-0.03 if u < 0.5 else 0.03) * (0.08 - edge) / 0.08
            if w > 0.82:
                z += 0.07 * math.sin((w - 0.82) / 0.18 * math.pi) # folded-back top edge
            v.co.z = z
    o = mesh_obj('sleep_blanket', bm, M['linen'], origin=((x0 + x1) / 2, y0 + 0.7, 0.5), smooth=True)
    sm = o.modifiers.new('s', 'SOLIDIFY'); sm.thickness = 0.03
    ss = o.modifiers.new('sub', 'SUBSURF'); ss.levels = 1
    bake(o)
    for i, xx in enumerate((x0 + 0.30, x1 - 0.30)):
        pillow(f'sleep_pillow{i + 1}', (xx, y1 - 0.26, 0.56))

def pillow(name, at):
    x, y, z = at
    bm = bmesh.new()
    _box_bm(bm, (x - 0.25, y - 0.17, z - 0.06), (x + 0.25, y + 0.17, z + 0.06))
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=6, use_grid_fill=True)
    for v in bm.verts:
        dx, dy = (v.co.x - x) / 0.25, (v.co.y - y) / 0.17
        puff = max(0.0, 1 - 0.55 * (dx * dx + dy * dy))
        v.co.z = z + (v.co.z - z) * (0.25 + 0.95 * puff)
    o = mesh_obj(name, bm, M['cotton'], origin=at, smooth=True)
    ss = o.modifiers.new('sub', 'SUBSURF'); ss.levels = 1
    bake(o)
    return o

def wardrobe():
    x0, x1, y0, y1 = 3.0, 3.6, 1.95, 3.15
    boxes('fix_wardrobe_body', [((x0 + 0.02, y0, 0.0), (x1, y0 + 0.02, 2.0)), ((x0 + 0.02, y1 - 0.02, 0.0), (x1, y1, 2.0)),
                                ((x0 + 0.02, y0, 1.98), (x1, y1, 2.0)), ((x0 + 0.02, y0, 0.0), (x1, y1, 0.08)),
                                ((x1 - 0.02, y0, 0.0), (x1, y1, 2.0)), ((x0 + 0.02, 2.54, 0.08), (x1, 2.56, 1.98)),
                                ((x0 + 0.02, 2.56, 1.2), (x1 - 0.02, y1 - 0.02, 1.22)), ((x0 + 0.02, 2.56, 0.6), (x1 - 0.02, y1 - 0.02, 0.62))],
          M['cabwood'], bevel=0.003)
    tube('xprop_wardrobe_rod', [(3.30, 1.97, 1.78), (3.30, 2.52, 1.78)], 0.012, M['chrome'])
    # doors face -X (toward room), hinge at outer y
    for name, ya, yb, hinge in (('sleep_wardrobe_left', 1.952, 2.548, 'ymin'), ('sleep_wardrobe_right', 2.552, 3.148, 'ymax')):
        hy = (yb - 0.06, yb - 0.045) if hinge == 'ymin' else (ya + 0.045, ya + 0.06)
        boxes(name, [((x0, ya, 0.082), (x0 + 0.02, yb, 1.978), 0), ((x0 - 0.02, hy[0], 0.9), (x0, hy[1], 1.15), 1)],
              [M['cabwood'], M['alu']], origin=(x0 + 0.01, ya if hinge == 'ymin' else yb, 0.082), bevel=0.003)
    tube('sleep_hanger', [(3.30, 2.10, 1.78), (3.30, 2.10, 1.72), (3.30, 1.95 + 0.0, 1.64), (3.30, 2.25, 1.64), (3.30, 2.10, 1.72)], 0.004, M['pb'])
    coat = box('sleep_coat', (3.12, 2.15, 0.95), (3.48, 2.40, 1.70), mat('M_CoatWool', (0.16, 0.16, 0.18, 1), 0.9), bevel=0.05, seg=3)
    shade_smooth_auto(coat)
    boxes('sleep_shirt', [((3.15, 2.70, 1.22), (3.45, 2.98, 1.27))], mat('M_ShirtCotton', (0.72, 0.78, 0.85, 1), 0.9), bevel=0.012, seg=2)

def chest():
    x0, x1, y0, y1 = 0.2, 0.85, 4.95, 5.4
    boxes('fix_drawer_chest', [((x0, y0 + 0.02, 0.0), (x0 + 0.02, y1, 0.78)), ((x1 - 0.02, y0 + 0.02, 0.0), (x1, y1, 0.78)),
                               ((x0, y0 + 0.02, 0.76), (x1, y1, 0.78)), ((x0, y0 + 0.02, 0.0), (x1, y1, 0.05)),
                               ((x0, y1 - 0.02, 0.0), (x1, y1, 0.78))], M['pw'], bevel=0.003)
    # drawers face -Y (front at y0)
    for nm, za, zb in (('sleep_drawer_top', 0.52, 0.755), ('sleep_drawer_mid', 0.285, 0.515), ('sleep_drawer_bottom', 0.05, 0.28)):
        drawer_y(nm, (x0 + 0.02, y0, za), (x1 - 0.02, y1 - 0.02, zb), M['pw'], M['pw'])

# ======================= BATHROOM =======================
def bathroom():
    # door (white ABS), hinge at Y 1.7 side, opens into bathroom (+X)
    boxes('bath_bath_door', [((1.93, 0.955, 0.012), (1.97, 1.695, 1.995), 0),
                             ((1.90, 1.0, 0.98), (1.93, 1.03, 1.0), 1), ((1.90, 1.0, 0.98), (1.912, 1.12, 0.995), 1),
                             ((1.97, 1.0, 0.98), (2.0, 1.03, 1.0), 1), ((1.988, 1.0, 0.98), (2.0, 1.12, 0.995), 1)],
          [M['doorwhite'], M['chrome']], origin=(1.95, 1.695, 0.012), bevel=0.004)
    switch_plate('bath_light_switch', (1.9, 1.78, 1.2), facing='-x')
    switch_plate('bath_vent_fan', (1.9, 1.86, 1.2), facing='-x')
    # toilet (tank on east wall, faces -X)
    tx, ty = 3.18, 0.45
    bowl = lathe('fix_toilet_bowl', [(0, 0.0), (0.12, 0.0), (0.15, 0.06), (0.17, 0.25), (0.19, 0.38), (0.175, 0.40), (0.14, 0.39),
                                     (0.10, 0.30), (0.05, 0.22), (0, 0.22)], [M['porc']], 48, location=(tx, ty, -0.045))
    bowl.scale = (1.22, 1.0, 1.0)
    boxes('fix_toilet_tank', [((3.38, ty - 0.21, 0.34), (3.58, ty + 0.21, 0.78))], [M['porc']], bevel=0.025, seg=3)
    seat = lathe('bath_toilet_seat', [(0.13, 0.0), (0.19, 0.0), (0.195, 0.012), (0.185, 0.022), (0.135, 0.022), (0.125, 0.01)],
                 [M['pw']], 48, location=(tx, ty, 0.355))
    seat.scale = (1.2, 1.0, 1.0)
    lid = lathe('bath_toilet_lid', [(0.0, 0.03), (0.195, 0.03), (0.2, 0.022), (0.19, 0.045), (0.0, 0.05)], [M['pw']], 48,
                location=(tx, ty, 0.355))
    lid.scale = (1.2, 1.0, 1.0)
    for o in (seat, lid):
        bake(o) if o.modifiers else None
    # pivots at the back hinge
    for o in (seat, lid):
        o.data.transform(__import__('mathutils').Matrix.Diagonal((1.2, 1, 1, 1)))
        o.scale = (1, 1, 1)
        set_origin(o, (3.38, ty, 0.375))
    bowl.data.transform(__import__('mathutils').Matrix.Diagonal((1.22, 1, 1, 1))); bowl.scale = (1, 1, 1)
    boxes('bath_flush_handle', [((3.37, ty + 0.12, 0.70), (3.38, ty + 0.17, 0.72))], M['chrome'], bevel=0.003)
    tube('bath_toilet_brush', [(3.5, 0.08, -0.04), (3.5, 0.08, 0.38)], 0.015, M['pw'])
    tube('bath_toilet_paper', [(3.57, 0.82, 0.70), (3.47, 0.82, 0.70)], 0.055, M['paper'])
    # wall basin on north partition (y 1.8), faces -Y
    bm = bmesh.new()
    _box_bm(bm, (2.58, 1.40, 0.70), (3.12, 1.80, 0.84))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.04, segments=4, affect='EDGES')
    sink = mesh_obj('bath_sink', bm, M['porc'], origin=(2.85, 1.6, 0.70), smooth=True)
    cut = box('tmp_bcut', (2.63, 1.45, 0.73), (3.07, 1.72, 0.9), None, bevel=0.06, seg=4)
    boolean_cut(sink, cut); shade_smooth_auto(sink, 45)
    base = lathe('tmp_bfb', [(0, 0), (0.022, 0), (0.02, 0.09), (0, 0.09)], M['chrome'], 24, location=(2.85, 1.75, 0.84))
    spout = tube('tmp_bfs', [(2.85, 1.75, 0.91), (2.85, 1.66, 0.93), (2.85, 1.62, 0.90)], 0.01, M['chrome'])
    lev = boxes('tmp_bfl', [((2.845, 1.74, 0.93), (2.855, 1.80, 0.94))], M['chrome'], bevel=0.003)
    join('bath_sink_faucet', [base, spout, lev], origin=(2.85, 1.75, 0.84))
    boxes('bath_lower_cabinet', [((2.66, 1.46, 0.10), (3.04, 1.80, 0.66), 0), ((2.82, 1.455, 0.55), (2.88, 1.46, 0.57), 1)],
          [M['pw'], M['chrome']], origin=(2.66, 1.46, 0.10), bevel=0.006)
    # mirror cabinet (door is mirror, hinge at x min)
    boxes('fix_mirror_cabinet_body', [((2.55, 1.66, 1.15), (3.15, 1.80, 1.80)), ((2.57, 1.68, 1.47), (3.13, 1.80, 1.48))], M['pw'], bevel=0.003)
    boxes('bath_mirror_cabinet', [((2.55, 1.64, 1.15), (3.15, 1.66, 1.80), 0), ((2.56, 1.638, 1.16), (3.14, 1.64, 1.79), 1)],
          [M['pw'], M['mirror']], origin=(2.55, 1.65, 1.15), bevel=0.004)
    lathe('bath_toothpaste', [(0, 0), (0.018, 0), (0.018, 0.15), (0.01, 0.17), (0, 0.17)], M['pw'], 16, location=(2.62, 1.73, 1.48))
    tube('bath_toothbrush', [(2.70, 1.73, 1.49), (2.70, 1.73, 1.66)], 0.006, mat('M_PlasticBlue', (0.15, 0.35, 0.65, 1), 0.4))
    lathe('bath_cup', [(0, 0), (0.035, 0), (0.04, 0.10), (0.037, 0.10), (0.032, 0.004), (0, 0.004)], mat('M_PlasticBlue', (0.15, 0.35, 0.65, 1), 0.4), 24,
          location=(3.05, 1.45, 0.84 - 0.0))
    boxes('bath_soap', [((2.66, 1.47, 0.84), (2.74, 1.52, 0.865))], mat('M_Soap', (0.9, 0.85, 0.72, 1), 0.5), bevel=0.01, seg=2)
    # shower: riser on south wall, head, hose, tap
    tube('xprop_shower_riser', [(2.4, 0.03, 1.0), (2.4, 0.03, 1.95)], 0.011, M['chrome'])
    hd = lathe('bath_shower_head', [(0, 0), (0.05, 0), (0.055, 0.02), (0.018, 0.04), (0.015, 0.2), (0, 0.2)], M['chrome'], 28, location=(2.4, 0.07, 1.7))
    hd.rotation_euler = (math.radians(200), 0, 0)
    tube('xprop_shower_hose', [(2.4, 0.06, 0.95), (2.45, 0.2, 0.6), (2.42, 0.12, 1.2), (2.4, 0.08, 1.55)], 0.008, M['chrome'])
    boxes('bath_shower_tap', [((2.32, 0.0, 0.92), (2.48, 0.06, 0.98)), ((2.39, 0.06, 0.94), (2.41, 0.12, 0.96))], M['chrome'], bevel=0.006)
    lathe('bath_shampoo', [(0, 0), (0.035, 0), (0.035, 0.18), (0.012, 0.21), (0.012, 0.24), (0, 0.24)], M['pw'], 20, location=(2.15, 0.12, -0.045))
    lathe('bath_body_wash', [(0, 0), (0.035, 0), (0.035, 0.2), (0.012, 0.22), (0.012, 0.25), (0, 0.25)], M['green'], 20, location=(2.24, 0.10, -0.045))
    lathe('bath_drain', [(0, 0.0), (0.06, 0.0), (0.06, 0.003), (0.0, 0.003)], M['steel'], 32, location=(2.4, 0.45, -0.045))
    # towels on bar (north partition inner side near door)
    tube('xprop_towel_bar', [(2.05, 1.77, 1.35), (2.45, 1.77, 1.35)], 0.008, M['chrome'])
    box('bath_towel1', (2.07, 1.745, 0.95), (2.25, 1.79, 1.37), mat('M_TowelGray', (0.55, 0.56, 0.58, 1), 1.0), bevel=0.012, seg=2)
    box('bath_towel2', (2.27, 1.745, 1.0), (2.43, 1.79, 1.37), mat('M_TowelBeige', (0.78, 0.72, 0.62, 1), 1.0), bevel=0.012, seg=2)
    lathe('bath_laundry_bin', [(0, 0), (0.14, 0), (0.15, 0.4), (0.14, 0.4), (0.13, 0.02), (0, 0.02)], [M['pw']], 24, location=(2.2, 1.45, -0.045))
    box('bath_floor_mat', (2.05, 1.0, -0.045), (2.5, 1.45, -0.035), mat('M_BathMat', (0.45, 0.55, 0.6, 1), 1.0), bevel=0.004)
    boxes('bath_window', [((3.62, 1.21, 1.61), (3.66, 1.59, 1.99), 0), ((3.63, 1.23, 1.63), (3.64, 1.57, 1.97), 1)],
          [M['pw'], mat('M_FrostedGlass', (0.85, 0.88, 0.9, 0.7), 0.6)], origin=(3.64, 1.4, 1.61), bevel=0.004)
    boxes('bath_ceiling', [((2.75, 0.75, 2.19), (3.20, 1.20, 2.2))], M['pw'], origin=(2.75, 0.975, 2.2), bevel=0.003)
    lathe('xprop_bath_light', [(0, -0.0), (0.12, 0.0), (0.12, -0.03), (0.0, -0.05)], M['led'], 32, location=(2.4, 1.2, 2.2))
    boxes('xprop_bath_vent_grille', [((3.25, 1.35, 2.19), (3.45, 1.55, 2.2))], M['pw'], bevel=0.003)

# ======================= HALLWAY =======================
def hallway():
    C = 'Hall3F'
    box('arch_hall_floor', (-1.6, -1.8, -0.30), (6.2, -0.15, ST), M['stair'], bevel=0, collection=C)
    box('arch_hall_ceiling', (-1.6, -1.8, H - 0.05), (6.2, -0.15, H), M['ceil'], bevel=0, collection=C)
    box('arch_hall_wall_s', (-1.6, -1.95, ST), (6.2, -1.8, H), M['hconc'], bevel=0, collection=C)
    box('arch_hall_wall_e', (6.2, -1.95, ST), (6.35, -0.15, H), M['hconc'], bevel=0, collection=C)
    box('arch_hall_wall_302_ext', (2.0, -0.15, ST), (6.2, -0.14, H), M['hplaster'], bevel=0, collection=C)
    box('arch_hall_wall_west_ext', (-1.6, -0.15, ST), (0.07, -0.14, H), M['hplaster'], bevel=0, collection=C)
    # stairs down (west end)
    for i in range(6):
        box(f'arch_hall_stair_{i}', (-1.6, -1.75 + i * 0.27, ST - 0.17 * (i + 1) - 0.02), (-0.4, -1.48 + i * 0.27, ST - 0.17 * (i + 1)),
            M['stair'], bevel=0.004, collection=C)
    tube('hall_stairs', [(-0.42, -1.75, ST + 0.9), (-0.42, -0.2, ST + 0.9 - 1.0)], 0.02, M['alu'], collection=C)
    # neighbor door 301
    boxes('hall_neighbor_door', [((4.6, -0.20, ST + 0.01), (5.5, -0.15, ST + 2.03), 0), ((4.7, -0.21, ST + 0.95), (4.78, -0.20, ST + 1.30), 1)],
          [M['doorsteel'], M['pb']], origin=(5.5, -0.175, ST), bevel=0.006, collection=C)
    lathe('hall_sensor', [(0, 0), (0.07, 0), (0.06, -0.04), (0, -0.05)], M['pw'], 28, location=(1.6, -0.9, H - 0.05), collection=C)
    lathe('hall_cctv', [(0, 0), (0.06, 0), (0.06, -0.02), (0.05, -0.07), (0, -0.08)], [M['pb']], 24, location=(5.9, -1.6, H - 0.05), collection=C)
    boxes('hall_mailbox', [((-1.58, -1.2, ST + 0.9), (-1.48, -0.6, ST + 1.3))], M['alu'], bevel=0.004, collection=C)
    boxes('hall_intercom', [((-1.58, -0.5, ST + 1.3), (-1.555, -0.36, ST + 1.52), 0), ((-1.556, -0.48, ST + 1.42), (-1.553, -0.38, ST + 1.5), 1)],
          [M['pw'], M['screen']], bevel=0.004, collection=C)
    box('xprop_hall_302_plate', (0.3, -0.161, ST + 2.12), (0.5, -0.15, ST + 2.2), M['brass'], bevel=0.002, collection=C)

architecture(); entrance(); kitchen(); living(); bathroom(); hallway()

# ---- export ----
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
fbx = args[0] if args else os.path.join(os.path.dirname(__file__), '..', 'out', 'Room302.fbx')
blend = args[1] if len(args) > 1 else None
for o in list(bpy.data.objects):
    if o.name.startswith('tmp_'):
        bpy.data.objects.remove(o, do_unlink=True)
names = sorted(o.name for o in bpy.data.objects)
print('OBJECTS', len(names))
open(os.path.splitext(fbx)[0] + '_objects.txt', 'w', encoding='utf-8').write('\n'.join(names))
export_fbx(fbx)
if blend:
    bpy.ops.wm.save_as_mainfile(filepath=blend)
print('EXPORTED', fbx)
