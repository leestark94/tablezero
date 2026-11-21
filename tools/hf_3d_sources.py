"""3D source images (Higgsfield): clean, evenly lit, single subject — derived from the user-approved concepts.
  python tools/hf_3d_sources.py s2      # 이서연 full body A-pose (Seedream 5.0 Pro)   ~2 credits
  python tools/hf_3d_sources.py hand    # isolated right hand + flashlight (Nano Banana Pro) ~2 credits
Saves full-resolution results to assets_src/3d_sources/<id>.png (+ job json)."""
import json, pathlib, re, shutil, subprocess, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets_src' / '3d_sources'
C = ROOT / 'assets_src' / 'concepts'
HF = shutil.which('higgsfield') or 'higgsfield'

JOBS = {
    's2': ('seedream_v5_pro', [C / 'suspect_s2_leeseoyeon_1.png', ROOT / 'assets_src' / 'tripo' / 'refs' / 'ref_s2_seoyeon.png'],
           ['--aspect_ratio', '2:3', '--resolution', '2k'],
           'Full-body photo of the same Korean woman as image[1] and image[2], for 3D reconstruction: standing straight, facing the camera, '
           'relaxed A-pose with arms slightly away from the body, feet shoulder-width apart, whole body from head to shoes in frame. '
           'Keep exactly: long dark centre-parted hair below the chest, oversized dark brown cable-knit sweater, silver metal wristwatch on '
           'the LEFT wrist. Dark grey slacks, black flat shoes. Calm neutral face, age 29, natural Korean features. Soft even studio light '
           'from the front, no harsh shadows, plain light grey seamless background. No text, no logo.'),
    'hand': ('nano_banana_pro', [C / 'hands_fp_police_2.png'], ['--aspect_ratio', '1:1', '--resolution', '2k'],
             'Isolated product-style photo of the RIGHT hand and forearm from image[1]: a Korean man in his late 30s gripping the same black '
             'tactical flashlight, natural slightly tanned skin, short clean nails, visible knuckles, dark navy jacket sleeve ending mid-forearm '
             'with a thin white shirt cuff. Three-quarter side view, the whole hand, flashlight and sleeve end fully in frame, nothing cropped. '
             'Flashlight off. Soft even studio light, no harsh shadows, plain light grey seamless background. Anatomically correct five fingers. '
             'No other hand, no room, no text, no logo.'),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for jid in sys.argv[1:]:
        model, refs, extra, prompt = JOBS[jid]
        args = [HF, 'generate', 'create', model, '--prompt', prompt, *extra, '--wait', '--json']
        for r in refs:
            args += ['--image-references', str(r)]
        p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', shell=sys.platform == 'win32')
        t = p.stdout
        (OUT / f'{jid}.json').write_text(t, encoding='utf-8')
        urls = [u for u in re.findall(r'https://[^"\s]+', t) if 'd8j0ntlcm91z4' in u and '_min.' not in u
                and any(x in u.lower() for x in ('.png', '.jpg', '.jpeg', '.webp'))]
        if not urls:
            print(jid, 'NO RESULT', (t + p.stderr)[-400:]); continue
        dst = OUT / f'{jid}.png'
        urllib.request.urlretrieve(urls[0], dst)
        print(jid, '->', dst)


if __name__ == '__main__':
    main()
