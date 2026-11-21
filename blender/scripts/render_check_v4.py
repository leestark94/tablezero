"""Close-up geometry checks for the v4 props (Workbench, CPU-safe).
blender -b Room302.blend -P render_check_v4.py -- outdir"""
import bpy, sys, os
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
cam_data = bpy.data.cameras.new('cam'); cam_data.lens = 35
cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam); sc.camera = cam
views = {
    'v4_table_food': ((1.95, 3.05, 0.75), (1.72, 3.55, 0.33)),
    'v4_table_top': ((1.70, 3.58, 1.25), (1.70, 3.57, 0.33)),
    'v4_gloves_sink': ((1.0, 1.70, 1.35), (0.45, 1.70, 0.86)),
    'v4_hoodie_bed': ((2.0, 4.0, 1.2), (3.05, 4.65, 0.35)),
    'v4_towels': ((2.55, 1.0, 1.35), (2.52, 1.97, 1.1)),
    'v4_markers': ((-4.7, -6.6, 0.25), (-4.7, -6.0, 0.05)),
    'v4_floor_blood': ((2.9, 3.0, 1.6), (2.2, 3.9, 0.0)),
}
for name, (pos, tgt) in views.items():
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = 'ceiling' in o.name or o.name == 'fix_ceiling_light'
    cam.location = pos
    d = Vector(tgt) - Vector(pos)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{name}.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', name)
