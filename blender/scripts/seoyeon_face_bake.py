"""Identity pass for 이서연: projects the approved front reference (assets_src/3d_sources/s2.png) onto the MPFB skin texture.

Method (no ML, deterministic):
- landmarks on the mesh: eye centres (eye mesh halves), mouth corners (lips material), measured in front orthographic space (X, Z)
- landmarks on the photo: pixel positions measured on a grid crop (see PHOTO_LM)
- per-axis affine fit X->px, Z->py (least squares)
- every front-facing head triangle is rasterised in UV space; texels take the photo colour, weighted by
  facing (fades on the sides), a face-oval mask (feathered), and a luminance mask so hair strands across the
  forehead/cheeks are NOT painted onto the skin (those come from real hair cards instead)
- the whole skin texture is first gain-matched to the photo's skin tone so neck/arms/hands have no seam.
"""
import math
import numpy as np
import bpy

# photo landmarks (original pixels of s2.png, measured on a 25 px grid crop)
PHOTO_LM = {'eye_r': (793.0, 345.5), 'eye_l': (871.5, 344.0), 'mouth_r': (804.0, 434.3), 'mouth_l': (861.7, 434.3)}
FACE_CENTRE, FACE_RADII = (832.0, 402.0), (84.0, 92.0)


def _smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _load_rgba(path):
    img = bpy.data.images.load(path, check_existing=True)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)   # bottom-up rows
    return img, px, w, h


