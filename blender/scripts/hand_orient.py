"""Re-orient the FP hand so the flashlight lens points along Blender -Y (= Unity +Z forward) and the wrist/sleeve
comes from lower-right in view; origin at the grip. Classification by albedo colour sampled at each vertex's UV:
grey/black low-saturation = flashlight, navy = sleeve. blender -b -P hand_orient.py -- in.fbx albedo.png out.fbx"""
import bpy, sys, os, colorsys
import numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
src, albedo, dst = a
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src)
ob = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
bpy.context.view_layer.objects.active = ob
for o in bpy.context.scene.objects: o.select_set(o == ob)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
img = bpy.data.images.load(albedo); W, H = img.size
px = np.array(img.pixels[:]).reshape(H, W, 4)
me = ob.data; uv = me.uv_layers.active.data
vcol = {}
for p in me.polygons:
    for li in p.loop_indices:
        vi = me.loops[li].vertex_index
        if vi in vcol: continue
        u, v = uv[li].uv
        x = min(W - 1, max(0, int(u * W))); y = min(H - 1, max(0, int(v * H)))
        vcol[vi] = px[y, x, :3]
co = np.array([v.co[:] for v in me.vertices])
flash, sleeve, skin = [], [], []
for vi, c in vcol.items():
    h, s, val = colorsys.rgb_to_hsv(*c)
    if s < 0.18 and val < 0.45: flash.append(vi)
    elif 0.55 < h < 0.75 and s > 0.2 and val < 0.5: sleeve.append(vi)
    elif 0.0 <= h < 0.12 and s > 0.15: skin.append(vi)
F, S = co[flash], co[sleeve]
print('CLASS flash', len(flash), 'sleeve', len(sleeve), 'skin', len(skin))
c0 = F.mean(0); u, s_, vt = np.linalg.svd(F - c0); axis = vt[0]
proj = (F - c0) @ axis
lo, hi = F[proj < np.percentile(proj, 15)], F[proj > np.percentile(proj, 85)]
def rad(P): return np.linalg.norm((P - c0) - np.outer((P - c0) @ axis, axis), axis=1).mean()
lens = axis if rad(hi) > rad(lo) else -axis            # the wider end is the head/lens
w = S.mean(0) - c0; w = w - (w @ lens) * lens; w /= np.linalg.norm(w)   # wrist direction perpendicular to the beam
# target frame: lens -> -Y ; wrist -> down-right in view = Blender (-X, -Z) mix
tl = np.array([0, -1, 0.0]); tw = np.array([-0.55, 0, -1.0]); tw /= np.linalg.norm(tw)
src_m = np.stack([lens, w, np.cross(lens, w)], 1); dst_m = np.stack([tl, tw, np.cross(tl, tw)], 1)
R = dst_m @ src_m.T
M = Matrix(((R[0, 0], R[0, 1], R[0, 2], 0), (R[1, 0], R[1, 1], R[1, 2], 0), (R[2, 0], R[2, 1], R[2, 2], 0), (0, 0, 0, 1)))
me.transform(Matrix.Translation(-Vector(c0)))
me.transform(M)
me.update()
print('ORIENT lens_radius_hi_lo', round(rad(hi), 4), round(rad(lo), 4), 'dims', tuple(round(x, 3) for x in ob.dimensions))
bpy.ops.export_scene.fbx(filepath=dst, use_selection=True, axis_forward='-Z', axis_up='Y', bake_space_transform=True,
                         path_mode='STRIP', embed_textures=False, mesh_smooth_type='FACE')
