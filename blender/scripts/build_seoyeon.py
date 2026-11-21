"""이서연 (29) — rigged 3D character from MPFB2 (MakeHuman, CC0 assets). Headless (needs the MPFB extension enabled,
so run WITHOUT --factory-startup):
  blender -b -P blender/scripts/build_seoyeon.py -- <out.fbx> <out.blend>

Pipeline: MPFB base mesh with macro shape (Korean woman, 29, slim/average) -> mixamo_unity rig (64 bones: spine, neck,
head, jaw, both eyes, full fingers — maps to Unity Humanoid) -> macro targets baked -> helper geometry removed ->
facial expression shape keys (Asian expression units: eye closure L/R, brows, mouth) added for blink/lip/brow acting ->
CC0 system assets when installed (skin, brown eyes, brows, lashes, long hair, clothes) -> FBX (Unity axes).
Identity match to the approved profile is iterative: face targets below are first-pass and must be compared to
profile_s2 at the same angle before sign-off.
"""
import sys, os, math, importlib
import bpy

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT_FBX = args[0] if args else os.path.join(REPO, 'blender', 'out', 'seoyeon', 'Seoyeon.fbx')
OUT_BLEND = args[1] if len(args) > 1 else OUT_FBX.replace('.fbx', '.blend')

def mod(name):
    for root in ('bl_ext.blender_org.mpfb', 'mpfb'):
        try:
            return importlib.import_module(f'{root}.{name}')
        except ImportError:
            continue
    raise ImportError(name)

HumanService = mod('services.humanservice').HumanService
TargetService = mod('services.targetservice').TargetService
AssetService = mod('services.assetservice').AssetService
ObjectService = mod('services.objectservice').ObjectService
MPFB_DATA = os.path.dirname(mod('services.humanservice').__file__).replace('services', 'data')

bpy.ops.wm.read_homefile(use_empty=True)

# ------------------------------------------------------------ body: 29-year-old Korean woman, 163 cm, slim-average
macro = TargetService.get_default_macro_info_dict()
macro.update({'gender': 0.0, 'age': 0.53, 'muscle': 0.42, 'weight': 0.40, 'proportions': 0.62, 'height': 0.42,
              'cupsize': 0.42, 'firmness': 0.55})
macro['race'] = {'asian': 1.0, 'caucasian': 0.0, 'african': 0.0}
human = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True, feet_on_ground=True,
                                  scale=0.1, macro_detail_dict=macro)
human.name = 'Seoyeon_Body'

# first-pass face/body details toward the profile: oval face, soft jaw, slightly narrow nose bridge, fuller lower lip
DETAILS = {
    'head/head-oval': 0.45, 'head/head-age-decr|incr': -0.15,
    'chin/chin-prominent-decr|incr': -0.15, 'chin/chin-width-decr|incr': -0.25,
    'nose/nose-width1-decr|incr': -0.15, 'nose/nose-scale-vert-decr|incr': -0.10,
    'mouth/mouth-lowerlip-volume-decr|incr': 0.20, 'eyes/r-eye-height2-decr|incr': 0.10, 'eyes/l-eye-height2-decr|incr': 0.10,
    'neck/neck-scale-horiz-decr|incr': -0.15, 'torso/torso-scale-horiz-decr|incr': -0.10,
}
applied = []
for frag, w in DETAILS.items():
    group, rest = frag.split('/')
    if '|' in rest:
        base, pair = rest.split('-decr|incr')[0], None
        name = f'{base}-{"incr" if w > 0 else "decr"}'
    else:
        name = rest
    path = os.path.join(MPFB_DATA, 'targets', group, name + '.target.gz')
    if os.path.exists(path):
        TargetService.load_target(human, path, weight=abs(w), name=name)
        applied.append(name)
print('DETAIL_TARGETS', applied)

# ------------------------------------------------------------ rig (Unity-humanoid-friendly, with jaw/eyes/fingers)
rig = HumanService.add_builtin_rig(human, 'mixamo_unity', import_weights=True)
rig.name = 'Seoyeon_Rig'

# ------------------------------------------------------------ CC0 system assets (if the pack is installed)
def first_asset(subdir, kind, *needles):
    try:
        lst = AssetService.list_mhclo_assets(subdir) if kind == 'mhclo' else AssetService.list_mhmat_assets(subdir)
    except Exception:
        return None
    for n in needles:
        for p in lst:
            if n in str(p).lower():
                return str(p)
    return None

equipped = {}
skin = first_asset('skins', 'mhmat', 'young_asian_female', 'middleage_asian_female', 'asian_female')
if skin:
    HumanService.set_character_skin(skin, human, skin_type='ENHANCED_SSS'); equipped['skin'] = skin
# brows come from the projected reference photo (no brow cards on top of painted brows); long-sleeve top + trousers
# (male_casualsuit04 fitted to her body by MPFB, re-materialled as brown cable knit / dark wool); dark flats
for subdir, needles, atype in (('eyes', ('low-poly',), 'Eyes'), ('eyelashes', ('eyelashes02', 'eyelashes01'), 'Eyelashes'),
                               ('hair', ('long01',), 'Hair'), ('clothes', ('male_casualsuit04',), 'Clothes'),
                               ('clothes', ('shoes04',), 'Clothes')):
    p = first_asset(subdir, 'mhclo', *needles)
    if p:
        try:
            HumanService.add_mhclo_asset(p, human, asset_type=atype, subdiv_levels=0, material_type='MAKESKIN')
            equipped[atype + ':' + os.path.basename(p)] = p
        except Exception as e:
            print('ASSET_FAIL', atype, e)
