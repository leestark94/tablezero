"""Import GLBs, report mesh stats, render 3 views each (Eevee, neutral studio light). blender -b -P inspect_glb.py -- out_dir a.glb b.glb"""
import bpy, sys, os, math
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
out, files = args[0], args[1:]
os.makedirs(out, exist_ok=True)
for f in files:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=f)
    meshes = [o for o in sc.objects if o.type == 'MESH']
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    size = mx - mn; ctr = (mn + mx) / 2
    mats = {m.name for o in meshes for m in o.data.materials if m}
    imgs = [(i.name, i.size[0], i.size[1]) for i in bpy.data.images]
    print('STATS', os.path.basename(f), 'meshes', len(meshes), 'tris', tris, 'size', tuple(round(v, 3) for v in size), 'mats', mats, 'imgs', imgs)
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 900, 900
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.35, 0.35, 0.37, 1)
    for i, (rx, rz, e) in enumerate([(50, 30, 900), (60, 200, 500), (20, 110, 300)]):
        L = bpy.data.lights.new(f'l{i}', 'AREA'); L.energy = e; L.size = 2
        lo = bpy.data.objects.new(f'l{i}', L); sc.collection.objects.link(lo)
        lo.location = ctr + Vector((math.cos(math.radians(rz)), math.sin(math.radians(rz)), 1)) * max(size) * 3
        lo.rotation_euler = (ctr - lo.location).to_track_quat('-Z', 'Y').to_euler()
    cd = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
    r = max(size) * 1.9
    for name, (az, el) in {'front': (-90, 10), 'side': (0, 15), 'three4': (-45, 30)}.items():
        cam.location = ctr + Vector((math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el)))) * r
        cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, os.path.splitext(os.path.basename(f))[0] + f'_{name}.png')
        bpy.ops.render.render(write_still=True)
