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
