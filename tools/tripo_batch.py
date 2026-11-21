"""Batch Tripo 3D generation from data/tripo_asset_plan.json via the installed `tripo` CLI.

  python tools/tripo_batch.py --estimate            # dry-run every item: validates + sums the credit estimate (no credits)
  python tools/tripo_batch.py --tier A --budget 1000 # generate tier A, stop before the running estimate passes the budget

Never tops up or buys anything: when the balance is short it stops and reports. Outputs go to
assets_src/tripo/<id>/ (FBX + task json) and are appended to qa/logs/tripo_generations.tsv for the license ledger.
"""
import argparse, json, pathlib, subprocess, sys, datetime, shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLAN = ROOT / 'data' / 'tripo_asset_plan.json'
OUT = ROOT / 'assets_src' / 'tripo'
LOG = ROOT / 'qa' / 'logs' / 'tripo_generations.tsv'
TRIPO = shutil.which('tripo') or 'tripo'


def run(args):
    p = subprocess.run([TRIPO] + args, capture_output=True, text=True, encoding='utf-8', shell=sys.platform == 'win32')
    try:
        return json.loads(p.stdout.strip().splitlines()[-1]) if p.stdout.strip() else {'error': p.stderr.strip()}
    except json.JSONDecodeError:
        return {'error': (p.stdout + p.stderr).strip()[-400:]}


def make_args(item, suffix, dry):
    scenario = item.get('for', 'game-pc')
    chain = 'texture,rig,convert:fbx' if scenario == 'anim' else 'convert:fbx'
    a = ['make', f"{item['prompt']}, {suffix}", '--for', scenario, '--then', chain, '--name', item['id'],
         '-o', str(OUT / item['id']), '--json', '--yes', '--no-open', '--quiet']
    return a + (['--dry-run'] if dry else [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--estimate', action='store_true')
    ap.add_argument('--tier', default='ABC')
    ap.add_argument('--only', default='')
    ap.add_argument('--budget', type=int, default=0, help='max credits this run may spend (estimate-based)')
    a = ap.parse_args()
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    items = [i for i in plan['items'] if i['tier'] in a.tier and (not a.only or i['id'] in a.only.split(','))]
    bal = run(['balance', '--json']).get('balance', 0)
    total, rows = 0, []
    for it in items:
        est = run(make_args(it, plan['style_suffix'], True))
        cost = est.get('generation_credits_estimate', 0) or 0
        ok = est.get('valid', False)
        rows.append((it['id'], it['tier'], cost, ok, '; '.join(est.get('errors', [])) or est.get('error', '')))
        if a.estimate:
            continue
        if (OUT / it['id']).exists() and any((OUT / it['id']).rglob('*.fbx')):
            print('skip (exists)', it['id']); continue
        if not ok:
            print('invalid', it['id'], rows[-1][4]); continue
        if a.budget and total + cost > a.budget:
            print(f'stop: budget {a.budget} reached before {it["id"]}'); break
        if total + cost > bal:
            print(f'stop: balance {bal} credits is not enough for {it["id"]} (~{cost}); top up first'); break
        res = run(make_args(it, plan['style_suffix'], False))
        total += cost
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open('a', encoding='utf-8') as f:
            f.write('\t'.join([datetime.datetime.now().isoformat(timespec='seconds'), it['id'], str(cost),
                               json.dumps(res, ensure_ascii=False)[:600]]) + '\n')
        print('done', it['id'], res.get('status', res.get('error', '')))
    est_total = sum(r[2] for r in rows)
    print(json.dumps({'balance': bal, 'items': len(rows), 'estimate_total_credits': est_total,
                      'invalid': [r[0] for r in rows if not r[3]], 'per_item': rows}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
