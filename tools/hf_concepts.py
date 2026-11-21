"""Higgsfield concept images (images only, no 3D): first-person police hands + 3 suspects in the interrogation room.
Look/lighting follow the user's draft art in references_images/. Faces of suspects stay hidden by shadow/hair.
  python tools/hf_concepts.py            # 2 candidates each -> assets_src/concepts/<id>_<n>.png
"""
import json, pathlib, shutil, subprocess, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets_src' / 'concepts'
HF = shutil.which('higgsfield') or 'higgsfield'
MODEL = 'nano_banana_pro'
REF = {  # Higgsfield upload ids of the user's drafts
    'interrogation': '97e4eb4b-ced9-464a-8979-1e785077d5d0',
    's2_crop': '6d3d917f-b92b-48f7-bc79-25aa19262377',
    'scene302': '1e7e2939-5cb9-441a-9ef9-c5f2889a14e1',
    'hand_crop': '9e435126-cc41-4d70-8765-1c47f12f5b20',
    's1_ok': str(ROOT / 'assets_src' / 'concepts' / 'suspect_s1_kangdohyun_2.png'),
}
ROOM = ('Same Korean police interrogation room as image[1], with the same dark, moody cinematic lighting, camera angle, colour grade and '
        'photographic realism: dim room, cold blue light from the barred window behind, a warm practical lamp glow, a dark metal table '
        'in the foreground with faint reflections. The suspect sits at the table and the face must NOT be clearly visible: head lowered, '
        'features lost in shadow and hair, only fragments of the jaw or hands catch light. No interface, no subtitles, no text, no logos, '
        'no watermark. 16:9 cinematic still.')
JOBS = {
    'suspect_s2_leeseoyeon': (['interrogation', 's2_crop'], ROOM + ' The same Korean woman as image[2]: 29, long dark centre-parted hair '
                              'falling over her face, oversized dark brown cable-knit sweater, silver wristwatch on the left wrist, one hand '
                              'covering her mouth, exactly the mood of image[1].'),
    'suspect_s1_kangdohyun': (['interrogation'], ROOM + ' A Korean man, 31, logistics-centre day-shift supervisor: short black hair, '
                              'grey work jacket over a dark t-shirt, broad shoulders, elbows on the table, hands clasped in front of his mouth, '
                              'head bowed so the brow and eyes fall into deep shadow.'),
    'suspect_s3_parkhyunsoo': (['interrogation', 's1_ok'], 'Same interrogation room, darkness, colour grade and the SAME centred frontal '
                               'framing as image[2] (camera across the table, suspect centred behind it). A Korean man, 46, food-delivery '
                               'motorbike rider: short greying hair, a worn black padded rider jacket, weathered hands. He is slumped forward '
                               'with his head hanging low and his forehead almost resting on his clasped fists, so the whole face is turned '
                               'down into deep shadow; only the top of his greying head and his knuckles catch the cold window light. The face '
                               'must not be visible at all. No readable text anywhere, no labels on folders, no interface, no watermark. '
                               '16:9 cinematic still.'),
    'hands_fp_police': (['hand_crop', 'scene302'], 'Close first-person view model: the detective own two hands are the subject and fill '
                        'the lower half of the frame. Korean police detective, man in his late 30s: natural slightly tanned Korean skin, short '
                        'clean nails, visible knuckles and veins, a simple steel wristwatch on the left wrist, dark navy plain-clothes jacket '
                        'sleeves with a little white shirt cuff. Right hand grips a black tactical flashlight like image[1], beam pointing '
                        'forward; left hand half-open, raised, about to push a door. Background: a dark Korean one-room at night, heavily out '
                        'of focus, same darkness and colour grade as image[2], do not copy its layout. No gloves. Anatomically correct hands, '
                        'five fingers each. No interface, no text, no logos, no brand names, no watermark. 16:9 cinematic still.'),
}


def run(args):
    p = subprocess.run([HF] + args + ['--json'], capture_output=True, text=True, encoding='utf-8', shell=sys.platform == 'win32')
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {'error': (p.stdout + p.stderr)[-500:]}


def urls(obj):
    found = []
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str) and v.startswith('http') and any(v.lower().split('?')[0].endswith(e) for e in ('.png', '.jpg', '.jpeg', '.webp')):
                    found.append(v)
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(obj)
    return list(dict.fromkeys(found))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1:] or list(JOBS)
    for jid in only:
        refs, prompt = JOBS[jid]
        for n in (1, 2):
            args = ['generate', 'create', MODEL, '--prompt', prompt, '--aspect_ratio', '16:9', '--resolution', '2k', '--wait']
            for r in refs:
                args += ['--image-references', REF[r]]
            res = run(args)
            got = [u for u in urls(res) if '_min.' not in u and REF['interrogation'] not in u and REF['scene302'] not in u
                   and REF['s2_crop'] not in u and REF['hand_crop'] not in u]
            if not got:
                print(jid, n, 'NO IMAGE', json.dumps(res, ensure_ascii=False)[:400]); continue
            dst = OUT / f'{jid}_{n}.png'
            urllib.request.urlretrieve(got[0], dst)
            (OUT / f'{jid}_{n}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
            print(jid, n, '->', dst.name)


if __name__ == '__main__':
    main()
