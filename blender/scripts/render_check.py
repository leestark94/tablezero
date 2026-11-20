"""Geometry check renders (Workbench, CPU-safe). blender -b file.blend -P render_check.py -- outdir"""
import bpy, sys, os, math
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.show_cavity = True
sc.display.shading.show_shadows = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
cam_data = bpy.data.cameras.new('cam'); cam_data.lens = 18
cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam); sc.camera = cam
views = {
    'entrance_to_room': ((0.6, 0.6, 1.45), (2.4, 4.8, 0.4)),
    'kitchen_line': ((1.5, 2.6, 1.55), (0.0, 2.6, 0.8)),
    'bed_window': ((1.0, 2.6, 1.5), (3.2, 5.4, 0.5)),
    'bathroom': ((2.35, 1.65, 1.55), (3.9, 0.4, 0.6)),
    'scene_table': ((1.0, 4.9, 1.4), (2.0, 3.7, 0.1)),
    'hallway': ((-0.8, -1.4, 1.5), (3.0, -0.2, 0.9)),
    'topdown': ((2.1, 2.6, 10.0), (2.1, 2.7, 0.0)),
}
# hide ceilings for top view only
for name, (pos, tgt) in views.items():
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = (name == 'topdown' and ('ceiling' in o.name or o.name == 'fix_ceiling_light'))
    cam.location = pos
    d = Vector(tgt) - Vector(pos)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'blender_{name}.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', name)
