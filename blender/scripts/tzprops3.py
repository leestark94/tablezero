"""Third-pass prop builders (room polish v4).
- crime-scene surface marks as UV-fitted cards (textures are generated procedurally in Unity: gen_blood*, gen_shoeprint, gen_printdoc)
- the delivery 떡볶이/순대 set as real food geometry, an opened delivery bag
- cloth-simulated soft goods (rubber gloves over the counter edge, hoodie over the bed, towel on the bar)
- evidence marker tents (kit objects the game places when the detective photographs something)
All coordinates in Blender meters (Z up)."""
import math, random
import bpy, bmesh
from mathutils import Vector, Matrix
from tzlib import *
from tzlib import _box_bm
import tzprops2

M = {}


# ----------------------------------------------------------------------------- UV helpers
def fit_uv(obj, axis='z', u_range=(0.0, 1.0), v_range=(0.0, 1.0), flip_u=False):
    """Planar UVs normalised to the object's own bounds (one texture = one card)."""
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new()
    uv = me.uv_layers.active.data
    cs = [v.co for v in me.vertices]
    ia, ib = {'z': (0, 1), 'y': (0, 2), 'x': (1, 2)}[axis]
    amin, amax = min(c[ia] for c in cs), max(c[ia] for c in cs)
    bmin, bmax = min(c[ib] for c in cs), max(c[ib] for c in cs)
    for p in me.polygons:
        for li in p.loop_indices:
            c = me.vertices[me.loops[li].vertex_index].co
            u = (c[ia] - amin) / max(amax - amin, 1e-6)
            v = (c[ib] - bmin) / max(bmax - bmin, 1e-6)
            if flip_u:
                u = 1 - u
            uv[li].uv = (u_range[0] + u * (u_range[1] - u_range[0]), v_range[0] + v * (v_range[1] - v_range[0]))


def card(name, cx, cy, z, w, h, rot, material, u_range=(0, 1), v_range=(0, 1), flip_u=False, nx=1, ny=1, bend=None):
    """Flat floor/table card (w along local x, h along local y) with UVs in the given atlas window.
    bend(u, v) -> dz lets paper curl. Created at origin, rotated, then moved (UVs follow the card)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.verify()
    vs = [[bm.verts.new(((i / nx - 0.5) * w, (j / ny - 0.5) * h, bend(i / nx, j / ny) if bend else 0.0)) for i in range(nx + 1)] for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
            for l, (a, b) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                u = a / nx
                if flip_u:
                    u = 1 - u
                l[uvl].uv = (u_range[0] + u * (u_range[1] - u_range[0]), v_range[0] + (b / ny) * (v_range[1] - v_range[0]))
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(rot, 3, 'Z'))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(cx, cy, z))
    return mesh_obj(name, bm, material, origin=(cx, cy, z), uv=False)


def wall_card(name, center, normal_axis, w, h, material, u_range=(0, 1), v_range=(0, 1)):
    """Vertical card facing +/-x or +/-y (for drips on furniture sides)."""
    cx, cy, cz = center
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.verify()
    if normal_axis in ('+x', '-x'):
        pts = [(cx, cy - w / 2, cz - h / 2), (cx, cy + w / 2, cz - h / 2), (cx, cy + w / 2, cz + h / 2), (cx, cy - w / 2, cz + h / 2)]
        if normal_axis == '-x':
            pts = [pts[1], pts[0], pts[3], pts[2]]
    else:
        pts = [(cx + w / 2, cy, cz - h / 2), (cx - w / 2, cy, cz - h / 2), (cx - w / 2, cy, cz + h / 2), (cx + w / 2, cy, cz + h / 2)]
        if normal_axis == '-y':
            pts = [pts[1], pts[0], pts[3], pts[2]]
    f = bm.faces.new([bm.verts.new(p) for p in pts])
    for l, (a, b) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        l[uvl].uv = (u_range[0] + a * (u_range[1] - u_range[0]), v_range[0] + b * (v_range[1] - v_range[0]))
    return mesh_obj(name, bm, material, origin=center, uv=False)


# ----------------------------------------------------------------------------- blood (textures generated in Unity)
def blood_pool(name, at, w=0.66, h=0.52, rot=0.35):
    """Pooled blood at the table corner: one card, the shape lives in gen_bloodpool (wet centre, dried rim, satellites)."""
    x, y, z = at
    return card(name, x, y, z, w, h, rot, M['bloodpool'])


def blood_smear(name, pts, width, z=0.0016):
    """CPR drag smear: strip along pts, u runs along the path (streaks thin out toward the end), v across."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.verify()
    n = len(pts)
    seg = [0.0]
    for i in range(1, n):
        seg.append(seg[-1] + math.dist(pts[i - 1], pts[i]))
    total = seg[-1] or 1
    L, R = [], []
    for i, (x, y) in enumerate(pts):
        ax, ay = pts[max(i - 1, 0)]; bx, by = pts[min(i + 1, n - 1)]
        nx, ny = (by - ay), -(bx - ax)
        l = math.hypot(nx, ny) or 1
        w = width * (1.0 - 0.45 * seg[i] / total)
        L.append(bm.verts.new((x + nx / l * w, y + ny / l * w, z)))
        R.append(bm.verts.new((x - nx / l * w, y - ny / l * w, z)))
    for i in range(n - 1):
        f = bm.faces.new((L[i], R[i], R[i + 1], L[i + 1]))
        for lp, (u, v) in zip(f.loops, ((seg[i] / total, 1), (seg[i] / total, 0), (seg[i + 1] / total, 0), (seg[i + 1] / total, 1))):
            lp[uvl].uv = (u, v)
    return mesh_obj(name, bm, M['bloodsmear'], origin=(pts[0][0], pts[0][1], 0.0), uv=False)


