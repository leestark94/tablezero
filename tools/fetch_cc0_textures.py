"""Download CC0 PBR textures from Poly Haven (https://polyhaven.com/license) and log them.

python -I tools/fetch_cc0_textures.py
Writes TableZero.Unity/Assets/TableZero/Art/Textures/PolyHaven/<id>/<id>_<map>_2k.jpg
and appends rows to ASSET_LICENSE_LEDGER.csv (file, source URL, license, use, date).
"""
import csv, datetime, json, pathlib, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEST = ROOT / 'TableZero.Unity' / 'Assets' / 'TableZero' / 'Art' / 'Textures' / 'PolyHaven'
LEDGER = ROOT / 'ASSET_LICENSE_LEDGER.csv'
# asset id -> intended use in CASE 001
ASSETS = {
    'white_plaster_02': '302호 실크벽지 대용 벽면 (도배 질감은 별도 디테일 맵 필요)',
    'laminate_floor_02': '302호 바닥 강마루/장판 대용',
    'interior_tiles': '화장실 벽 타일',
    'worn_tile_floor': '화장실 바닥 타일',
    'concrete_wall_001': '빌라 복도/계단 벽',
    'plastered_wall': '빌라 공용부 벽 하단',
    'kitchen_wood': '주방 상하부장 도어 목무늬',
    'rough_linen': '이불/침구 원단',
    'cotton_jersey': '베개 커버/의류',
    'dirty_carpet': '현관 발매트',
    'oak_veneer_01': '낮은 식탁/협탁',
    'rectangular_facade_tiles_02': '화장실 벽 직사각 타일(한국 원룸 욕실)',
    'dirty_tiles': '욕실 바닥 소형 타일 후보',
    'brown_brick_02': '창밖 맞은편 적벽돌 빌라 외벽',
}
MAPS = {'Diffuse': 'diff', 'nor_gl': 'nor_gl', 'Rough': 'rough', 'AO': 'ao'}
UA = {'User-Agent': 'TableZeroAssetFetch/1.0'}

def get(url, timeout=60):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()

def main(res='2k'):
    DEST.mkdir(parents=True, exist_ok=True)
    rows = []
    for aid, use in ASSETS.items():
        files = json.loads(get(f'https://api.polyhaven.com/files/{aid}'))
        out = DEST / aid
        out.mkdir(exist_ok=True)
        for key, short in MAPS.items():
            if key not in files:
                continue
            node = files[key].get(res, {}).get('jpg') or files[key].get(res, {}).get('png')
            if not node:
                continue
            ext = node['url'].rsplit('.', 1)[-1]
            path = out / f'{aid}_{short}_{res}.{ext}'
            if not path.exists():
                path.write_bytes(get(node['url'], 180))
            rows.append([str(path.relative_to(ROOT)).replace('\\', '/'), node['url'], 'CC0 1.0 (Poly Haven)',
                         '출처 표기 불필요, 상업 사용 가능 (https://polyhaven.com/license)', use, datetime.date.today().isoformat()])
            print('ok', path.name, flush=True)
    new = not LEDGER.exists()
    existing = set()
    if not new:
        existing = {r[0] for r in csv.reader(LEDGER.open(encoding='utf-8-sig'))}
    with LEDGER.open('a', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        if new:
            w.writerow(['file', 'source_url', 'license', 'conditions', 'used_in', 'checked_date'])
        for r in rows:
            if r[0] not in existing:
                w.writerow(r)

if __name__ == '__main__':
    main(*(sys.argv[1:2]))
