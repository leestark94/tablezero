"""이서연 extras added on top of the MPFB build (called from build_seoyeon.py):

- add_fringe(): curtain bangs + face-framing side strands as alpha hair cards. Each strand follows the real
  face/scalp surface (ray cast from the front) a little in front of it, so in the 3D room the forehead and eyes sit
  behind hair and in its shadow (face rule: no black overlay). 100 % weighted to the head bone.
- add_watch(): metal bracelet watch on the left wrist (approved reference), 100 % weighted to the left forearm.
Blender axes: front = -Y, up = +Z. Units: metres.
"""
import math, random
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _bvh(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    for o in objs:
        tmp = bmesh.new(); tmp.from_object(o, dg); tmp.transform(o.matrix_world)
        me = bpy.data.meshes.new('_tmp'); tmp.to_mesh(me); tmp.free()
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    tree = BVHTree.FromBMesh(bm); bm.free()
    return tree


def _front_y(tree, x, z):
    hit = tree.ray_cast(Vector((x, -0.6, z)), Vector((0, 1, 0)))
    return hit[0].y if hit[0] is not None else None


def _skin_to(obj, rig, bone):
    obj.parent = rig
    vg = obj.vertex_groups.new(name=bone)
    vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
    m = obj.modifiers.new('Armature', 'ARMATURE'); m.object = rig


def add_fringe(body, hair, rig, tex_path, seed=29):
    rnd = random.Random(seed)
    tree = _bvh([body, hair])
    verts, faces, uvs = [], [], []

    def strand(x0, z0, x1, z1, bow, off0, off1, width, segs=14):
        pts = []
        for i in range(segs + 1):
            t = i / segs
            x = x0 + (x1 - x0) * (t ** 1.25) + bow * math.sin(math.pi * t)
            z = z0 + (z1 - z0) * t
            fy = _front_y(tree, x, z)
            if fy is None:
                fy = pts[-1].y + 0.004 if pts else -0.10
            pts.append(Vector((x, fy - (off0 + (off1 - off0) * t ** 1.4), z)))
        u0 = rnd.uniform(0.0, 0.6); u1 = u0 + rnd.uniform(0.25, 0.4)
        base = len(verts)
        for i, p in enumerate(pts):
            tan = (pts[min(i + 1, segs)] - pts[max(i - 1, 0)]).normalized()
            side = tan.cross(Vector((0, -1, 0))).normalized()
            w = width * (1.0 - 0.45 * (i / segs))             # strands thin out toward the tips
            verts.extend([p - side * w * 0.5, p + side * w * 0.5])
            uvs.extend([(u0, 1 - i / segs), (u1, 1 - i / segs)])
        for i in range(segs):
            a = base + i * 2
            faces.append((a, a + 1, a + 3, a + 2))

    # curtain bangs from a centre part: strands fall across the forehead and over the eyes, ending at the cheekbone
    for side in (-1, 1):
        for k in range(16):
            x0 = side * rnd.uniform(0.002, 0.03)
            x1 = side * (0.012 + k * 0.0042 + rnd.uniform(-0.004, 0.004))
            z1 = rnd.uniform(1.300, 1.335)
            strand(x0, 1.452, x1, z1, side * rnd.uniform(0.0, 0.01), 0.003, rnd.uniform(0.012, 0.022), rnd.uniform(0.012, 0.02))
    # face-framing side strands: temple -> jaw/shoulder, a little in front of the cheeks
    for side in (-1, 1):
        for k in range(12):
            x0 = side * rnd.uniform(0.035, 0.065)
            x1 = side * rnd.uniform(0.058, 0.09)
            z1 = rnd.uniform(1.17, 1.26)
            strand(x0, 1.44, x1, z1, side * rnd.uniform(-0.006, 0.008), 0.004, rnd.uniform(0.010, 0.02), rnd.uniform(0.014, 0.024), segs=18)

    me = bpy.data.meshes.new('Seoyeon_Hair_Fringe')
    me.from_pydata([tuple(v) for v in verts], [], faces)
    uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    mat = bpy.data.materials.new('Seoyeon_Fringe'); mat.use_nodes = True
    img = bpy.data.images.load(tex_path); bsdf = mat.node_tree.nodes['Principled BSDF']
    tn = mat.node_tree.nodes.new('ShaderNodeTexImage'); tn.image = img
    mat.node_tree.links.new(tn.outputs['Color'], bsdf.inputs['Base Color'])
    mat.node_tree.links.new(tn.outputs['Alpha'], bsdf.inputs['Alpha'])
    me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    obj = bpy.data.objects.new('Seoyeon_Hair_Fringe', me); bpy.context.scene.collection.objects.link(obj)
    _skin_to(obj, rig, 'mixamorig:Head')
    print('FRINGE strands', len(faces) // 14, 'verts', len(verts))
    return obj


def add_watch(body, rig):
    hand = rig.matrix_world @ rig.data.bones['mixamorig:LeftHand'].head_local
    elbow = rig.matrix_world @ rig.data.bones['mixamorig:LeftForeArm'].head_local
    axis = (hand - elbow).normalized()
    c = hand - axis * 0.038
    # wrist cross-section radius from the body mesh (verts within 1 cm of the plane through c)
    mw = body.matrix_world; rad = []
    for v in body.data.vertices:
        p = mw @ v.co; d = p - c
        if abs(d.dot(axis)) < 0.01:
            r = (d - axis * d.dot(axis)).length
            if r < 0.06: rad.append(r)
    r = (max(rad) if rad else 0.028) + 0.003
    up = Vector((0, 0, 1)); up = (up - axis * up.dot(axis)).normalized()   # back of the wrist (palm faces down)
    side = axis.cross(up).normalized()
    bm = bmesh.new()
    # bracelet: flattened ring, 18 mm wide, 2.5 mm thick (slightly oval like a wrist)
    n = 40; ring = []
    for i in range(n):
        a = 2 * math.pi * i / n
        d = up * math.cos(a) * r * 0.88 + side * math.sin(a) * r * 1.08
        dn = d.normalized()
        ring.append([bm.verts.new(c + d + axis * s * 0.009 + dn * t) for s, t in ((-1, 0), (1, 0), (1, 0.0025), (-1, 0.0025))])
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        for k in range(4):
            bm.faces.new((a[k], b[k], b[(k + 1) % 4], a[(k + 1) % 4]))
    # case + bezel + glass on the back of the wrist
    top = c + up * (r * 0.88 + 0.0025)
    seg = 32; cr = 0.017; h = 0.008
    bot_ring = [bm.verts.new(top + (side * math.cos(2 * math.pi * i / seg) + axis * math.sin(2 * math.pi * i / seg)) * cr) for i in range(seg)]
    top_ring = [bm.verts.new(v.co + up * h) for v in bot_ring]
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((bot_ring[i], bot_ring[j], top_ring[j], top_ring[i]))
    bm.faces.new(list(reversed(bot_ring)))
    glass_c = bm.verts.new(top + up * (h + 0.001))
    case_faces = len(bm.faces)
    for i in range(seg):
        bm.faces.new((top_ring[i], top_ring[(i + 1) % seg], glass_c))
    me = bpy.data.meshes.new('Seoyeon_Watch'); bm.to_mesh(me); bm.free()
    steel = bpy.data.materials.new('Seoyeon_WatchSteel'); dial = bpy.data.materials.new('Seoyeon_WatchDial')
    me.materials.append(steel); me.materials.append(dial)
    for i, p in enumerate(me.polygons):
        p.material_index = 1 if i >= case_faces else 0
        p.use_smooth = True
    obj = bpy.data.objects.new('Seoyeon_Watch', me); bpy.context.scene.collection.objects.link(obj)
    _skin_to(obj, rig, 'mixamorig:LeftForeArm')
    print('WATCH wrist_r', round(r, 4), 'at', tuple(round(x, 3) for x in c))
    return obj


def add_sleeves(body, rig, suit, start_z=1.06, cuff_gap=0.02, margin=0.0055, segs=28):
    """Long knit sleeves as a clean tube per arm (own UVs): from inside the pack's short sleeve (upper arm) down the forearm
    to just above the wrist. Radius at every ring = the real arm cross-section of the body mesh + margin, so the knit sits on
    the arm instead of floating. Weighted to upper-arm / forearm bones (blended at the elbow) so it bends with the arm."""
    mw = body.matrix_world; knit = bpy.data.materials.get('Seoyeon_Knit')
    gi = {g.name: g.index for g in body.vertex_groups}
    def arm_verts(pre):
        ids = {gi[n] for n in (f'mixamorig:{pre}Arm', f'mixamorig:{pre}ForeArm') if n in gi}
        return [mw @ v.co for v in body.data.vertices if any(g.group in ids and g.weight > 0.6 for g in v.groups)]
    arm_cache = {pre: arm_verts(pre) for pre in ('Left', 'Right')}
    out = []
    for side, pre in ((1, 'Left'), (-1, 'Right')):
        sh = rig.matrix_world @ rig.data.bones[f'mixamorig:{pre}Arm'].head_local
        el = rig.matrix_world @ rig.data.bones[f'mixamorig:{pre}ForeArm'].head_local
        wr = rig.matrix_world @ rig.data.bones[f'mixamorig:{pre}Hand'].head_local
        wr_end = wr - (wr - el).normalized() * cuff_gap
        # start point on the shoulder->elbow line where z == start_z
        t0 = max(0.0, min(1.0, (sh.z - start_z) / max(1e-4, (sh.z - el.z))))
        a = sh.lerp(el, t0)
        path = []; n_up = 5; n_fore = 9
        for i in range(n_up + 1): path.append(a.lerp(el, i / n_up))
        for i in range(1, n_fore + 1): path.append(el.lerp(wr_end, i / n_fore))
        bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); deform = bm.verts.layers.deform.verify()
        g_up = body.parent and None
        rings = []; length = 0.0; dist = [0.0]
        for i in range(1, len(path)): dist.append(dist[-1] + (path[i] - path[i - 1]).length)
        ref = Vector((0, -1, 0)) if abs((path[-1] - path[0]).normalized().y) < 0.9 else Vector((1, 0, 0))
        for i, c in enumerate(path):
            tan = ((path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)])).normalized()
            e1 = (ref - tan * ref.dot(tan)).normalized(); e2 = tan.cross(e1).normalized()
            # arm radius here: farthest body vertex within a thin slab around the plane, restricted to this arm
            rad = 0.0
            for p in arm_cache[pre]:
                d = p - c
                if abs(d.dot(tan)) < 0.012:
                    r = (d - tan * d.dot(tan)).length
                    if r < 0.07: rad = max(rad, r)
            rad = (rad if rad > 0 else 0.03) + margin
            ring = []
            for k in range(segs):
                ang = 2 * math.pi * k / segs
                v = bm.verts.new(c + (e1 * math.cos(ang) + e2 * math.sin(ang)) * rad)
                ring.append(v)
            rings.append(ring)
        for i in range(len(rings) - 1):
            for k in range(segs):
                k2 = (k + 1) % segs
                f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
                f.smooth = True
                for loop, (ring_i, kk) in zip(f.loops, ((i, k), (i, k2), (i + 1, k2), (i + 1, k))):
                    u = (kk if kk != 0 or loop is f.loops[0] or loop is f.loops[3] else segs) / segs
                    if kk == 0 and loop is f.loops[1]: u = 1.0
                    if kk == 0 and loop is f.loops[2]: u = 1.0
                    loop[uvl].uv = (u * 1.6, dist[ring_i] / 0.24)
        # blend weights: rings before the elbow -> upper arm, after -> forearm, 2 rings around the elbow mixed
        names = (f'mixamorig:{pre}Arm', f'mixamorig:{pre}ForeArm')
        me = bpy.data.meshes.new(f'Seoyeon_Sleeve_{pre}'); bm.to_mesh(me)
        obj = bpy.data.objects.new(f'Seoyeon_Sleeve_{pre}', me); bpy.context.scene.collection.objects.link(obj)
        obj.parent = rig
        ga = obj.vertex_groups.new(name=names[0]); gf = obj.vertex_groups.new(name=names[1])
        for ri, ring in enumerate(rings):
            w_f = 0.0 if ri < n_up - 1 else (0.5 if ri in (n_up - 1, n_up, n_up + 1) else 1.0)
            idx = [ri * segs + k for k in range(segs)]
            if w_f < 1: ga.add(idx, 1.0 - w_f, 'REPLACE')
            if w_f > 0: gf.add(idx, w_f, 'REPLACE')
        bm.free()
        me.materials.append(knit)
        for p in me.polygons: p.use_smooth = True
        m = obj.modifiers.new('Armature', 'ARMATURE'); m.object = rig
        out.append(obj)
    print('SLEEVES', [(o.name, len(o.data.vertices)) for o in out])
    return out