def shoeprints(name, steps):
    """Partial bloody sole prints walking away from the pool (119 crew). gen_shoeprint is a 4-column atlas:
    column = transfer strength (0 strongest .. 3 faint). steps: [(x, y, heading, left, column)]."""
    parts = []
    for i, (x, y, hd, left, col) in enumerate(steps):
        parts.append(card(f'tmp_sp{i}', x, y, 0.0013 + i * 0.00005, 0.11, 0.29, hd, M['shoeprint'],
                          u_range=(col * 0.25, col * 0.25 + 0.25), flip_u=not left))
    return join(name, parts, origin=(steps[0][0], steps[0][1], 0.0))


def spatter_cards(name, items, origin):
    """gen_bloodspatter atlas: column 0 = drop cluster (horizontal surfaces), column 1 = drips/runs (vertical surfaces).
    items: ('h', x, y, z, size, rot) or ('v', (cx,cy,cz), axis, w, h)."""
    parts = []
    for i, it in enumerate(items):
        if it[0] == 'h':
            _, x, y, z, s, r = it
            parts.append(card(f'tmp_bs{i}', x, y, z, s, s, r, M['bloodspatter'], u_range=(0.0, 0.5)))
        else:
            _, c, ax, w, h = it
            parts.append(wall_card(f'tmp_bs{i}', c, ax, w, h, M['bloodspatter'], u_range=(0.5, 1.0)))
    return join(name, parts, origin=origin)


# ----------------------------------------------------------------------------- printed paper
def sheet(name, x, y, z, rot, page=0, curl=0.0, lift_corner=0.0):
    """A4 sheet (0.21 x 0.297) printed with gen_printdoc (2-page atlas). curl lifts the long edges, lift_corner one corner."""
    def bend(u, v):
        return curl * ((u - 0.5) ** 2) * 4 + lift_corner * max(0.0, (u - 0.6) / 0.4) * max(0.0, (v - 0.6) / 0.4)
    return card(name, x, y, z, 0.21, 0.297, rot, M['printdoc'], u_range=(page * 0.5, page * 0.5 + 0.5), nx=6, ny=8, bend=bend)


# ----------------------------------------------------------------------------- delivery food
def _mat_by_normal(obj, axis_vec, index, thresh=0.8):
    for p in obj.data.polygons:
        if abs(p.normal.dot(Vector(axis_vec))) > thresh:
            p.material_index = index


