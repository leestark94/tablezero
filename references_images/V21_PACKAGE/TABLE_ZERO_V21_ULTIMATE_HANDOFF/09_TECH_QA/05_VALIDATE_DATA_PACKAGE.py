#!/usr/bin/env python3
"""Static validation of V21.1 design/package references. NOT a Unity build or AI test."""
from pathlib import Path
import json,csv,collections,sys,datetime
ROOT=Path(__file__).resolve().parent.parent
errors=[]
def check(condition,label):
    if not condition: errors.append(label)
    else: print('PASS',label)
def j(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))
def csvrows(path):
    return list(csv.DictReader((ROOT/path).open('r',encoding='utf-8-sig',newline='')))
truth=j('01_CANON/CASE001_V21_TRUTH.json')
e=j('04_EVIDENCE/EVIDENCE_CHAIN_AND_REPORT.json')
events=j('06_EVENTS/CONDITIONAL_SURPRISE_EVENTS.json')
groups=j('05_PROPS/18_HOTSPOT_GROUPS.json')
ori=csvrows('05_PROPS/ORIGINAL_208_MANIFEST.csv')
cls=csvrows('05_PROPS/PROP_208_V21_CLASSIFICATION.csv')
qa=csvrows('09_TECH_QA/04_QA_MATRIX.csv')
check(truth['case_id']=='001' and truth['culprit_id']=='s3','CASE001 culprit must be s3 (Park)')
check('박현수' in str(truth['actors']['s3']),'s3 is Park')
check(len(truth['truth_events'])==27,'truth events =27')
factids=[f['fact_id'] for f in truth['truth_events']]
check(len(factids)==len(set(factids)),'unique fact IDs')
check(set(['F07','F14','F21']).issubset(factids),'distinct injury fact IDs exist')
check(len(e['evidence'])==19,'19 evidence entries')
eids={r['id'] for r in e['evidence']}
check(len(eids)==len(e['evidence']),'unique evidence IDs')
check(len(events['events'])==22,'22 surprise event entries')
check(len({r['event_id'] for r in events['events']})==22,'unique event IDs')
check(all(r.get('action_cost_of_event',0)==0 for r in events['events']),'no event charges hidden costs')
check(len(groups['groups'])==18,'18 hotspot groups')
check(len(ori)==208 and len(cls)==208,'208 original and classified rows')
oriid={r['prop_id'] for r in ori}
clsid={r['prop_id'] for r in cls}
check(oriid==clsid,'208 ID set preserved exactly')
check(len(oriid)==208 and len(clsid)==208,'all prop IDs unique')
valid={'CORE_HOTSPOT','CONTEXT_INTERACT','DECOR_STATIC','MERGE_INTERACTION','REMOVE_CANDIDATE'}
check(all(r['v21_disposition'] in valid for r in cls),'valid classification dispositions')
counts=collections.Counter(r['v21_disposition'] for r in cls)
print('Classification:',dict(counts))
check(counts=={'CORE_HOTSPOT':34,'CONTEXT_INTERACT':47,'DECOR_STATIC':91,'MERGE_INTERACTION':23,'REMOVE_CANDIDATE':13},'consistent 208 classifications')
check(all(all(id in oriid for id in g['prop_ids']) for g in groups['groups']),'every hotspot prop ID exists')
check(all(all(id in eids for id in g.get('primary_evidence_ids',[])) for g in groups['groups']),'every hotspot evidence ID exists')
check(all(all(id in oriid for id in ev['prop_ids']) for ev in e['evidence']),'every evidence prop ID exists')
check(all(all(id in eids for id in fact.get('evidence_ids',[])) for fact in truth['truth_events']),'every truth event evidence ID exists')
check(all(all(id in factids for id in kb.get('direct_fact_ids',[])) for kb in truth['suspect_knowledge_projection'].values()),'suspect knowledge fact references valid')
check(all(f['source_family'] for f in e['evidence']),'evidence provenance family declared')
check(all(len(r.get('could_support',''))>3 and len(r.get('does_not_prove',''))>3 for r in e['evidence']),'evidence has limits')
check(len(qa)>=100 and all(x['actual_result']=='NOT_RUN' for x in qa),'129 QA cases authored, not falsely marked executed')
mandatory=['00_START_HERE.md','01_CLAUDE_CODE_ULTIMATE_PROMPT.md','08_UI_UX/01_COMPLETE_GAME_UX_SPEC.md','08_UI_UX/02_SCREEN_WIREFRAMES.md','08_UI_UX/03_UI_FLOW_AND_COST_CONTRACT.json','08_UI_UX/04_CLICKABLE_UX_PROTOTYPE.html','09_TECH_QA/01_STORY_PROOF_AND_CASE_LOGIC.md','09_TECH_QA/02_ARCHITECTURE_CASE002_AND_ACCEPTANCE.md','09_TECH_QA/03_CONFLICTS_MIGRATION_AND_NONNEGOTIABLE.md','10_IMPLEMENTATION/01_ORDER_OF_WORK_AND_DOD.md']
check(all((ROOT/f).is_file() for f in mandatory),'mandatory instructions and UX prototype exist')
if errors:
    print('FAILED',len(errors));print('\n'.join(errors));sys.exit(1)
print('\nPASS: STATIC DATA CONSISTENCY ONLY. Actual Unity/LLM/STT/TTS/forensic gameplay tests NOT EXECUTED.')
