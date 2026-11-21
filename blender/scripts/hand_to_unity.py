"""Tripo hand GLB -> game view model: decimate to ~40k tris, export FBX + texture PNGs.
blender -b -P hand_to_unity.py -- in.glb out_dir"""
import bpy, sys, os
args = sys.argv[sys.argv.index('--') + 1:]
src, out = args[0], args[1]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
mesh = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
tris = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
for o in bpy.context.scene.objects:
    o.select_set(o == mesh)
bpy.context.view_layer.objects.active = mesh
mesh.parent = None
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
d = mesh.modifiers.new('dec', 'DECIMATE'); d.ratio = 40000 / tris; d.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier='dec')
mesh.name = 'fp_hand_right'
for p in mesh.data.polygons: p.use_smooth = True
for img in bpy.data.images:
    kind = 'color' if img.name.startswith('Color') else 'normal' if img.name.startswith('Normal') else 'orm' if img.name.startswith('ORM') else None
    if kind:
        img.filepath_raw = os.path.join(out, f'fp_hand_{kind}_src.png'); img.file_format = 'PNG'; img.save()
for o in list(bpy.context.scene.objects):
    if o != mesh: bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.export_scene.fbx(filepath=os.path.join(out, 'fp_hand_right.fbx'), use_selection=True, apply_scale_options='FBX_SCALE_UNITS',
                         axis_forward='-Z', axis_up='Y', bake_space_transform=True, path_mode='STRIP', embed_textures=False,
                         mesh_smooth_type='FACE')
print('HAND tris', tris, '->', sum(len(p.vertices) - 2 for p in mesh.data.polygons), 'dims', tuple(round(v, 3) for v in mesh.dimensions))