def tteokbokki(name, at, rot=0.0):
    """떡볶이 in a black PP takeout tray, about half eaten: sauce, rice cakes, 어묵, 대파."""
    rnd = random.Random(5)
    x, y, z = at
    tray = tzprops2.loft('tmp_tbtray', [(0.0, 0.078, 0.056, 0, 0), (0.004, 0.080, 0.058, 0, 0), (0.052, 0.090, 0.066, 0, 0),
                                         (0.056, 0.095, 0.071, 0, 0), (0.058, 0.094, 0.070, 0, 0)],
                         [M['pb']], steps=40, superness=4.5, location=(x, y, z))
    sm = tray.modifiers.new('s', 'SOLIDIFY'); sm.thickness = 0.0015; bake(tray)
    sauce = tzprops2.loft('tmp_tbsauce', [(0.022, 0.083, 0.060, 0, 0), (0.0225, 0.083, 0.060, 0, 0)], [M['sauce']], steps=40,
                          cap_top=True, superness=4.5, location=(x, y, z))
    parts = [tray, sauce]
    cake_m = M['ricecake_sauced']
    placed = 0
    for i in range(14):
        cx, cy = rnd.uniform(-0.06, 0.06), rnd.uniform(-0.04, 0.04)
        if cx > 0.01 and rnd.random() < 0.75:      # the eaten half (left side) has little left
            continue
        a = rnd.uniform(0, math.pi)
        L = rnd.uniform(0.035, 0.05)
        p0 = (x + cx - math.cos(a) * L / 2, y + cy - math.sin(a) * L / 2, z + 0.03 + rnd.uniform(0, 0.006))
        p1 = (x + cx + math.cos(a) * L / 2, y + cy + math.sin(a) * L / 2, p0[2] + rnd.uniform(-0.002, 0.003))
        parts.append(tube(f'tmp_tbc{i}', [p0, p1], 0.0075, cake_m, res=10))
        placed += 1
    for i in range(3):                                 # 어묵 folded sheets
        cx, cy = rnd.uniform(-0.07, -0.01), rnd.uniform(-0.04, 0.04)
        o = box(f'tmp_tbe{i}', (x + cx - 0.022, y + cy - 0.013, z + 0.028), (x + cx + 0.022, y + cy + 0.013, z + 0.032), M['fishcake'], bevel=0.0015)
        o.rotation_euler = (rnd.uniform(-0.3, 0.3), rnd.uniform(-0.2, 0.2), rnd.uniform(0, 3))
        parts.append(o)
    for i in range(9):                                 # 대파 slices
        cx, cy = rnd.uniform(-0.07, 0.07), rnd.uniform(-0.05, 0.05)
        parts.append(tzprops2.loft(f'tmp_tbp{i}', [(0, 0.006, 0.006, 0, 0), (0.002, 0.006, 0.006, 0, 0)], [M['scallion']], steps=10,
                                   cap_top=True, location=(x + cx, y + cy, z + 0.0235)))
    o = join(name, parts, origin=(x, y, z))
    o.rotation_euler = (0, 0, rot)
    tray_lid = tzprops2.loft(name + '_lid_tmp', [(0.0, 0.096, 0.072, 0, 0), (0.006, 0.096, 0.072, 0, 0), (0.008, 0.090, 0.066, 0, 0)],
                             [M['foodlid']], steps=40, cap_top=True, superness=4.5)
    return o, tray_lid


def sundae(name, at, rot=0.0):
    """순대 tray with the clear lid still on: sliced 순대 (dark casing, grey-purple cut face), 간, a salt packet on the lid."""
    rnd = random.Random(8)
    x, y, z = at
    tray = tzprops2.loft('tmp_sdtray', [(0.0, 0.070, 0.050, 0, 0), (0.044, 0.080, 0.058, 0, 0), (0.047, 0.083, 0.061, 0, 0)],
                         [M['pw']], steps=40, superness=4.5, location=(x, y, z))
    sm = tray.modifiers.new('s', 'SOLIDIFY'); sm.thickness = 0.0015; bake(tray)
    parts = [tray]
    k = 0
    for row in range(3):
        for col in range(6):
            cx = -0.055 + col * 0.021 + rnd.uniform(-0.002, 0.002)
            cy = -0.03 + row * 0.03
            s = tzprops2.loft(f'tmp_sds{k}', [(-0.006, 0.0145, 0.0145, 0, 0), (0.006, 0.0145, 0.0145, 0, 0)], [M['sundae_casing'], M['sundae_cut']],
                              steps=14, cap_top=True)
            _mat_by_normal(s, (0, 0, 1), 1)
            s.data.transform(Matrix.Rotation(math.radians(58) + rnd.uniform(-0.12, 0.12), 4, 'Y'))
            s.location = (x + cx, y + cy, z + 0.013)
            parts.append(s); k += 1
    for i in range(3):
        o = box(f'tmp_sdl{i}', (x + 0.03 + i * 0.012, y + 0.035, z + 0.004), (x + 0.04 + i * 0.012, y + 0.06, z + 0.02), M['liver'], bevel=0.003)
        o.rotation_euler = (0.3, 0, 0.1); parts.append(o)
    lid = tzprops2.loft('tmp_sdlid', [(0.047, 0.084, 0.062, 0, 0), (0.05, 0.084, 0.062, 0, 0), (0.056, 0.078, 0.056, 0, 0)],
                        [M['foodlid']], steps=40, cap_top=True, superness=4.5, location=(x, y, z))
    parts.append(lid)
    parts.append(box('tmp_salt', (x - 0.03, y - 0.015, z + 0.0565), (x + 0.012, y + 0.012, z + 0.059), M['saltpack'], bevel=0.001))
    o = join(name, parts, origin=(x, y, z))
    o.rotation_euler = (0, 0, rot)
    return o


