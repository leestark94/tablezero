"""Close-up checks for v5 (labels, bath clutter, bigger markers). blender -b Room302.blend -P render_check_v5.py -- outdir"""
import bpy, sys, os
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.show_cavity = True; sc.display.shading.show_shadows = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
cd = bpy.data.cameras.new('cam'); cd.lens = 40
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
views = {
    'v5_condiments': ((0.55, 3.40, 1.05), (0.09, 3.38, 0.95)),
    'v5_bath_floor': ((2.6, 1.45, 1.3), (2.75, 0.45, 0.0)),
    'v5_shampoo': ((2.40, 0.55, 0.25), (2.40, 0.11, 0.03)),
    'v5_ramyeon': ((0.75, 2.45, 1.85), (0.25, 2.45, 1.75)),
    'v5_markers': ((-4.7, -6.5, 0.12), (-4.7, -6.0, 0.06)),
    'v5_markers_b': ((-4.1, -6.5, 0.12), (-4.1, -6.0, 0.06)),
}
hide = ('ceiling', 'kitchen_overhead_cabinet', 'fix_ceiling_light')
for name, (pos, tgt) in views.items():
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = any(h in o.name for h in hide)
    cam.location = pos
    cam.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{name}.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', name)
