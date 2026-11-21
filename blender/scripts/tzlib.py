"""TABLE//ZERO Blender modeling helpers (Blender 4.5, run headless).

All dimensions in meters, Blender Z-up. Every object gets world-scale UVs (1 UV unit = 1 m)
so Unity materials tile at real-world density. Bevels are real geometry, not normal tricks.
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for c in (bpy.data.meshes, bpy.data.materials, bpy.data.objects, bpy.data.curves):
        for x in list(c):
            c.remove(x)

_COLL = {}
def coll(name):
    if name not in _COLL:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        _COLL[name] = c
    return _COLL[name]

def mat(name, color=(0.8, 0.8, 0.8, 1), rough=0.6, metal=0.0):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes.get('Principled BSDF')
        b.inputs['Base Color'].default_value = color
        b.inputs['Roughness'].default_value = rough
        b.inputs['Metallic'].default_value = metal
        m.diffuse_color = color
    return m

def uv_world(bm, scale=1.0, offset=(0, 0, 0)):
    """Box-projected UVs in meters using face normal dominant axis."""
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            co = l.vert.co + Vector(offset)
            if ax == 0:
                u, v = (co.y if n.x > 0 else -co.y), co.z
            elif ax == 1:
                u, v = (-co.x if n.y > 0 else co.x), co.z
            else:
                u, v = co.x, (co.y if n.z > 0 else -co.y)
            l[uv].uv = (u * scale, v * scale)

def mesh_obj(name, bm, material=None, collection='Room302', origin=(0, 0, 0), uv=True, uv_scale=1.0, smooth=False):
    """Create object from bmesh. bm coords are WORLD; object origin placed at `origin`."""
    if uv:
        uv_world(bm, uv_scale)
    o = Vector(origin)
    for v in bm.verts:
        v.co -= o
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    obj = bpy.data.objects.new(name, me)
    obj.location = o
    coll(collection).objects.link(obj)
    if material is not None:
        mats = material if isinstance(material, (list, tuple)) else [material]
        for m in mats:
            me.materials.append(m)
    return obj

def _box_bm(bm, mn, mx):
    mn, mx = Vector(mn), Vector(mx)
    r = bmesh.ops.create_cube(bm, size=1.0)
    verts = r['verts']
    c = (mn + mx) / 2
    s = mx - mn
    for v in verts:
        v.co = Vector((c.x + v.co.x * s.x, c.y + v.co.y * s.y, c.z + v.co.z * s.z))
    return verts

def box(name, mn, mx, material=None, bevel=0.004, seg=2, collection='Room302', origin=None, mat_index=0):
    bm = bmesh.new()
    verts = _box_bm(bm, mn, mx)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=seg, affect='EDGES', profile=0.5)
    bm.normal_update()
    if origin is None:
        origin = ((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2])
    return mesh_obj(name, bm, material, collection, origin)

def boxes(name, parts, material=None, collection='Room302', origin=(0, 0, 0), bevel=0.003, seg=1):
    """Several boxes merged into one object: parts = [(mn, mx, mat_index), ...]."""
    bm = bmesh.new()
    for p in parts:
        mn, mx = p[0], p[1]
        mi = p[2] if len(p) > 2 else 0
        vs = _box_bm(bm, mn, mx)
        faces = list({f for v in vs for f in v.link_faces})
        for f in faces:
            f.material_index = mi
        if bevel > 0:
            edges = list({e for v in vs for e in v.link_edges})
            bmesh.ops.bevel(bm, geom=edges, offset=min(bevel, min(abs(mx[i] - mn[i]) for i in range(3)) * 0.3),
                            segments=seg, affect='EDGES', profile=0.5)
    bm.normal_update()
    return mesh_obj(name, bm, material, collection, origin)

def bake(obj):
    """Apply all modifiers by evaluating the depsgraph (works headless)."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    old = obj.data
    obj.modifiers.clear()
    obj.data = me
    bpy.data.meshes.remove(old)
    return obj