def danmuji(name, at):
    """단무지 cup: clear round tub, yellow half-moon slices."""
    x, y, z = at
    cup = lathe('tmp_dmc', [(0, 0), (0.033, 0), (0.038, 0.035), (0.039, 0.037), (0.0, 0.037)], [M['foodlid']], 28, location=(x, y, z))
    parts = [cup]
    for i in range(4):
        s = tzprops2.loft(f'tmp_dms{i}', [(0, 0.028, 0.028, 0, 0), (0.005, 0.028, 0.028, 0, 0)], [M['danmuji']], steps=20, cap_top=True)
        bm = bmesh.new(); bm.from_mesh(s.data)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True)
        bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=0)
        bm.to_mesh(s.data); bm.free()
        s.data.transform(Matrix.Rotation(0.4 * i, 4, 'Z'))
        s.location = (x - 0.005, y, z + 0.004 + i * 0.0055)
        parts.append(s)
    return join(name, parts, origin=(x, y, z))


def chopsticks(name, at, rot, split=True, sauce=True):
    """나무젓가락: split pair with sauce-stained tips, or an unsplit pair still in its paper sleeve."""
    x, y, z = at
    parts = []
    if split:
        for k, (dy, da) in enumerate(((-0.006, 0.0), (0.008, 0.07))):
            st = boxes(f'tmp_cs{k}', [((-0.105, -0.003, 0), (0.105, 0.003, 0.005), 0)], [M['woodstick']], bevel=0.0008)
            st.data.transform(Matrix.Rotation(da, 4, 'Z')); st.data.transform(Matrix.Translation((0, dy, 0)))
            parts.append(st)
            if sauce:
                tip = boxes(f'tmp_ct{k}', [((-0.106, -0.0032, -0.0002), (-0.07, 0.0032, 0.0052), 0)], [M['sauce']], bevel=0.0008)
                tip.data.transform(Matrix.Rotation(da, 4, 'Z')); tip.data.transform(Matrix.Translation((0, dy, 0)))
                parts.append(tip)
    else:
        parts.append(boxes('tmp_csl', [((-0.12, -0.011, 0), (0.12, 0.011, 0.006), 0)], [M['paper']], bevel=0.001))
        parts.append(boxes('tmp_csb', [((-0.06, -0.0112, 0.0005), (0.0, 0.0112, 0.0062), 0)], [M['inkred']], bevel=0.0008))
    o = join(name, parts, origin=(0, 0, 0))
    o.data.transform(Matrix.Rotation(rot, 4, 'Z'))
    o.location = (x, y, z)
    return o


def soda_can(name, at, body_mat):
    """Generic 355 ml can: aluminium ends, printed body band."""
    x, y, z = at
    body = lathe('tmp_canb', [(0.033, 0.012), (0.033, 0.108)], [body_mat], 28, location=(x, y, z))
    ends = lathe('tmp_cane', [(0, 0.002), (0.024, 0.0), (0.029, 0.004), (0.033, 0.012), (0.033, 0.0121)], [M['alu']], 28, location=(x, y, z))
    top = lathe('tmp_cant', [(0.033, 0.108), (0.028, 0.118), (0.027, 0.122), (0.0265, 0.120), (0.0, 0.117)], [M['alu']], 28, location=(x, y, z))
    tab = boxes('tmp_cantab', [((x - 0.006, y - 0.012, z + 0.1185), (x + 0.006, y + 0.006, z + 0.1195))], M['alu'], bevel=0.001)
    stripe = lathe('tmp_cans', [(0.03305, 0.05), (0.03305, 0.058)], [M['pw']], 28, location=(x, y, z))
    return join(name, [body, ends, top, tab, stripe], origin=(x, y, z))


