"""CASE 001 — 진술녹화실 2 (interrogation / statement-recording room) as real geometry. Headless:
  blender -b --factory-startup -P blender/scripts/build_interrogation.py -- <out.fbx> <out.blend>

Staging (approved INTERROGATION_TARGET_VISUAL + V14 A concept): detective seated at the near table edge (camera ~1.18 m),
suspect seated opposite on a padded steel-frame chair, one conical pendant lamp low over the table (the key light that
keeps the suspect's eyes in natural shadow), blinds over a night window behind her, a caged wall bulb behind-left (hair rim),
recording camera on a tripod in the back-left corner, statement form + paper cup on her side, recorder + case file +
water glass on the detective side. No suspect body here — the character is a separate rigged asset.
Layout (Blender Z-up): room X -1.7..1.7, Y -1.7..2.0 (Y+ = behind the suspect), H 2.5. Table centred on the origin.
Naming: ir_<thing>. Materials M_IR*.
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(__file__))
import bpy, bmesh
from mathutils import Vector
from tzlib import *
from tzlib import _box_bm

random.seed(2)
reset()
C = 'Interrogation'
X0, X1, Y0, Y1, H = -1.7, 1.7, -1.7, 2.0, 2.5
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FONT = os.path.join(REPO, 'TableZero.Unity', 'Assets', 'TableZero', 'Art', 'Fonts', 'NotoSansKR-Variable.ttf')

M = {
 'floor': mat('M_IRFloor', (0.30, 0.30, 0.29, 1), 0.5), 'wain': mat('M_IRWainscot', (0.16, 0.16, 0.17, 1), 0.45),
 'panel': mat('M_IRAcoustic', (0.42, 0.40, 0.37, 1), 0.9), 'seam': mat('M_IRSeam', (0.05, 0.05, 0.05, 1), 0.9),
 'ceil': mat('M_IRCeilTile', (0.55, 0.55, 0.53, 1), 0.95), 'grid': mat('M_IRCeilGrid', (0.62, 0.62, 0.60, 1), 0.5, 0.6),
 'alu': mat('M_IRAlu', (0.18, 0.18, 0.19, 1), 0.45, 0.8), 'glass': mat('M_IRGlass', (0.30, 0.34, 0.38, 0.12), 0.05),
 'blind': mat('M_IRBlind', (0.55, 0.54, 0.50, 1), 0.55), 'night': mat('M_IRNightCity', (1, 1, 1, 1), 0.2),
 'top': mat('M_IRTableTop', (0.06, 0.05, 0.045, 1), 0.2), 'edge': mat('M_IRTableEdge', (0.03, 0.03, 0.03, 1), 0.4),
 'steel': mat('M_IRSteelBlack', (0.03, 0.03, 0.035, 1), 0.4, 0.7), 'chrome': mat('M_IRChrome', (0.8, 0.8, 0.82, 1), 0.1, 1.0),
 'fabric': mat('M_IRChairFabric', (0.05, 0.05, 0.055, 1), 0.9), 'shade': mat('M_IRLampShade', (0.06, 0.06, 0.06, 1), 0.4, 0.9),
 'shadein': mat('M_IRLampInner', (0.9, 0.88, 0.82, 1), 0.5), 'bulb': mat('M_IRBulb', (1.0, 0.82, 0.55, 1), 0.3),
 'cord': mat('M_IRCord', (0.02, 0.02, 0.02, 1), 0.5), 'gun': mat('M_IRGunmetal', (0.10, 0.10, 0.11, 1), 0.45, 0.8),
 'screen': mat('M_IRLCD', (0.05, 0.07, 0.06, 1), 0.8), 'led': mat('M_IRLedRed', (1.0, 0.05, 0.03, 1), 0.3),
 'manila': mat('M_IRManila', (0.62, 0.50, 0.33, 1), 0.25), 'paper': mat('M_IRPaper', (0.86, 0.85, 0.80, 1), 0.2),
 'rule': mat('M_IRRule', (0.55, 0.55, 0.58, 1), 0.3), 'ink': mat('M_IRInk', (0.05, 0.05, 0.06, 1), 0.3), 'redink': mat('M_IRStampRed', (0.55, 0.06, 0.05, 1), 0.3),
 'cup': mat('M_IRPaperCup', (0.88, 0.87, 0.83, 1), 0.25), 'water': mat('M_IRWater', (0.55, 0.62, 0.66, 0.35), 0.95),
 'cabinet': mat('M_IRCabinetGrey', (0.36, 0.37, 0.37, 1), 0.35, 0.4), 'rubber': mat('M_IRRubber', (0.02, 0.02, 0.02, 1), 0.2),
 'door': mat('M_IRDoor', (0.30, 0.27, 0.24, 1), 0.35), 'plate': mat('M_IRPlate', (0.75, 0.73, 0.68, 1), 0.3, 0.7),
 'cam': mat('M_IRCameraBody', (0.04, 0.04, 0.045, 1), 0.35, 0.2), 'lens': mat('M_IRLensGlass', (0.02, 0.025, 0.03, 1), 0.02, 0.0),
 'base': mat('M_IRSkirting', (0.08, 0.08, 0.08, 1), 0.4),
}

# ---------------------------------------------------------------- architecture
box('arch_floor', (X0, Y0, -0.05), (X1, Y1, 0.0), M['floor'], bevel=0, collection=C)
box('arch_ceiling_slab', (X0, Y0, H), (X1, Y1, H + 0.05), M['ceil'], bevel=0, collection=C)
T = 0.12
WIN = (-0.95, 0.95, 0.95, 2.05)                     # back-wall window x0,x1,z0,z1
# back wall (Y1) with a window hole: 4 boxes
box('arch_wall_back_l', (X0, Y1, 0), (WIN[0], Y1 + T, H), M['panel'], bevel=0, collection=C)
box('arch_wall_back_r', (WIN[1], Y1, 0), (X1, Y1 + T, H), M['panel'], bevel=0, collection=C)
box('arch_wall_back_b', (WIN[0], Y1, 0), (WIN[1], Y1 + T, WIN[2]), M['panel'], bevel=0, collection=C)
box('arch_wall_back_t', (WIN[0], Y1, WIN[3]), (WIN[1], Y1 + T, H), M['panel'], bevel=0, collection=C)
box('arch_wall_front', (X0, Y0 - T, 0), (X1, Y0, H), M['panel'], bevel=0, collection=C)
DOOR = (-1.25, -0.30)                                # left-wall door span in Y
box('arch_wall_left_a', (X0 - T, Y0, 0), (X0, DOOR[0], H), M['panel'], bevel=0, collection=C)
box('arch_wall_left_b', (X0 - T, DOOR[1], 0), (X0, Y1, H), M['panel'], bevel=0, collection=C)
box('arch_wall_left_c', (X0 - T, DOOR[0], 2.1), (X0, DOOR[1], H), M['panel'], bevel=0, collection=C)
box('arch_wall_right', (X1, Y0, 0), (X1 + T, Y1, H), M['panel'], bevel=0, collection=C)

# wainscot (lower dark laminate, 0.9 m) + skirting, on all walls; acoustic panel seams above every 0.6 m
def wain_x(y, sgn, x0, x1):
    yy = (y - 0.012, y) if sgn > 0 else (y, y + 0.012)
    box(f'arch_wain_{y:.1f}_{x0:.1f}', (x0, yy[0], 0), (x1, yy[1], 0.9), M['wain'], bevel=0.002, seg=1, collection=C)
    box(f'arch_wain_cap_{y:.1f}_{x0:.1f}', (x0, yy[0] - 0.008 * sgn if sgn > 0 else yy[0], 0.895),
        (x1, yy[1] if sgn > 0 else yy[1] + 0.008, 0.915), M['alu'], bevel=0.002, seg=1, collection=C)
def wain_y(x, sgn, y0, y1):
    xx = (x - 0.012, x) if sgn > 0 else (x, x + 0.012)
    box(f'arch_wainY_{x:.1f}_{y0:.1f}', (xx[0], y0, 0), (xx[1], y1, 0.9), M['wain'], bevel=0.002, seg=1, collection=C)
    box(f'arch_wainY_cap_{x:.1f}_{y0:.1f}', (xx[0] - (0.008 if sgn > 0 else 0), y0, 0.895), (xx[1] + (0 if sgn > 0 else 0.008), y1, 0.915), M['alu'], bevel=0.002, seg=1, collection=C)
wain_x(Y1, 1, X0, X1); wain_x(Y0, -1, X0, X1)
wain_y(X1, 1, Y0, Y1); wain_y(X0, -1, Y0, DOOR[0]); wain_y(X0, -1, DOOR[1], Y1)
seams = []
for x in [X0 + 0.6 * i for i in range(1, 6)]:
    if not (WIN[0] - 0.05 < x < WIN[1] + 0.05):
        seams.append(((x - 0.003, Y1 - 0.003, 0.915), (x + 0.003, Y1, H)))
for y in [Y0 + 0.62 * i for i in range(1, 6)]:
    seams.append(((X1 - 0.003, y - 0.003, 0.915), (X1, y + 0.003, H)))
    if not (DOOR[0] - 0.1 < y < DOOR[1] + 0.1):
        seams.append(((X0, y - 0.003, 0.915), (X0 + 0.003, y + 0.003, H)))
boxes('arch_panel_seams', seams, M['seam'], collection=C, bevel=0)

# T-bar ceiling grid 600 mm
grid = []
z = H - 0.012
for x in [X0 + 0.6 * i for i in range(0, 7)]:
    grid.append(((x - 0.012, Y0, z), (x + 0.012, Y1, H)))
for y in [Y0 + 0.6 * i for i in range(0, 8)]:
    grid.append(((X0, y - 0.012, z), (X1, y + 0.012, H)))
boxes('arch_ceiling_grid', grid, M['grid'], collection=C, bevel=0)

# window: frame, mullion, glass, blinds, night city card behind
wf = []
wy0, wy1 = Y1, Y1 + T
wf += [((WIN[0], wy0 - 0.02, WIN[2] - 0.04), (WIN[1], wy1, WIN[2])), ((WIN[0], wy0 - 0.02, WIN[3]), (WIN[1], wy1, WIN[3] + 0.04)),
       ((WIN[0] - 0.04, wy0 - 0.02, WIN[2] - 0.04), (WIN[0], wy1, WIN[3] + 0.04)), ((WIN[1], wy0 - 0.02, WIN[2] - 0.04), (WIN[1] + 0.04, wy1, WIN[3] + 0.04)),
       ((-0.02, wy0 + 0.04, WIN[2]), (0.02, wy0 + 0.08, WIN[3]))]
boxes('arch_window_frame', wf, M['alu'], collection=C, bevel=0.003)
box('arch_window_glass', (WIN[0], wy0 + 0.058, WIN[2]), (WIN[1], wy0 + 0.064, WIN[3]), M['glass'], bevel=0, collection=C)
box('arch_window_sill', (WIN[0] - 0.06, wy0 - 0.10, WIN[2] - 0.05), (WIN[1] + 0.06, wy0 + 0.01, WIN[2] - 0.02), M['alu'], bevel=0.004, collection=C)
# blinds: 25 mm aluminium slats, 22 mm pitch, tilted ~40° (light leaks between them), lower third pulled up a little unevenly
slats = bmesh.new()
pitch, sw, tilt = 0.024, 0.025, math.radians(40)
zz = WIN[3] - 0.03
yb = wy0 - 0.045
n = 0
while zz > WIN[2] + 0.02:
    dz, dy = math.sin(tilt) * sw / 2, math.cos(tilt) * sw / 2
    sag = 0.0
    vs = [slats.verts.new(v) for v in ((WIN[0] + 0.03, yb - dy, zz - dz), (WIN[1] - 0.03, yb - dy, zz - dz),
                                        (WIN[1] - 0.03, yb + dy, zz + dz), (WIN[0] + 0.03, yb + dy, zz + dz))]
    slats.faces.new(vs)
    zz -= pitch; n += 1
bmesh.ops.solidify(slats, geom=list(slats.faces), thickness=0.0012)
slats.normal_update()
mesh_obj('arch_blinds', slats, M['blind'], C)
box('arch_blinds_headrail', (WIN[0] + 0.02, yb - 0.025, WIN[3] - 0.02), (WIN[1] - 0.02, yb + 0.025, WIN[3] + 0.02), M['blind'], bevel=0.004, collection=C)
box('arch_blinds_bottomrail', (WIN[0] + 0.03, yb - 0.015, WIN[2] + 0.005), (WIN[1] - 0.03, yb + 0.015, WIN[2] + 0.02), M['blind'], bevel=0.003, collection=C)
for i, x in enumerate((-0.55, 0.0, 0.55)):
    tube(f'arch_blinds_ladder_{i}', [(x, yb - 0.014, WIN[3] - 0.02), (x, yb - 0.014, WIN[2] + 0.01)], 0.0009, M['blind'], C)
tube('arch_blinds_cord', [(WIN[1] - 0.06, yb - 0.03, WIN[3] - 0.02), (WIN[1] - 0.06, yb - 0.03, 1.15)], 0.0016, M['blind'], C)
card_bm = bmesh.new()
vs = [card_bm.verts.new(v) for v in ((-2.4, Y1 + 1.6, -0.4), (2.4, Y1 + 1.6, -0.4), (2.4, Y1 + 1.6, 3.2), (-2.4, Y1 + 1.6, 3.2))]
card_bm.faces.new(vs)
o = mesh_obj('arch_night_city', card_bm, M['night'], C, uv=False)
o.data.uv_layers.new(name='UV'); uvl = o.data.uv_layers[0]
for li, (u, v) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
    uvl.data[li].uv = (u, v)

# door (left wall), frame, handle; skirting
box('fix_door_leaf', (X0 - 0.04, DOOR[0] + 0.03, 0.0), (X0 - 0.005, DOOR[1] - 0.03, 2.07), M['door'], bevel=0.003, collection=C)
boxes('fix_door_frame', [((X0 - 0.02, DOOR[0], 0), (X0 + 0.015, DOOR[0] + 0.03, 2.1)), ((X0 - 0.02, DOOR[1] - 0.03, 0), (X0 + 0.015, DOOR[1], 2.1)),
                         ((X0 - 0.02, DOOR[0], 2.07), (X0 + 0.015, DOOR[1], 2.1))], M['alu'], collection=C)
tube('fix_door_handle', [(X0 + 0.0, DOOR[1] - 0.10, 1.02), (X0 + 0.055, DOOR[1] - 0.10, 1.02), (X0 + 0.06, DOOR[1] - 0.22, 1.02)], 0.009, M['chrome'], C)
text_mesh('fix_sign_room', '진술녹화실 2', 0.05, (X0 + 0.004, DOOR[1] + 0.30, 1.62), (math.pi / 2, 0, -math.pi / 2), M['ink'], FONT, collection=C, bold=0.004)
box('fix_sign_plate', (X0, DOOR[1] + 0.12, 1.57), (X0 + 0.003, DOOR[1] + 0.48, 1.67), M['plate'], bevel=0.001, collection=C)

# ---------------------------------------------------------------- table (heavy laminate top, black steel frame)
TX, TY, TZ = 0.85, 0.43, 0.745
box('fix_table_top', (-TX, -TY, TZ - 0.032), (TX, TY, TZ), M['top'], bevel=0.006, seg=3, collection=C)
boxes('fix_table_edgeband', [((-TX - 0.002, -TY - 0.002, TZ - 0.030), (TX + 0.002, -TY + 0.004, TZ - 0.003)),
                             ((-TX - 0.002, TY - 0.004, TZ - 0.030), (TX + 0.002, TY + 0.002, TZ - 0.003))], M['edge'], collection=C, bevel=0.001)
legs = []
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = sx * (TX - 0.06), sy * (TY - 0.06)
        legs.append(((x - 0.022, y - 0.022, 0.0), (x + 0.022, y + 0.022, TZ - 0.032)))
legs += [((-TX + 0.05, -TY + 0.05, TZ - 0.09), (TX - 0.05, -TY + 0.075, TZ - 0.032)), ((-TX + 0.05, TY - 0.075, TZ - 0.09), (TX - 0.05, TY - 0.05, TZ - 0.032)),
         ((-TX + 0.04, -TY + 0.05, TZ - 0.09), (-TX + 0.08, TY - 0.05, TZ - 0.032)), ((TX - 0.08, -TY + 0.05, TZ - 0.09), (TX - 0.04, TY - 0.05, TZ - 0.032))]
boxes('fix_table_frame', legs, M['steel'], collection=C, bevel=0.003)
boxes('fix_table_feet', [((sx * (TX - 0.06) - 0.025, sy * (TY - 0.06) - 0.025, 0), (sx * (TX - 0.06) + 0.025, sy * (TY - 0.06) + 0.025, 0.012))
                         for sx in (-1, 1) for sy in (-1, 1)], M['rubber'], collection=C, bevel=0.003)

# ---------------------------------------------------------------- suspect chair (padded seat/back, black steel sled frame)
CY = 0.80          # chair centre (seat) — she sits facing -Y
def chair(prefix, cx, cy, face=-1, rot=0.0):
    s = face
    seat_z = 0.455
    box(f'{prefix}_seat', (cx - 0.235, cy - 0.215, seat_z - 0.06), (cx + 0.235, cy + 0.215, seat_z), M['fabric'], bevel=0.025, seg=4, collection=C)
    box(f'{prefix}_seat_shell', (cx - 0.225, cy - 0.205, seat_z - 0.085), (cx + 0.225, cy + 0.205, seat_z - 0.055), M['steel'], bevel=0.008, seg=2, collection=C)
    by = cy - s * 0.215
    box(f'{prefix}_back', (cx - 0.225, by - 0.025, seat_z + 0.10), (cx + 0.225, by + 0.025, seat_z + 0.52), M['fabric'], bevel=0.02, seg=4, collection=C)
    # sled frame tubes
    for sx in (-1, 1):
        x = cx + sx * 0.215
        tube(f'{prefix}_sled_{sx}', [(x, cy + s * 0.22, 0.012), (x, cy - s * 0.24, 0.012), (x, cy - s * 0.24, seat_z - 0.07),
                                      (x, cy - s * 0.22, seat_z - 0.07)], 0.011, M['steel'], C)
        tube(f'{prefix}_front_{sx}', [(x, cy + s * 0.22, 0.012), (x, cy + s * 0.20, seat_z - 0.07)], 0.011, M['steel'], C)
        tube(f'{prefix}_backpost_{sx}', [(x, cy - s * 0.20, seat_z - 0.07), (x, by - s * 0.03, seat_z + 0.15), (x * 0.98 + cx * 0.02, by - s * 0.03, seat_z + 0.42)], 0.010, M['steel'], C)
    tube(f'{prefix}_crossbar', [(cx - 0.215, cy - s * 0.10, seat_z - 0.075), (cx + 0.215, cy - s * 0.10, seat_z - 0.075)], 0.008, M['steel'], C)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f'{prefix}_glide_{sx}_{sy}', (cx + sx * 0.215 - 0.014, cy + sy * 0.23 - 0.02, 0), (cx + sx * 0.215 + 0.014, cy + sy * 0.23 + 0.02, 0.006), M['rubber'], bevel=0.002, collection=C)
chair('fix_chair_suspect', 0.0, CY, face=-1)

# ---------------------------------------------------------------- pendant lamp (key light) + caged wall bulb (rim)
LZ = 1.58
LY = 0.42                                            # slightly over her side: eyes fall under the shade's cut-off
tube('fix_pendant_cord', [(0.0, LY, H), (0.0, LY, LZ + 0.16)], 0.003, M['cord'], C)
lathe('fix_pendant_shade', [(0.012, 0.17), (0.035, 0.165), (0.05, 0.12), (0.12, 0.05), (0.19, 0.0), (0.192, -0.004)], M['shade'], 64, C, location=(0, LY, LZ))
lathe('fix_pendant_inner', [(0.188, -0.001), (0.118, 0.046), (0.048, 0.116), (0.034, 0.158)], M['shadein'], 64, C, location=(0, LY, LZ))
lathe('fix_pendant_bulb', [(0.0, 0.06), (0.022, 0.058), (0.032, 0.035), (0.03, 0.012), (0.0, 0.0)], M['bulb'], 32, C, location=(0, LY, LZ + 0.03))
lathe('fix_pendant_canopy', [(0.0, 0.0), (0.05, 0.0), (0.05, -0.03), (0.01, -0.035)], M['shade'], 32, C, location=(0, LY, H))
WB = (-1.25, Y1 - 0.01, 1.86)
box('fix_wallbulb_base', (WB[0] - 0.05, WB[1] - 0.025, WB[2] - 0.05), (WB[0] + 0.05, WB[1], WB[2] + 0.05), M['steel'], bevel=0.004, collection=C)
lathe('fix_wallbulb_bulb', [(0.0, -0.10), (0.028, -0.095), (0.034, -0.07), (0.02, -0.035), (0.016, 0.0)], M['bulb'], 32, C, location=(WB[0], WB[1] - 0.06, WB[2]))
cage = []
for i in range(6):
    a = 2 * math.pi * i / 6
    cage.append(tube(f'fix_wallbulb_cage_{i}', [(WB[0] + math.cos(a) * 0.045, WB[1] - 0.06 + math.sin(a) * 0.045, WB[2] - 0.005),
                                               (WB[0] + math.cos(a) * 0.05, WB[1] - 0.06 + math.sin(a) * 0.05, WB[2] - 0.06),
                                               (WB[0], WB[1] - 0.06, WB[2] - 0.12)], 0.0018, M['steel'], C))
join('fix_wallbulb_cage', cage, collection=C)
tube('fix_wallbulb_arm', [(WB[0], WB[1] - 0.02, WB[2]), (WB[0], WB[1] - 0.06, WB[2])], 0.012, M['steel'], C)

# ---------------------------------------------------------------- recording camera on tripod (back-left corner) + ceiling dome
TPx, TPy = -1.22, 1.45
for i, a in enumerate((0.3, 2.4, 4.4)):
    tube(f'fix_tripod_leg_{i}', [(TPx + math.cos(a) * 0.32, TPy + math.sin(a) * 0.32, 0.0), (TPx, TPy, 1.22)], 0.011, M['steel'], C)
tube('fix_tripod_column', [(TPx, TPy, 0.95), (TPx, TPy, 1.32)], 0.014, M['steel'], C)
box('fix_tripod_head', (TPx - 0.04, TPy - 0.04, 1.32), (TPx + 0.04, TPy + 0.04, 1.37), M['steel'], bevel=0.006, collection=C)
box('prop_rec_camera_body', (TPx - 0.055, TPy - 0.12, 1.37), (TPx + 0.055, TPy + 0.10, 1.49), M['cam'], bevel=0.012, seg=3, collection=C)
lathe('prop_rec_camera_lens', [(0.0, 0.0), (0.042, 0.0), (0.045, 0.02), (0.045, 0.11), (0.05, 0.115), (0.05, 0.14), (0.0, 0.14)], M['cam'], 40, C, location=(0, 0, 0))
lens = bpy.data.objects['prop_rec_camera_lens']
lens.rotation_euler = (math.radians(-90), 0, math.radians(-38)); lens.location = (TPx + 0.0, TPy - 0.11, 1.43)
lathe('prop_rec_camera_glass', [(0.0, 0.0), (0.036, 0.0), (0.0, 0.004)], M['lens'], 40, C)
g = bpy.data.objects['prop_rec_camera_glass']; g.rotation_euler = lens.rotation_euler; g.location = lens.location + Vector((math.sin(math.radians(38)) * 0.141, -math.cos(math.radians(38)) * 0.141, 0))
box('prop_rec_camera_tally', (TPx - 0.03, TPy - 0.122, 1.475), (TPx - 0.018, TPy - 0.118, 1.483), M['led'], bevel=0, collection=C)
cb = bpy.data.objects['prop_rec_camera_body']; cb.rotation_euler = (0, 0, math.radians(-38))
lathe('fix_ceiling_dome', [(0.0, 0.0), (0.06, 0.0), (0.06, -0.012), (0.05, -0.05), (0.0, -0.065)], M['lens'], 40, C, location=(1.35, -1.35, H))

# ---------------------------------------------------------------- grey steel cabinet (back-right) with file boxes
box('fix_cabinet', (1.22, 1.45, 0), (1.66, 1.95, 1.05), M['cabinet'], bevel=0.006, collection=C)
boxes('fix_cabinet_doors', [((1.225, 1.445, 0.06), (1.44, 1.452, 1.0)), ((1.445, 1.445, 0.06), (1.655, 1.452, 1.0))], M['cabinet'], collection=C, bevel=0.002)
for i, z in enumerate((0.55,)):
    tube('fix_cabinet_handles', [(1.43, 1.44, 0.48), (1.43, 1.44, 0.62)], 0.006, M['chrome'], C)
for i in range(3):
    x = 1.26 + i * 0.13
    box(f'prop_filebox_{i}', (x, 1.55, 1.05), (x + 0.11, 1.90, 1.05 + 0.30 - i * 0.02), M['manila'], bevel=0.004, collection=C)

# ---------------------------------------------------------------- table props
def recorder(at, rot):
    x, y = at
    parts = [box('prop_recorder_body', (x - 0.032, y - 0.07, TZ), (x + 0.032, y + 0.07, TZ + 0.022), M['gun'], bevel=0.008, seg=3, collection=C),
             box('prop_recorder_screen', (x - 0.022, y - 0.01, TZ + 0.0215), (x + 0.022, y + 0.035, TZ + 0.0235), M['screen'], bevel=0.001, collection=C),
             box('prop_recorder_led', (x - 0.004, y + 0.052, TZ + 0.0215), (x + 0.004, y + 0.058, TZ + 0.0245), M['led'], bevel=0.0005, collection=C)]
    for i in range(3):
        parts.append(box(f'prop_recorder_btn_{i}', (x - 0.020 + i * 0.015, y - 0.045, TZ + 0.0215), (x - 0.010 + i * 0.015, y - 0.030, TZ + 0.025), M['rubber'], bevel=0.001, collection=C))
    for i in range(5):
        for j in range(3):
            parts.append(box(f'prop_recorder_grille_{i}_{j}', (x - 0.012 + j * 0.01 - 0.0018, y + 0.040 - 0.0018 - i * 0.006 + 0.0, TZ + 0.0215),
                             (x - 0.012 + j * 0.01 + 0.0018, y + 0.040 + 0.0018 - i * 0.006, TZ + 0.0222), M['ink'], bevel=0, collection=C))
    o = join('prop_recorder', parts, origin=(x, y, TZ), collection=C)
    o.rotation_euler.z = rot
recorder((0.30, -0.22), math.radians(-12))

def folder_stack(at, rot):
    x, y = at
    parts = []
    z = TZ
    for i in range(3):
        dx, dy = random.uniform(-0.006, 0.006), random.uniform(-0.006, 0.006)
        parts.append(box(f'prop_casefile_cover_b{i}', (x - 0.115 + dx, y - 0.155 + dy, z), (x + 0.115 + dx, y + 0.155 + dy, z + 0.0012), M['manila'], bevel=0, collection=C))
        parts.append(box(f'prop_casefile_pages{i}', (x - 0.108 + dx, y - 0.150 + dy, z + 0.0012), (x + 0.110 + dx, y + 0.148 + dy, z + 0.009), M['paper'], bevel=0.0006, collection=C))
        parts.append(box(f'prop_casefile_cover_t{i}', (x - 0.115 + dx, y - 0.155 + dy, z + 0.009), (x + 0.115 + dx, y + 0.155 + dy, z + 0.0102), M['manila'], bevel=0, collection=C))
        z += 0.0105
    parts.append(text_mesh('prop_casefile_title', '수사기록', 0.034, (x, y + 0.06, z + 0.0002), (0, 0, math.pi), M['ink'], FONT, collection=C, bold=0.003))
    parts.append(text_mesh('prop_casefile_case', 'CASE 001  ·  정수연 사망 사건', 0.0105, (x, y + 0.02, z + 0.0002), (0, 0, math.pi), M['ink'], FONT, collection=C))
    parts.append(text_mesh('prop_casefile_stamp', '형사과 강력1팀', 0.012, (x + 0.03, y - 0.09, z + 0.0002), (0, 0, math.pi + 0.12), M['redink'], FONT, collection=C, bold=0.002))
    o = join('prop_casefile', parts, origin=(x, y, TZ), collection=C)
    o.rotation_euler.z = rot
folder_stack((0.60, -0.16), math.radians(14))

def statement_form(at, rot):
    x, y = at
    parts = [box('prop_statement_sheet', (x - 0.105, y - 0.1485, TZ), (x + 0.105, y + 0.1485, TZ + 0.0006), M['paper'], bevel=0, collection=C)]
    # printed form faces the suspect (text reads from +Y side): title, rule lines, signature box
    parts.append(text_mesh('prop_statement_title', '진 술 서', 0.016, (x, y - 0.115, TZ + 0.0007), (0, 0, 0), M['ink'], FONT, collection=C, bold=0.0015))
    for i in range(16):
        yy = y - 0.085 + i * 0.0135
        parts.append(box(f'prop_statement_rule_{i}', (x - 0.09, yy, TZ + 0.0006), (x + 0.09, yy + 0.0009, TZ + 0.00075), M['rule'], bevel=0, collection=C))
    for i in range(5):     # a few handwritten-looking lines already filled in
        yy = y - 0.080 + i * 0.0135
        w = random.uniform(0.10, 0.17)
        parts.append(box(f'prop_statement_hand_{i}', (x - 0.088, yy + 0.002, TZ + 0.0006), (x - 0.088 + w, yy + 0.0048, TZ + 0.0008), M['ink'], bevel=0, collection=C))
    parts.append(box('prop_statement_sign', (x + 0.03, y + 0.118, TZ + 0.0006), (x + 0.09, y + 0.1385, TZ + 0.00075), M['redink'], bevel=0, collection=C))
    o = join('prop_statement', parts, origin=(x, y, TZ), collection=C)
    o.rotation_euler.z = rot
statement_form((0.04, 0.20), math.radians(-6))
tube('prop_pen', [(0.17, 0.10, TZ + 0.0045), (0.30, 0.15, TZ + 0.0045)], 0.0045, M['ink'], C)
lathe('prop_paper_cup', [(0.0, 0.0), (0.026, 0.0), (0.027, 0.002), (0.036, 0.088), (0.038, 0.09), (0.036, 0.091), (0.034, 0.089), (0.025, 0.003), (0.0, 0.003)],
      M['cup'], 48, C, location=(-0.32, 0.25, TZ))
lathe('prop_paper_cup_water', [(0.0, 0.055), (0.0325, 0.055)], M['water'], 48, C, location=(-0.32, 0.25, TZ))
lathe('prop_glass', [(0.0, 0.0), (0.030, 0.0), (0.032, 0.004), (0.036, 0.105), (0.033, 0.105), (0.029, 0.008), (0.0, 0.008)], M['glass'], 48, C, location=(-0.58, -0.24, TZ))
lathe('prop_glass_water', [(0.0, 0.009), (0.0295, 0.009), (0.0335, 0.07), (0.0, 0.07)], M['water'], 48, C, location=(-0.58, -0.24, TZ))

# ---------------------------------------------------------------- export
out_fbx = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else os.path.join(REPO, 'blender', 'out', 'Interrogation2.fbx')
out_blend = sys.argv[sys.argv.index('--') + 2] if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 2 else out_fbx.replace('.fbx', '.blend')
os.makedirs(os.path.dirname(out_fbx), exist_ok=True)
export_fbx(out_fbx)
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
print('INTERROGATION_BUILT', len(bpy.data.objects), out_fbx)
