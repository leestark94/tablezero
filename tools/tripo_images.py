"""Image stage ONLY (no 3D): concept sheets for the essential characters, for user approval.
Uses Tripo's image models through the installed CLI. Stops if the balance is 0; never tops up.

  python tools/tripo_images.py                 # all four briefs
  python tools/tripo_images.py --only s2       # one brief
Outputs: assets_src/tripo/concepts/<id>/   (review these; 3D runs only from an approved image)
Brief: docs/art/CHARACTER_IMAGE_BRIEF.md
"""
import argparse, json, pathlib, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets_src' / 'tripo' / 'concepts'
REFS = ROOT / 'assets_src' / 'tripo' / 'refs'
TRIPO = shutil.which('tripo') or 'tripo'
MODEL = 'banana_pro'   # strongest identity/style consistency among the listed image models
STYLE = ('photorealistic, natural Korean everyday person, soft even studio lighting for 3D reconstruction, no harsh shadows, '
         'plain neutral grey background, no text, no logo, no watermark')

JOBS = {
    's2': {'kind': 'i2i', 'refs': ['ref_s2_seoyeon.png', 'ref_s2_portrait.png'], 'prompt':
           'Character turnaround sheet of the same Korean woman as image[1] and image[2]: front, side and back views side by side, '
           'full body, relaxed A-pose, same height and scale in each view. Keep exactly: long dark centre-parted hair below the chest, '
           'oversized dark brown cable-knit sweater, silver metal wristwatch on the LEFT wrist. Add dark grey slacks and black flats. '
           'Face visible, tired eyes, light makeup, age 29. Remove all subtitles and UI. ' + STYLE},
    'hands': {'kind': 'i2i', 'refs': ['ref_hand_flashlight.png', 'ref_hand_left_door.png'], 'prompt':
              'First-person game view-model sheet based on image[1] and image[2]: bare adult male hands (no gloves), dark navy jacket sleeves. '
              'Panel 1: right hand gripping a black tactical flashlight seen from the player\'s eyes. Panel 2: the same right hand and flashlight '
              'from a three-quarter side view. Panel 3: left hand open, palm forward, as if bracing on a door frame. Anatomically correct five '
              'fingers, isolated, no room, remove all UI text. ' + STYLE},
    's1': {'kind': 'i2i_style', 'refs': ['@s2'], 'prompt':
           'Character turnaround sheet in exactly the same rendering style, lighting, framing and A-pose as image[1], but a different person: '
           'Korean man age 31, logistics center day-shift supervisor, short black hair, light stubble, grey work jacket over a plain t-shirt, '
           'jeans, sneakers, average to sturdy build, looks like he came straight from work. Front, side and back views. ' + STYLE},
    's3': {'kind': 'i2i_style', 'refs': ['@s2'], 'prompt':
           'Character turnaround sheet in exactly the same rendering style, lighting, framing and A-pose as image[1], but a different person: '
           'Korean man age 46, food delivery motorbike rider, sun-weathered face, short greying hair, black padded rider jacket, cargo pants, '
           'worn sneakers, no helmet. Front, side and back views. ' + STYLE},
}


def tripo(args):
    p = subprocess.run([TRIPO] + args, capture_output=True, text=True, encoding='utf-8', shell=sys.platform == 'win32')
    out = p.stdout.strip()
    try:
        return json.loads(out.splitlines()[-1]) if out else {'error': p.stderr.strip()[-400:]}
    except json.JSONDecodeError:
        return {'error': (out + p.stderr)[-400:]}


def approved_sheet(cid):
    d = OUT / cid
    imgs = sorted(d.glob('*.png')) + sorted(d.glob('*.jpg')) + sorted(d.glob('*.webp'))
    ok = d / 'APPROVED.txt'
    return (d / ok.read_text(encoding='utf-8').strip()) if ok.exists() else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    bal = tripo(['balance', '--json']).get('balance', 0)
    if not bal:
        print('stop: Tripo balance is 0 credits on the CLI account (`tripo whoami`); nothing generated'); return
    for cid, job in JOBS.items():
        if a.only and cid not in a.only.split(','):
            continue
        inputs = []
        for r in job['refs']:
            if r.startswith('@'):
                src = approved_sheet(r[1:])
                if not src:
                    print(f'skip {cid}: needs the approved {r[1:]} sheet first (write its file name into concepts/{r[1:]}/APPROVED.txt)'); inputs = None; break
                inputs.append(str(src))
            else:
                inputs.append(str(REFS / r))
        if inputs is None:
            continue
        (OUT / cid).mkdir(parents=True, exist_ok=True)
        res = tripo(['generate', 'image-to-image', *inputs, '--prompt', job['prompt'], '--model', MODEL,
                     '-o', str(OUT / cid), '--name', f'concept_{cid}', '--json', '--yes', '--no-open', '--quiet'])
        print(cid, json.dumps(res, ensure_ascii=False)[:300])


if __name__ == '__main__':
    main()