def bake(human, eyes_obj, photo_path, skin_path, out_path):
    mw = human.matrix_world
    me = human.data
    me.calc_loop_triangles()
    co = np.array([tuple(mw @ v.co) for v in me.vertices], dtype=np.float64)
    nrm = np.array([tuple((mw.to_3x3() @ v.normal).normalized()) for v in me.vertices], dtype=np.float64)

    # ---- mesh landmarks
    ev = np.array([tuple(eyes_obj.matrix_world @ v.co) for v in eyes_obj.data.vertices])
    eye_l = ev[ev[:, 0] > 0].mean(axis=0); eye_r = ev[ev[:, 0] < 0].mean(axis=0)   # subject's left = +X (faces -Y)
    lips_idx = [i for i, m in enumerate(me.materials) if m and m.name.lower().endswith('lips')]
    lip_verts = sorted({v for p in me.polygons if p.material_index in lips_idx for v in p.vertices})
    lv = co[lip_verts]
    front = lv[lv[:, 1] < np.percentile(lv[:, 1], 60)]
    mouth_r = front[np.argmin(front[:, 0])]; mouth_l = front[np.argmax(front[:, 0])]
    mouth_z = front[:, 2].mean()

    # ---- per-axis affine fit
    X = np.array([eye_r[0], eye_l[0], mouth_r[0], mouth_l[0]]); PX = np.array([PHOTO_LM[k][0] for k in ('eye_r', 'eye_l', 'mouth_r', 'mouth_l')])
    ax, bx = np.polyfit(X, PX, 1)
    Z = np.array([(eye_r[2] + eye_l[2]) / 2, mouth_z]); PY = np.array([(PHOTO_LM['eye_r'][1] + PHOTO_LM['eye_l'][1]) / 2, PHOTO_LM['mouth_r'][1]])
    ay, by = np.polyfit(Z, PY, 1)
    head = co[co[:, 2] > mouth_z - 0.16]
    nose = head[np.argmin(head[:, 1])]
    print('FACE_FIT ax=%.1f ay=%.1f nose_pred=(%.0f,%.0f) expect~(832,397)' % (ax, ay, ax * nose[0] + bx, ay * nose[2] + by))

    # ---- textures
    _, photo, pw, ph = _load_rgba(photo_path)
    photo = photo[::-1]                                       # top-down rows for pixel coords
    skin_img, skin, sw, sh = _load_rgba(skin_path)
    out = skin.copy()

    def sample(px_, py_):
        x = np.clip(px_, 0, pw - 1.001); y = np.clip(py_, 0, ph - 1.001)
        x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = (x - x0)[..., None]; fy = (y - y0)[..., None]
        c = (photo[y0, x0] * (1 - fx) * (1 - fy) + photo[y0, x0 + 1] * fx * (1 - fy) +
             photo[y0 + 1, x0] * (1 - fx) * fy + photo[y0 + 1, x0 + 1] * fx * fy)
        return c[..., :3]

    uv = me.uv_layers.active.data
    acc_c = np.zeros((sh, sw, 3), np.float32); acc_w = np.zeros((sh, sw), np.float32)
    zmin = mouth_z - 0.12                                     # down to the upper neck
    for tri in me.loop_triangles:
        vs = tri.vertices
        if co[list(vs), 2].min() < zmin:
            continue
        f = -nrm[list(vs), 1]
        if f.max() < 0.12:
            continue
        uvs = np.array([uv[l].uv[:] for l in tri.loops]) * [sw, sh]
        P = np.array([[ax * co[v, 0] + bx, ay * co[v, 2] + by] for v in vs])
        x0, y0 = np.floor(uvs.min(axis=0)).astype(int); x1, y1 = np.ceil(uvs.max(axis=0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, sw - 1), min(y1, sh - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        (ux0, uy0), (ux1, uy1), (ux2, uy2) = uvs
        den = (uy1 - uy2) * (ux0 - ux2) + (ux2 - ux1) * (uy0 - uy2)
        if abs(den) < 1e-9:
            continue
        l0 = ((uy1 - uy2) * (gx - ux2) + (ux2 - ux1) * (gy - uy2)) / den
        l1 = ((uy2 - uy0) * (gx - ux2) + (ux0 - ux2) * (gy - uy2)) / den
        l2 = 1 - l0 - l1
        inside = (l0 >= -0.01) & (l1 >= -0.01) & (l2 >= -0.01)
        if not inside.any():
            continue
        px_ = l0 * P[0, 0] + l1 * P[1, 0] + l2 * P[2, 0]; py_ = l0 * P[0, 1] + l1 * P[1, 1] + l2 * P[2, 1]
        ff = l0 * f[0] + l1 * f[1] + l2 * f[2]
        c = sample(px_, py_)
        lum = c[..., 0] * 0.3 + c[..., 1] * 0.59 + c[..., 2] * 0.11
        d = np.sqrt(((px_ - FACE_CENTRE[0]) / FACE_RADII[0]) ** 2 + ((py_ - FACE_CENTRE[1]) / FACE_RADII[1]) ** 2)
        w = _smooth(0.15, 0.55, ff) * (1 - _smooth(0.82, 1.02, d)) * _smooth(0.30, 0.46, lum)
        w = np.where(inside, w, 0)
        acc_c[y0:y1 + 1, x0:x1 + 1][inside] = c[inside]
        acc_w[y0:y1 + 1, x0:x1 + 1] = np.maximum(acc_w[y0:y1 + 1, x0:x1 + 1], w)

    m = acc_w > 0.7
    if m.sum() > 50:
        gain = acc_c[m].mean(axis=0) / np.maximum(out[..., :3][m].mean(axis=0), 1e-4)
        gain = np.clip(gain, 0.6, 1.6)
        out[..., :3] = np.clip(out[..., :3] * gain, 0, 1)
        print('SKIN_GAIN', np.round(gain, 3), 'texels', int(m.sum()))
    w3 = acc_w[..., None]
    out[..., :3] = out[..., :3] * (1 - w3) + acc_c * w3

    res = bpy.data.images.new('seoyeon_skin_diffuse', sw, sh, alpha=True)
    res.pixels[:] = out.reshape(-1)
    res.filepath_raw = out_path; res.file_format = 'PNG'; res.save()
    print('FACE_BAKED', out_path, sw, sh, 'face_texels', int((acc_w > 0.05).sum()))
    return out_path