def add_hair_cap(body, rig, offset=0.005):
    """Dark matte dome over the crown/back of the scalp: the pack's hair shell leaves the top of the head showing skin."""
    mw = body.matrix_world
    bm = bmesh.new(); bm.from_mesh(body.data)
    keep = []
    for f in bm.faces:
        c = mw @ f.calc_center_median()
        if c.z > 1.40 and (c.y > -0.085 or c.z > 1.43):
            keep.append(f)
    # also drop faces of the face/forehead (front) from the cap's lower rim
    geom = set(keep)
    for f in list(bm.faces):
        if f not in geom: bm.faces.remove(f)
    for v in list(bm.verts):
        if not v.link_faces: bm.verts.remove(v)
    for v in bm.verts:
        v.co = body.matrix_world.inverted() @ ((mw @ v.co) + (mw.to_3x3() @ v.normal).normalized() * offset)
    for k in list(bm.verts.layers.deform.keys()) if hasattr(bm.verts.layers.deform, 'keys') else []:
        pass
    deform = bm.verts.layers.deform.verify()
    me = bpy.data.meshes.new('Seoyeon_HairCap'); bm.to_mesh(me); bm.free()
    mat = bpy.data.materials.new('Seoyeon_HairCap'); mat.use_nodes = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.04, 0.03, 0.026, 1)
    me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    obj = bpy.data.objects.new('Seoyeon_HairCap', me); bpy.context.scene.collection.objects.link(obj)
    _skin_to(obj, rig, 'mixamorig:Head')
    print('HAIRCAP faces', len(me.polygons))
    return obj