def delivery_bag_open(name, at, rot=0.0, font=None):
    """배달 비닐봉투 after it was opened: slumped open sack, rim folded, handles flopped, red '감사합니다' print."""
    rnd = random.Random(21)
    x, y, z = at
    rings = [(0.0, 0.115, 0.070, 0, 0), (0.015, 0.125, 0.077, 0, 0), (0.06, 0.12, 0.074, 0, 0), (0.085, 0.112, 0.068, 0, 0),
             (0.092, 0.122, 0.078, 0, 0), (0.088, 0.128, 0.083, 0, 0)]
    o = tzprops2.loft('tmp_bag', rings, [M['bagw']], steps=48, superness=2.4)
    bm = bmesh.new(); bm.from_mesh(o.data)
    for v in bm.verts:
        u = min(1.0, v.co.z / 0.09)
        ang = math.atan2(v.co.y, v.co.x)
        wr = 0.006 * math.sin(ang * 9 + v.co.z * 60) + 0.004 * math.sin(ang * 17 + 1.3)
        r = Vector((v.co.x, v.co.y, 0)).normalized()
        v.co += r * wr * u
        v.co.z -= 0.018 * u * (0.5 + 0.5 * math.sin(ang * 2 + 0.6))      # the rim sags unevenly
        v.co.x += 0.012 * u * u
    bm.to_mesh(o.data); bm.free()
    sm = o.modifiers.new('s', 'SOLIDIFY'); sm.thickness = 0.0012; bake(o)
    parts = [o]
    for s_ in (-1, 1):
        parts.append(tube(f'tmp_bh{s_}', [(s_ * 0.07, -0.06, 0.07), (s_ * 0.08, -0.10, 0.055), (s_ * 0.065, -0.125, 0.012),
                                           (s_ * 0.03, -0.12, 0.004), (s_ * 0.008, -0.088, 0.03), (s_ * 0.02, -0.068, 0.068)], 0.0045, M['bagw']))
    if font:
        parts.append(text_mesh('tmp_bagtxt', '감사합니다', 0.020, (0.0, -0.0775, 0.045), (math.radians(90), 0, 0), M['inkred'], font_path=font, extrude=0.0002))
    j = join(name, parts, origin=(0, 0, 0))
    j.data.transform(Matrix.Rotation(rot, 4, 'Z'))
    j.location = at
    shade_smooth_auto(j, 60)
    return j


# ----------------------------------------------------------------------------- cloth simulation helpers
def _cloth_bake(o, colliders, frames, mass=0.3, tension=15, bending=2.0, friction=20, distance=0.006, pins=None):
    for c in colliders:
        c.modifiers.new('col', 'COLLISION')
        c.collision.cloth_friction = 80.0
        c.collision.thickness_outer = 0.004
    if pins:
        vg = o.vertex_groups.new(name='pin')
        vg.add(pins, 1.0, 'REPLACE')
    cl = o.modifiers.new('cloth', 'CLOTH')
    st = cl.settings
    st.quality = 12; st.mass = mass; st.tension_stiffness = tension; st.compression_stiffness = tension
    st.shear_stiffness = tension * 0.4; st.bending_stiffness = bending; st.air_damping = 3
    if pins:
        st.vertex_group_mass = 'pin'
    cl.collision_settings.distance_min = distance
    cl.collision_settings.friction = friction
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, frames
    cl.point_cache.frame_start, cl.point_cache.frame_end = 1, frames
    for f in range(1, frames + 1):
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


_BVH = {}


