"""Second-pass prop builders (room polish v3): loft modeller + Korean household items.
All coordinates in Blender meters (Z up). Objects are real geometry with smooth shading where curved."""
import math, random
import bpy, bmesh
from mathutils import Vector, Matrix
from tzlib import *
from tzlib import _box_bm

M = {}

def loft(name, rings, material, steps=40, cap_bottom=True, cap_top=False, location=(0, 0, 0), smooth=True, superness=2.0):
    """Connect elliptical / superelliptical cross-sections.
    rings: [(z, rx, ry, cx, cy), ...] in local coords. superness>2 gives squarer sections."""
    bm = bmesh.new()
    loops = []
    for (z, rx, ry, cx, cy) in rings:
        ring = []
        for i in range(steps):
            a = 2 * math.pi * i / steps
            c, s = math.cos(a), math.sin(a)
            e = 2.0 / superness
            x = cx + rx * math.copysign(abs(c) ** e, c)
            y = cy + ry * math.copysign(abs(s) ** e, s)
            ring.append(bm.verts.new((x, y, z)))
        loops.append(ring)
    for k in range(len(loops) - 1):
        a, b = loops[k], loops[k + 1]
        for i in range(steps):
            j = (i + 1) % steps
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if cap_bottom:
        bm.faces.new(list(reversed(loops[0])))
    if cap_top:
        bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for l in f.loops:
            co = l.vert.co
            l[uv].uv = ((math.atan2(co.y, co.x) / (2 * math.pi) + 0.5), co.z * 3)
    for v in bm.verts:
        v.co += Vector(location)
    return mesh_obj(name, bm, material, origin=location, uv=False, smooth=smooth)

def toilet(prefix, at, facing=-1):
    """Korean one-piece-style close-coupled toilet: footed trapway skirt, elongated bowl with rim and
    water surface, separate tank with lid and push button. Bowl front points to facing*X.
    Returns (bowl_obj, seat_pivot). Seat/lid are built by the caller with loft too."""
    x, y, z = at
    # bowl rings (local: +X = front). (z, rx, ry, cx, cy)
    outer = [(0.00, 0.13, 0.11, -0.02, 0), (0.06, 0.135, 0.115, -0.02, 0), (0.16, 0.15, 0.13, 0.0, 0),
             (0.26, 0.19, 0.16, 0.03, 0), (0.33, 0.215, 0.175, 0.04, 0), (0.375, 0.225, 0.18, 0.04, 0),
             (0.39, 0.222, 0.177, 0.04, 0)]
    inner = [(0.39, 0.195, 0.15, 0.045, 0), (0.37, 0.185, 0.14, 0.045, 0), (0.30, 0.15, 0.11, 0.05, 0),
             (0.24, 0.10, 0.08, 0.06, 0), (0.20, 0.07, 0.06, 0.06, 0)]
    bowl = loft(prefix + '_bowl_tmp', outer + inner, M['porc'], steps=48, cap_bottom=True, cap_top=True, location=(0, 0, 0))
    bowl.data.transform(Matrix.Rotation(0 if facing > 0 else math.pi, 4, 'Z'))
    bowl.location = (x, y, z)
    water = loft(prefix + '_water_tmp', [(0.20, 0.069, 0.059, 0.06, 0), (0.201, 0.069, 0.059, 0.06, 0)],
                 [mat('M_ToiletWater', (0.7, 0.8, 0.85, 0.35), 0.02)], steps=32, cap_top=True, location=(0, 0, 0))
    water.data.transform(Matrix.Rotation(0 if facing > 0 else math.pi, 4, 'Z'))
    water.location = (x, y, z)
    return [bowl, water]

