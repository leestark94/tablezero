"""Reusable prop builders for CASE 001 rooms (extracted from v1)."""
import math, random
import bpy, bmesh
from mathutils import Vector, Matrix
from tzlib import *
from tzlib import _box_bm
M = {}

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
            parts.append(tube('tmp_ear%d' % s, [(x + s * 0.012, y, z + sz - 0.01), (x + s * 0.035, y + 0.012, z + sz + 0.025),
                                                  (x + s * 0.05, y - 0.006, z + sz + 0.012), (x + s * 0.03, y - 0.01, z + sz - 0.01)], 0.007, material))
    o = join(name, parts, origin=at)
    shade_smooth_auto(o, 60)
    return o

def blood_decal(name, at, r):
    """Irregular pooled stain with a darker dried rim and a few satellite drops (no star shape)."""
    x, y, z = at
    rnd = random.Random(41)
    bm = bmesh.new()
    def blob(cx, cy, rad, n=40, zz=z):
        ph = [rnd.uniform(0, 6.28) for _ in range(4)]
        ctr = bm.verts.new((cx, cy, zz))
        ring = []
        for i in range(n):
            a = 2 * math.pi * i / n
            k = 1 + 0.18 * math.sin(2 * a + ph[0]) + 0.10 * math.sin(3 * a + ph[1]) + 0.06 * math.sin(7 * a + ph[2]) + rnd.uniform(-0.03, 0.03)
            ring.append(bm.verts.new((cx + rad * k * math.cos(a) * 1.25, cy + rad * k * math.sin(a), zz)))
        for i in range(n):
            bm.faces.new((ctr, ring[i], ring[(i + 1) % n]))
    blob(x, y, r)
    blob(x + r * 0.9, y - r * 0.4, r * 0.35, 24)
    for i in range(7):
        a = rnd.uniform(0, 6.28); d = r * rnd.uniform(1.3, 2.4)
        blob(x + d * math.cos(a), y + d * math.sin(a), rnd.uniform(0.006, 0.014), 10, z + 0.0001)
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