def _surface_z(colliders, x, y, default):
    """Highest collider surface under (x, y) via BVH ray casts (cloth starts conforming instead of falling)."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    best = default
    for c in colliders:
        if c.name not in _BVH:
            _BVH[c.name] = BVHTree.FromObject(c, dg)
        inv = c.matrix_world.inverted()
        hit = _BVH[c.name].ray_cast(inv @ Vector((x, y, 5.0)), (inv.to_3x3() @ Vector((0, 0, -1))).normalized())
        if hit[0] is not None:
            best = max(best, (c.matrix_world @ hit[0]).z)
    return best


def _mask_grid(name, u_len, v_len, du, inside, place, material, smooth_boundary=4):
    """Grid over (u, v) keeping only cells whose centre is inside the silhouette; place(u, v) -> world xyz."""
    nu, nv = int(u_len / du), int(v_len / du)
    bm = bmesh.new()
    vid = {}
    def V(i, j):
        if (i, j) not in vid:
            vid[(i, j)] = bm.verts.new(place(i * du, j * du - v_len / 2))
        return vid[(i, j)]
    for i in range(nu):
        for j in range(nv):
            if inside((i + 0.5) * du, (j + 0.5) * du - v_len / 2):
                bm.faces.new((V(i, j), V(i + 1, j), V(i + 1, j + 1), V(i, j + 1)))
    for _ in range(smooth_boundary):                 # relax the stair-stepped silhouette along the outline
        new = {}
        for v in bm.verts:
            if not v.is_boundary:
                continue
            nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
            if len(nb) == 2:
                new[v] = v.co * 0.4 + (nb[0].co + nb[1].co) * 0.3
        for v, c in new.items():
            v.co = c
    return mesh_obj(name, bm, material, origin=(0, 0, 0), smooth=True)


def _seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy)))
    return math.hypot(px - ax - vx * t, py - ay - vy * t)


def glove_inside(u, v):
    """고무장갑 silhouette, u from cuff opening (0) to finger tips, v across (thumb at +v)."""
    if u < 0.135:
        return abs(v) < 0.056 - 0.006 * (u / 0.135)
    if u < 0.245:
        return abs(v) < 0.048
    for fv, L in ((-0.032, 0.062), (-0.011, 0.078), (0.011, 0.082), (0.032, 0.072)):
        if abs(v - fv) < 0.0085 and u < 0.245 + L:
            return True
    return _seg_dist(u, v, 0.165, 0.040, 0.225, 0.078) < 0.0115


def rubber_gloves_cloth(name, placements, z_top, material, colliders):
    """고무장갑 pair pulled off and left on the worktop: flat-ish hands with fingers, dropped in a cloth sim so they
    settle with soft creases. placements: [(cuff_x, cuff_y, heading_rad, flip)]."""
    objs = []
    for k, (cx, cy, hd, flip) in enumerate(placements):
        ca, sa = math.cos(hd), math.sin(hd)
        def place(u, v, cx=cx, cy=cy, ca=ca, sa=sa, flip=flip, k=k):
            vv = -v if flip else v
            px, py = cx + ca * u - sa * vv, cy + sa * u + ca * vv
            bump = 0.006 * math.sin(u * 40 + k) * math.sin(v * 50) + 0.004 * math.sin(u * 17)
            return (px, py, _surface_z(colliders, px, py, z_top) + 0.008 + abs(bump))
        objs.append(_mask_grid(f'tmp_glove{k}', 0.33, 0.13, 0.0045, glove_inside, place, material))
    g = join('tmp_gloves', objs, origin=(0, 0, 0))
    _cloth_bake(g, colliders, 40, mass=0.12, tension=12, bending=0.8, distance=0.003)
    sm = g.modifiers.new('s', 'SOLIDIFY'); sm.thickness = 0.006; sm.offset = 1
    ss = g.modifiers.new('sub', 'SUBSURF'); ss.levels = 1
    bake(g)
    g.name = name
    xs = [pl[0] for pl in placements]; ys = [pl[1] for pl in placements]
    set_origin(g, (sum(xs) / len(xs), sum(ys) / len(ys), z_top))
    shade_smooth_auto(g, 80)
    return g


def hoodie_inside(u, v):
    """Flat hoodie: hood (u<0.24), body to the hem, sleeves out from the shoulders drooping slightly."""
    if u < 0.24:
        return (u - 0.13) ** 2 / 0.13 ** 2 + v ** 2 / 0.14 ** 2 < 1.0
    if u < 0.86 and abs(v) < 0.27:
        return True
    if 0.27 <= abs(v) < 0.78:
        lo = 0.27 + (abs(v) - 0.27) * 0.15
        return lo < u < lo + 0.15
    return False


def hoodie_on_bed(name, at, material, colliders):
    """Hoodie thrown over the side of the bed: hood and shoulders on the mattress, hem and a sleeve slide to the floor."""
    x, y, z = at   # x = bed side edge, z = mattress top
    def place(u, v):
        lift = 0.0
        if abs(v) > 0.27:                                # sleeves folded back across the body (tossed, not laid out)
            v = math.copysign(0.27 - (abs(v) - 0.27) * 0.8, v)
            u += 0.04
            lift = 0.022
        px, py = x + 0.55 - u, y + v * 0.95
        return (px, py, _surface_z(colliders, px, py, 0.0) + 0.012 + lift + 0.008 * math.sin(v * 11) * math.sin(u * 7))
    o = _mask_grid('tmp_hoodie', 0.86, 1.62, 0.012, hoodie_inside, place, material)
    pins = [v.index for v in o.data.vertices if v.co.x > x + 0.55 - 0.10]
    _cloth_bake(o, colliders, 70, mass=0.4, tension=18, bending=3.0, distance=0.006, friction=60, pins=pins)
    sm = o.modifiers.new('s', 'SOLIDIFY'); sm.thickness = 0.012; sm.offset = 1
    ss = o.modifiers.new('sub', 'SUBSURF'); ss.levels = 1
    bake(o)
    o.name = name
    set_origin(o, (x, y, 0.0))
    shade_smooth_auto(o, 80)
    return o


def towel_on_bar(name, bar_a, bar_b, length, material):
    """Face towel folded over the towel bar (pinned along the fold, both halves hang)."""
    (ax, ay, az), (bx, by, bz) = bar_a, bar_b
    w = math.dist(bar_a, bar_b) * 0.8
    cx, cy = (ax + bx) / 2, (ay + by) / 2
    bm = bmesh.new()
    nu, nv = 14, 30
    grid = []
    for j in range(nv + 1):
        row = []
        for i in range(nu + 1):
            s = (j / nv - 0.5) * length            # signed distance along the towel from the fold
            px = cx + (i / nu - 0.5) * w
            if abs(s) < 0.02:
                pz, py = az + 0.013, cy + s * 0.8
            else:
                pz = az + 0.013 - (abs(s) - 0.02)
                py = cy - math.copysign(0.016, s)
            py += 0.006 * math.sin(i * 1.1 + j * 0.3) * min(1.0, abs(s) * 4)
            row.append(bm.verts.new((px, py, pz)))
        grid.append(row)
    for j in range(nv):
        for i in range(nu):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    o = mesh_obj('tmp_towel', bm, material, origin=(0, 0, 0), smooth=True)
    mid = nv // 2
    pins = [mid * (nu + 1) + i for i in range(nu + 1)]
    bar = tube('tmp_towelbar', [bar_a, bar_b], 0.012, None)
    wall = box('tmp_towelwall', (ax - 0.3, by + 0.026, az - 0.8), (bx + 0.3, by + 0.08, az + 0.3), None, bevel=0.0)
    _cloth_bake(o, [bar, wall], 50, mass=0.3, tension=15, bending=1.5, pins=pins)
    for t in (bar, wall):
        bpy.data.objects.remove(t, do_unlink=True)
    sm = o.modifiers.new('s', 'SOLIDIFY'); sm.thickness = 0.006; sm.offset = 0
    bake(o)
    o.name = name
    set_origin(o, (cx, cy, az))
    shade_smooth_auto(o, 80)
    return o


# ----------------------------------------------------------------------------- small clutter
def crumpled_tissues(name, spots, material):
    rnd = random.Random(33)
    parts = []
    for i, (x, y, z, r) in enumerate(spots):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
        for v in bm.verts:
            n = v.co.normalized()
            v.co += n * rnd.uniform(-0.35, 0.25) * r
            v.co.z *= 0.65
        bmesh.ops.translate(bm, verts=bm.verts, vec=(x, y, z + r * 0.55))
        parts.append(mesh_obj(f'tmp_tis{i}', bm, material, origin=(x, y, z)))
    o = join(name, parts, origin=spots[0][:3])
    return o


# ----------------------------------------------------------------------------- evidence marker kit
def evidence_markers(font, count=12, at=(-6.0, -6.0, 0.0)):
    """Yellow A-frame evidence tents numbered 1..count (kit_marker_NN). Parked outside the playable area;
    the game clones one beside each object the detective photographs."""
    yel = M['marker_yellow']
    out = []
    for n in range(1, count + 1):
        bx, by, bz = at[0] + n * 0.2, at[1], at[2]
        parts = []
        t22 = math.radians(22)
        for s in (-1, 1):
            # A-frame: each leaf leans in so the two tops meet over the centre line
            p = box(f'tmp_mk{n}{s}', (-0.045, -0.0018, 0.0), (0.045, 0.0018, 0.115), yel, bevel=0.0012)
            p.data.transform(Matrix.Rotation(s * t22, 4, 'X'))
            p.data.transform(Matrix.Translation((0, s * math.sin(t22) * 0.115, 0)))
            parts.append(p)
            txt = text_mesh(f'tmp_mkt{n}{s}', str(n), 0.082, (0, 0, 0), (math.radians(90), 0, 0 if s < 0 else math.pi), M['ink'],
                            font_path=font, extrude=0.0006, bold=0.0013)
            txt.data.transform(Matrix.Rotation(s * t22, 4, 'X'))
            h = 0.058
            yy = s * (math.sin(t22) * 0.115 - math.sin(t22) * h) + s * math.cos(t22) * 0.0026
            txt.data.transform(Matrix.Translation((0, yy, math.cos(t22) * h + math.sin(t22) * 0.0022)))
            parts.append(txt)
        o = join(f'kit_marker_{n:02d}', parts, origin=(0, 0, 0))
        o.location = (bx, by, bz)
        out.append(o)
    return out


# ----------------------------------------------------------------------------- v5: labels, bath clutter
def wrap_on_cylinder(obj, cx, cy, r, facing='+x'):
    """Bend a flat label/text mesh (built tangent to the cylinder) onto its surface so no edge floats."""
    mw = obj.matrix_world.copy(); inv = mw.inverted()
    for v in obj.data.vertices:
        w = mw @ v.co
        if facing in ('+x', '-x'):
            sgn = 1 if facing == '+x' else -1
            t, d = w.y - cy, (w.x - cx) * sgn - r          # tangent offset, height above the tangent plane
            a = t / r
            w.x, w.y = cx + sgn * (r + d) * math.cos(a), cy + (r + d) * math.sin(a)
        else:
            sgn = 1 if facing == '+y' else -1
            t, d = w.x - cx, (w.y - cy) * sgn - r
            a = t / r
            w.y, w.x = cy + sgn * (r + d) * math.cos(a), cx + (r + d) * math.sin(a)
        v.co = inv @ w
    return obj


def bottle_label(tag, cx, cy, z0, z1, r, band_mat, text, text_mat, font, size, facing='+x'):
    """Printed wrap label: a band ring around the bottle + the product word bent onto it."""
    band = lathe(f'tmp_lb{tag}', [(r + 0.0008, z0), (r + 0.0008, z1)], [band_mat], 28, location=(cx, cy, 0))
    rot = (math.radians(90), 0, math.radians(90)) if facing == '+x' else (math.radians(90), 0, math.radians(180))
    zc = (z0 + z1) / 2
    loc = (cx + r + 0.0014, cy, zc) if facing == '+x' else (cx, cy + r + 0.0014, zc)
    txt = label_text(f'tmp_lt{tag}', text, size, loc, rot, text_mat, font)
    bpy.context.view_layer.update()
    wrap_on_cylinder(txt, cx, cy, r, facing)
    return [band, txt]


def label_text(name, text, size, loc, rot, m, font):
    return text_mesh(name, text, size, loc, rot, m, font_path=font, extrude=0.0003, bold=size * 0.022)


def bath_stool(name, at, material):
    """목욕의자: low square-ish plastic stool with a flared skirt and a hand hole in the seat."""
    x, y, z = at
    o = tzprops2.loft('tmp_stool', [(0.0, 0.16, 0.15, 0, 0), (0.02, 0.155, 0.145, 0, 0), (0.21, 0.135, 0.125, 0, 0),
                                     (0.235, 0.145, 0.135, 0, 0), (0.25, 0.14, 0.13, 0, 0)], [material], steps=40,
                       cap_bottom=False, cap_top=True, superness=3.5, location=(x, y, z))
    sm = o.modifiers.new('s', 'SOLIDIFY'); sm.thickness = 0.004; bake(o)
    hole = box('tmp_stoolhole', (x - 0.04, y - 0.012, z + 0.2), (x + 0.04, y + 0.012, z + 0.3), None, bevel=0.01, seg=3)
    boolean_cut(o, hole)
    o.name = name
    return o


def wash_basin(name, at, material):
    """대야: wide shallow plastic basin, rim lip."""
    x, y, z = at
    return lathe(name, [(0, 0.0), (0.15, 0.0), (0.2, 0.11), (0.215, 0.115), (0.212, 0.12), (0.195, 0.115), (0.145, 0.006), (0, 0.006)],
                 [material], 48, location=(x, y, z))


def drain_hair(name, at, material):
    """Long hairs tangled on the drain cover (thin curved tubes)."""
    rnd = random.Random(13)
    x, y, z = at
    parts = []
    for i in range(7):
        a0 = rnd.uniform(0, 6.28); pts = []
        rr = rnd.uniform(0.02, 0.05)
        for k in range(7):
            a = a0 + k * rnd.uniform(0.6, 1.1)
            pts.append((x + math.cos(a) * rr * (1 + 0.3 * k / 6), y + math.sin(a) * rr * (1 + 0.3 * k / 6), z + 0.0035 + 0.0012 * (k % 2)))
        parts.append(tube(f'tmp_hair{i}', pts, 0.0011, material, res=4))
    return join(name, parts, origin=at)