def bm_from(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    return bm

def rewrap_uv(obj, scale=1.0):
    bpy.context.view_layer.update()
    bm = bm_from(obj)
    bm.transform(obj.matrix_world)
    uv_world(bm, scale)
    bm.transform(obj.matrix_world.inverted())
    bm.to_mesh(obj.data)
    bm.free()

def boolean_cut(target, cutter, solver='EXACT'):
    m = target.modifiers.new('cut', 'BOOLEAN')
    m.operation = 'DIFFERENCE'
    m.object = cutter
    m.solver = solver
    bake(target)
    bpy.data.objects.remove(cutter, do_unlink=True)
    return target

def lathe(name, profile, material=None, steps=48, collection='Room302', location=(0, 0, 0), smooth=True, uv_scale=1.0):
    """Revolve a 2D profile [(r,z),...] around local Z."""
    bm = bmesh.new()
    rings = []
    for i in range(steps):
        a = 2 * math.pi * i / steps
        ring = [bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for r, z in profile]
        rings.append(ring)
    for i in range(steps):
        a, b = rings[i], rings[(i + 1) % steps]
        for j in range(len(profile) - 1):
            if profile[j][0] == 0 and profile[j + 1][0] == 0:
                continue
            try:
                bm.faces.new((a[j], b[j], b[j + 1], a[j + 1]))
            except ValueError:
                pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # cylindrical UV: u = angle * radius-ish, v = z
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for l in f.loops:
            co = l.vert.co
            ang = math.atan2(co.y, co.x)
            l[uv].uv = ((ang / (2 * math.pi) + 0.5) * uv_scale, co.z * uv_scale * 4)
    for v in bm.verts:
        v.co += Vector(location)
    obj = mesh_obj(name, bm, material, collection, origin=location, uv=False, smooth=smooth)
    return obj

def tube(name, points, radius, material=None, collection='Room302', res=10, origin=None):
    """Bezier tube through points (world). Converted to mesh."""
    cu = bpy.data.curves.new(name + '_c', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = radius
    cu.bevel_resolution = max(2, res // 4)
    cu.use_fill_caps = True
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
    o = bpy.data.objects.new(name, cu)
    coll(collection).objects.link(o)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.curves.remove(cu)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    for f in bm.faces:
        f.smooth = True
    return mesh_obj(name, bm, material, collection, origin or points[0], smooth=True)

def join(name, objs, origin=None, collection='Room302'):
    """Merge objects into one (keeps materials)."""
    bpy.context.view_layer.update()
    bm = bmesh.new()
    mats = []
    for o in objs:
        tmp = bmesh.new()
        tmp.from_mesh(o.data)
        tmp.transform(o.matrix_world)
        remap = {}
        for i, m in enumerate(o.data.materials):
            if m not in mats:
                mats.append(m)
            remap[i] = mats.index(m)
        for f in tmp.faces:
            f.material_index = remap.get(f.material_index, 0)
        me = bpy.data.meshes.new('tmp')
        tmp.to_mesh(me)
        tmp.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    origin = origin or (0, 0, 0)
    for v in bm.verts:
        v.co -= Vector(origin)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    obj = bpy.data.objects.new(name, me)
    obj.location = origin
    coll(collection).objects.link(obj)
    return obj

def set_origin(obj, world_point):
    """Move pivot to a world point (objects here carry translation only)."""
    wp = Vector(world_point)
    local = wp - obj.location
    obj.data.transform(Matrix.Translation(-local))
    obj.location = wp

def parent(child, par):
    bpy.context.view_layer.update()
    mw = child.matrix_world.copy()
    child.parent = par
    child.matrix_world = mw

def shade_smooth_auto(obj, angle=35):
    for p in obj.data.polygons:
        p.use_smooth = True
    try:
        obj.data.set_sharp_from_angle(angle=math.radians(angle))
    except Exception:
        pass

_FONT = {}
def text_mesh(name, text, size, location, rotation=(0, 0, 0), material=None, font_path=None, extrude=0.0004,
              collection='Room302', align='CENTER', bold=0.0):
    """Real Korean text as thin geometry (labels, receipts, markers). Font must be OFL (Noto)."""
    if font_path and font_path not in _FONT:
        _FONT[font_path] = bpy.data.fonts.load(font_path)
    cu = bpy.data.curves.new(name + '_t', 'FONT')
    cu.body = text
    cu.size = size
    cu.extrude = extrude
    cu.offset = bold            # fattens glyph outlines (Noto variable font has no bold face loaded)
    cu.align_x = align
    cu.align_y = 'CENTER'
    if font_path:
        cu.font = _FONT[font_path]
    o = bpy.data.objects.new(name, cu)
    o.location = location
    o.rotation_euler = rotation
    coll(collection).objects.link(o)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    mw = o.matrix_world.copy()
    bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.curves.remove(cu)
    bm = bmesh.new(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    bm.transform(mw)
    return mesh_obj(name, bm, material, collection, origin=location)

def export_fbx(path, collection=None):
    for o in bpy.data.objects:
        o.select_set(False)
    objs = [o for o in bpy.data.objects if collection is None or collection in [c.name for c in o.users_collection]]
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
                             axis_forward='-Z', axis_up='Y', bake_space_transform=True, object_types={'MESH', 'EMPTY'},
                             use_mesh_modifiers=True, mesh_smooth_type='FACE', use_tspace=True, add_leaf_bones=False,
                             path_mode='STRIP')