def toilet_seat_and_lid(seat_name, lid_name, at, hinge_x, facing=-1, open_lid=True):
    """Seat ring + lid (closed shape), pivots on the rear hinge so TZPropMotion can lift them."""
    x, y, z = at
    rot = 0 if facing > 0 else math.pi
    # seat: flat superelliptic ring
    bm = bmesh.new()
    steps = 48
    rings = []
    for (r_x, r_y, zz) in [(0.20, 0.165, 0.0), (0.205, 0.17, 0.012), (0.20, 0.165, 0.022), (0.14, 0.10, 0.022), (0.135, 0.095, 0.008), (0.14, 0.10, 0.0)]:
        ring = []
        for i in range(steps):
            a = 2 * math.pi * i / steps
            ring.append(bm.verts.new((0.045 + r_x * math.cos(a), r_y * math.sin(a), zz)))
        rings.append(ring)
    for k in range(len(rings)):
        a, b = rings[k], rings[(k + 1) % len(rings)]
        for i in range(steps):
            j = (i + 1) % steps
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.transform(Matrix.Rotation(rot, 4, 'Z'))
    for v in bm.verts:
        v.co += Vector((x, y, z + 0.392))
    seat = mesh_obj(seat_name, bm, M['pw'], origin=(x, y, z + 0.392), smooth=True)
    lid = loft(lid_name, [(0.0, 0.205, 0.17, 0.045, 0), (0.018, 0.204, 0.168, 0.045, 0), (0.03, 0.19, 0.155, 0.045, 0), (0.034, 0.16, 0.13, 0.045, 0)],
               M['pw'], steps=48, cap_bottom=True, cap_top=True, location=(0, 0, 0))
    lid.data.transform(Matrix.Rotation(rot, 4, 'Z'))
    lid.location = (x, y, z + 0.414)
    bpy.context.view_layer.update()
    set_origin(seat, (hinge_x, y, z + 0.40))
    set_origin(lid, (hinge_x, y, z + 0.42))
    return seat, lid

def floor_chair(name, at, rot_z=0.5):
    """좌식의자 knocked over backwards: backrest flat on the floor, padded seat tipped up on the hinge."""
    x, y, _ = at
    def cushion(tag, w, d, t, puff=0.018):
        bm = bmesh.new()
        _box_bm(bm, (-w / 2, 0, 0), (w / 2, d, t))
        bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=5, use_grid_fill=True)
        for v in bm.verts:
            u, s2 = v.co.x / (w / 2), (v.co.y - d / 2) / (d / 2)
            k = max(0.0, 1 - 0.6 * (u * u + s2 * s2))
            if v.co.z > t * 0.5:
                v.co.z += puff * k
            else:
                v.co.z -= puff * 0.3 * k
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.008, segments=2, affect='EDGES')
        o = mesh_obj(tag, bm, M['vinylcover'], origin=(0, 0, 0), smooth=True)
        ss = o.modifiers.new('s', 'SUBSURF'); ss.levels = 1; bake(o)
        return o
    back = cushion('tmp_fback', 0.42, 0.46, 0.05)                 # lies on the floor, hinge at y=0
    seat = cushion('tmp_fseat', 0.42, 0.42, 0.055)
    seat.data.transform(Matrix.Rotation(math.radians(180 - 72), 4, 'X'))   # seat swung up, ~72 deg off the floor
    seat.data.transform(Matrix.Translation((0, 0, 0.055)))
    hinge = boxes('tmp_fhinge', [((-0.215, -0.04, 0.0), (-0.205, 0.05, 0.09)), ((0.205, -0.04, 0.0), (0.215, 0.05, 0.09))], M['steel'], bevel=0.002)
    c = join(name, [seat, back, hinge], origin=(0, 0, 0))
    c.data.transform(Matrix.Rotation(rot_z, 4, 'Z'))
    bpy.context.view_layer.update()
    mn = min(v.co.z for v in c.data.vertices)
    c.location = (x, y, -mn)
    return c

def rice_cooker(name, at, rot=0.0):
    """전기밥솥 (6인용): rounded body, lid with release button and steam cap, front display."""
    x, y, z = at
    body = loft('tmp_rcb', [(0.0, 0.135, 0.125, 0, 0), (0.01, 0.15, 0.14, 0, 0), (0.20, 0.155, 0.145, 0, 0), (0.225, 0.15, 0.14, 0, 0)],
                [M['pw']], steps=40, cap_top=True, superness=2.4)
    lid = loft('tmp_rcl', [(0.225, 0.148, 0.138, 0, 0), (0.25, 0.14, 0.13, 0, 0), (0.262, 0.11, 0.10, 0, 0), (0.265, 0.0, 0.0, 0, 0)],
               [mat('M_RiceCookerLid', (0.52, 0.10, 0.12, 1), 0.35)], steps=40, superness=2.4)
    cap = loft('tmp_rcc', [(0.262, 0.025, 0.025, 0.03, 0), (0.28, 0.022, 0.022, 0.03, 0)], [M['pg']], steps=16, cap_top=True)
    btn = boxes('tmp_rcbtn', [((0.12, -0.03, 0.20), (0.152, 0.03, 0.225))], M['pg'], bevel=0.004)
    disp = boxes('tmp_rcd', [((0.148, -0.05, 0.11), (0.157, 0.05, 0.17))], M['screen'], bevel=0.002)
    o = join(name, [body, lid, cap, btn, disp], origin=(0, 0, 0))
    o.data.transform(Matrix.Rotation(rot, 4, 'Z'))
    o.location = at
    return o