print('EQUIPPED', equipped)

# bake macro + detail targets into the base shape (assets were fitted to this shape already)
bpy.context.view_layer.objects.active = human
for o in bpy.data.objects: o.select_set(o == human)
if human.data.shape_keys:
    bpy.ops.object.shape_key_remove(all=True, apply_mix=True)

# ------------------------------------------------------------ facial acting shape keys (Asian expression units)
units = os.path.join(MPFB_DATA, 'targets', 'expression', 'units', 'asian')
FACE = ['eye-left-closure', 'eye-right-closure', 'eye-left-slit', 'eye-right-slit', 'eyebrows-left-down', 'eyebrows-right-down',
        'eyebrows-left-inner-up', 'eyebrows-right-inner-up', 'mouth-open', 'mouth-compression', 'mouth-depression',
        'mouth-pursing', 'mouth-corner-puller', 'mouth-elevation', 'mouth-retraction', 'nose-compression', 'neck-platysma']
if not human.data.shape_keys:
    human.shape_key_add(name='Basis', from_mix=False)
loaded = []
for u in FACE:
    p = os.path.join(units, u + '.target.gz')
    if os.path.exists(p):
        TargetService.load_target(human, p, weight=0.0, name='fx_' + u.replace('-', '_'))
        loaded.append(u)
print('FACE_KEYS', len(loaded))

# ------------------------------------------------------------ remove hidden geometry for real (helpers + body under clothes)
bpy.context.view_layer.objects.active = human
for o in bpy.data.objects: o.select_set(o == human)
import bmesh
for m in list(human.modifiers):
    if m.type != 'MASK':
        continue
    g = human.vertex_groups.get(m.vertex_group)
    if g is not None:
        gi = g.index
        bm = bmesh.new(); bm.from_mesh(human.data)
        dl = bm.verts.layers.deform.verify()
        kill = [v for v in bm.verts if ((gi in v[dl]) and v[dl][gi] > 0.0) == bool(m.invert_vertex_group)]
        print('MASK', m.name, m.vertex_group, 'invert', m.invert_vertex_group, 'delete', len(kill))
        bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(human.data); bm.free()
    human.modifiers.remove(m)
human.data.update()

# ------------------------------------------------------------ outfit split: knit top vs wool trousers (by height / arm reach)
suit = next((o for o in bpy.data.objects if 'casualsuit' in o.name), None)
if suit:
    hips_z = (rig.matrix_world @ rig.data.bones['mixamorig:Hips'].head_local).z
    knit = bpy.data.materials.new('Seoyeon_Knit'); trousers = bpy.data.materials.new('Seoyeon_Trousers')
    suit.data.materials.clear(); suit.data.materials.append(knit); suit.data.materials.append(trousers)
    mwS = suit.matrix_world; n_k = 0
    for poly in suit.data.polygons:
        c = mwS @ poly.center
        is_top = c.z > hips_z + 0.02 or abs(c.x) > 0.22
        poly.material_index = 0 if is_top else 1; n_k += is_top
    print('OUTFIT_SPLIT knit_faces', n_k, 'of', len(suit.data.polygons))

# ------------------------------------------------------------ identity: project the approved front reference onto the face
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seoyeon_face_bake
tex_dir = os.path.join(os.path.dirname(OUT_FBX), 'textures'); os.makedirs(tex_dir, exist_ok=True)
eyes_obj = next((o for o in bpy.data.objects if 'low-poly' in o.name or 'high-poly' in o.name), None)
skin_img = next((i for i in bpy.data.images if 'diffuse' in i.name.lower() and 'skinned' in i.name.lower()), None)
if eyes_obj and skin_img:
    seoyeon_face_bake.bake(human, eyes_obj, os.path.join(REPO, 'assets_src', '3d_sources', 's2.png'),
                           bpy.path.abspath(skin_img.filepath), os.path.join(tex_dir, 'seoyeon_skin_diffuse.png'))
else:
    print('FACE_BAKE_SKIPPED eyes', bool(eyes_obj), 'skin', bool(skin_img))

# ------------------------------------------------------------ export
os.makedirs(os.path.dirname(OUT_FBX), exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.type in ('MESH', 'ARMATURE'):
        o.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.fbx(filepath=OUT_FBX, use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
                         axis_forward='-Z', axis_up='Y', bake_space_transform=False, object_types={'MESH', 'ARMATURE'},
                         use_mesh_modifiers=False, mesh_smooth_type='FACE', use_tspace=True, add_leaf_bones=False,
                         primary_bone_axis='Y', secondary_bone_axis='X', armature_nodetype='NULL', bake_anim=False,
                         path_mode='COPY', embed_textures=False)
import shutil
copied = []
for img in bpy.data.images:
    fp = bpy.path.abspath(img.filepath) if img.filepath else ''
    if fp and os.path.isfile(fp) and os.path.dirname(os.path.abspath(fp)) != os.path.abspath(tex_dir):
        shutil.copy2(fp, os.path.join(tex_dir, os.path.basename(fp))); copied.append(os.path.basename(fp))
print('TEXTURES', copied)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print('SEOYEON_BUILT', OUT_FBX, 'verts', len(human.data.vertices), 'bones', len(rig.data.bones),
      'shapekeys', len(human.data.shape_keys.key_blocks) if human.data.shape_keys else 0)
