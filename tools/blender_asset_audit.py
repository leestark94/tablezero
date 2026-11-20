"""Run inside Blender --background FILE.blend --python blender_asset_audit.py
Read-only on source scene. Checks geometry, materials, skeletons, textures.
It NEVER generates replacement geometry or grades aesthetics automatically.
"""
import json,sys
from pathlib import Path
try:import bpy
except ImportError:raise SystemExit('Run with Blender bundled Python')
report={'scene':bpy.data.filepath,'mesh_objects':0,'armatures':0,'materials':0,'warnings':[],'errors':[]}
for o in bpy.data.objects:
 if o.type=='ARMATURE':report['armatures']+=1
 if o.type!='MESH':continue
 report['mesh_objects']+=1
 if o.name.lower().startswith(('cube','sphere','cylinder','capsule','placeholder','temp')):
  report['errors'].append(f'{o.name}: suspicious prototype naming')
 if len(o.data.polygons)==0:report['errors'].append(f'{o.name}: no faces')
 if len(o.data.uv_layers)==0:report['warnings'].append(f'{o.name}: no UVs')
 if not o.material_slots:report['errors'].append(f'{o.name}: no materials')
 if not any(m.type=='ARMATURE' for m in o.modifiers) and o.name.lower().startswith(('suspect','hand','actor','npc')):
  report['errors'].append(f'{o.name}: human mesh no skeleton binding')
 for slot in o.material_slots:
  m=slot.material
  if m is None:report['errors'].append(f'{o.name}: missing material');continue
  if not m.use_nodes:report['warnings'].append(f'{o.name}: material {m.name} non-node')
  else:
   for n in m.node_tree.nodes:
    if n.type=='TEX_IMAGE' and (not n.image or (n.image.source=='FILE' and not n.image.packed_file and n.image.filepath and not Path(bpy.path.abspath(n.image.filepath)).exists())):
     report['errors'].append(f'{o.name}: missing image file in {m.name}')
report['materials']=len(bpy.data.materials)
out=Path(bpy.path.abspath('//'))/'TABLEZERO_BLENDER_AUDIT.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if report['errors']:sys.exit(1)