def kettle(name, at, rot=0.0):
    """전기포트: tapered body, spout, handle, base plate."""
    x, y, z = at
    base = loft('tmp_kb', [(0.0, 0.085, 0.085, 0, 0), (0.02, 0.085, 0.085, 0, 0)], [M['pb']], steps=32, cap_top=True)
    body = loft('tmp_kbody', [(0.02, 0.075, 0.075, 0, 0), (0.12, 0.08, 0.08, 0, 0), (0.20, 0.068, 0.068, 0, 0), (0.215, 0.06, 0.06, 0, 0)],
                [M['steel']], steps=32, cap_top=True)
    spout = tube('tmp_ks', [(0.06, 0, 0.17), (0.095, 0, 0.20), (0.11, 0, 0.215)], 0.012, M['steel'])
    handle = tube('tmp_kh', [(-0.07, 0, 0.19), (-0.115, 0, 0.17), (-0.11, 0, 0.07), (-0.07, 0, 0.05)], 0.012, M['pb'])
    o = join(name, [base, body, spout, handle], origin=(0, 0, 0))
    o.data.transform(Matrix.Rotation(rot, 4, 'Z'))
    o.location = at
    return o

def spoon_holder(name, at):
    """수저통 with spoons and chopsticks standing in it."""
    x, y, z = at
    cup = loft('tmp_sh', [(0.0, 0.04, 0.04, 0, 0), (0.13, 0.045, 0.045, 0, 0), (0.13, 0.042, 0.042, 0, 0), (0.005, 0.037, 0.037, 0, 0)],
               [M['steel']], steps=24)
    parts = [cup]
    rnd = random.Random(5)
    for i in range(5):
        a = i * 1.25
        r = 0.02
        top = (r * math.cos(a) * 2.2, r * math.sin(a) * 2.2, 0.24 + rnd.uniform(0, 0.03))
        parts.append(tube(f'tmp_ut{i}', [(r * math.cos(a), r * math.sin(a), 0.02), top], 0.0035, M['steel']))
    o = join(name, parts, origin=(0, 0, 0))
    o.location = at
    return o

def rubber_gloves(name, at, rot=0.0):
    """고무장갑 pair draped over the counter front edge: flat cuff on the worktop, palm hanging, four fingers + thumb."""
    x, y, z = at
    pink = mat('M_RubberGlovePink', (0.85, 0.35, 0.45, 1), 0.45)
    parts = []
    rnd = random.Random(11)
    for k, dy in enumerate((-0.05, 0.045)):
        band = tube(f'tmp_rgb{k}', [(-0.07, 0, 0.004), (0.0, 0, 0.007), (0.05, 0, 0.0), (0.075, 0, -0.04), (0.08, 0, -0.12)], 0.013, pink)
        band.data.transform(Matrix.Diagonal((1, 2.7, 1, 1)))
        band.data.transform(Matrix.Translation((0, dy, 0)))
        parts.append(band)
        for i, fy in enumerate((-0.026, -0.009, 0.009, 0.026)):
            L = 0.07 + rnd.uniform(-0.01, 0.012) - (0.012 if i in (0, 3) else 0)
            parts.append(tube(f'tmp_rgf{k}{i}', [(0.08, dy + fy, -0.115), (0.082, dy + fy * 1.08, -0.115 - L * 0.6), (0.085, dy + fy * 1.1, -0.115 - L)], 0.0075, pink))
        parts.append(tube(f'tmp_rgt{k}', [(0.078, dy + 0.034, -0.06), (0.082, dy + 0.055, -0.09), (0.085, dy + 0.06, -0.115)], 0.0085, pink))
    o = join(name, parts, origin=(0, 0, 0))
    o.data.transform(Matrix.Rotation(rot, 4, 'Z'))
    o.location = at
    shade_smooth_auto(o, 60)
    return o

def condiments(name, at):
    """간장·식용유·참기름 bottles on the counter corner."""
    x, y, z = at
    soy = loft('tmp_soy', [(0, 0.035, 0.035, 0, 0), (0.17, 0.035, 0.035, 0, 0), (0.21, 0.014, 0.014, 0, 0), (0.24, 0.014, 0.014, 0, 0)],
               [mat('M_SoyBottle', (0.08, 0.04, 0.02, 0.85), 0.7)], steps=20, cap_top=True)
    oil = loft('tmp_oil', [(0, 0.032, 0.032, 0.08, 0), (0.22, 0.032, 0.032, 0.08, 0), (0.26, 0.012, 0.012, 0.08, 0), (0.28, 0.012, 0.012, 0.08, 0)],
               [mat('M_OilBottle', (0.85, 0.70, 0.25, 0.6), 0.8)], steps=20, cap_top=True)
    ses = loft('tmp_ses', [(0, 0.025, 0.025, 0.04, 0.07), (0.13, 0.025, 0.025, 0.04, 0.07), (0.16, 0.01, 0.01, 0.04, 0.07), (0.18, 0.01, 0.01, 0.04, 0.07)],
               [mat('M_SesameBottle', (0.35, 0.18, 0.05, 0.85), 0.7)], steps=20, cap_top=True)
    caps = [loft(f'tmp_cap{i}', [(h, 0.016, 0.016, cx, cy), (h + 0.02, 0.016, 0.016, cx, cy)], [M['red'] if i == 0 else M['green']], steps=12, cap_top=True)
            for i, (h, cx, cy) in enumerate([(0.24, 0, 0), (0.28, 0.08, 0), (0.18, 0.04, 0.07)])]
    o = join(name, [soy, oil, ses] + caps, origin=(0, 0, 0))
    o.location = at
    return o

def detergent(name, at, rot=0.0):
    """액체세제 jug on the washer (handle + cap)."""
    jug = loft('tmp_dj', [(0, 0.09, 0.055, 0, 0), (0.24, 0.085, 0.052, 0, 0), (0.27, 0.05, 0.04, -0.02, 0), (0.29, 0.03, 0.03, -0.03, 0)],
               [mat('M_DetergentBlue', (0.25, 0.45, 0.75, 1), 0.5)], steps=24, cap_top=True, superness=3.0)
    cap = loft('tmp_dc', [(0.29, 0.032, 0.032, -0.03, 0), (0.33, 0.032, 0.032, -0.03, 0)], [M['pw']], steps=16, cap_top=True)
    o = join(name, [jug, cap], origin=(0, 0, 0))
    o.data.transform(Matrix.Rotation(rot, 4, 'Z'))
    o.location = at
    return o

def dipper(name, at):
    """욕실 바가지: shallow bowl with a short handle."""
    bowl = loft('tmp_dp', [(0.0, 0.07, 0.07, 0, 0), (0.07, 0.11, 0.11, 0, 0), (0.072, 0.105, 0.105, 0, 0), (0.008, 0.065, 0.065, 0, 0)],
                [mat('M_DipperPink', (0.85, 0.55, 0.60, 1), 0.5)], steps=32)
    hd = boxes('tmp_dph', [((0.10, -0.02, 0.05), (0.18, 0.02, 0.066))], mat('M_DipperPink', (0.85, 0.55, 0.60, 1), 0.5), bevel=0.006)
    o = join(name, [bowl, hd], origin=(0, 0, 0))
    o.location = at
    return o

def tissue_box(name, at, rot=0.0):
    """각티슈 with a tissue sticking out."""
    bx = boxes('tmp_tb', [((-0.12, -0.06, 0), (0.12, 0.06, 0.085))], [mat('M_TissueBox', (0.75, 0.82, 0.78, 1), 0.6)], bevel=0.004)
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in [(-0.05, -0.005, 0.085), (0.05, 0.005, 0.085), (0.03, 0.02, 0.15), (-0.04, 0.0, 0.14)]]
    bm.faces.new(v)
    t = mesh_obj('tmp_tt', bm, M['paper'], origin=(0, 0, 0))
    sm = t.modifiers.new('s', 'SOLIDIFY'); sm.thickness = 0.001; bake(t)
    o = join(name, [bx, t], origin=(0, 0, 0))
    o.data.transform(Matrix.Rotation(rot, 4, 'Z'))
    o.location = at
    return o

def cable(name, pts, r=0.0025, m=None):
    return tube(name, pts, r, m or M['pw'])

def flat_plate(name, mn, mx, m, rot_z=0.0):
    o = box(name, mn, mx, m, bevel=0)
    o.rotation_euler = (0, 0, rot_z)
    return o
