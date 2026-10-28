import httpx
import sys

BASE = 'http://127.0.0.1:8000'

def test_all():
    client = httpx.Client(base_url=BASE, timeout=60.0)
    
    print('1. Checking Health...')
    r = client.get('/api/health')
    assert r.status_code == 200, f'Health failed: {r.text}'
    print('   Health OK:', r.json())
    
    print('2. Creating Case with raw_text decomposition...')
    r = client.post('/api/cases', json={
        'title': 'Distributed CockroachDB Migration',
        'raw_text': 'We should migrate from monolithic Postgres to CockroachDB to improve availability and reduce maintenance overhead.'
    })
    assert r.status_code == 201, f'Create case failed: {r.text}'
    case = r.json()
    case_id = case['case_id']
    print(f'   Case created: {case_id}, state: {case.get("state")}')
    
    print('3. Fetching Case Details...')
    r = client.get(f'/api/cases/{case_id}')
    assert r.status_code == 200, f'Get case failed: {r.text}'
    print('   Case fetched successfully.')
    
    print('4. Running Court Proceedings...')
    r = client.post(f'/api/cases/{case_id}/court/start')
    assert r.status_code == 200, f'Court run failed: {r.text}'
    court_res = r.json()
    verdict = court_res.get("verdict", {}).get("verdict")
    print(f'   Court execution finished! Verdict: {verdict}')
    
    print('5. Fetching Verdict...')
    r = client.get(f'/api/cases/{case_id}/verdict')
    assert r.status_code == 200, f'Get verdict failed: {r.text}'
    print('   Verdict fetched successfully.')
    
    print('6. Fetching Findings & Arguments...')
    r = client.get(f'/api/cases/{case_id}/findings')
    assert r.status_code == 200, f'Get findings failed: {r.text}'
    findings = r.json()
    print(f'   Findings count: args={len(findings.get("arguments", []))}, cross_exams={len(findings.get("cross_examinations", []))}')
    
    print('7. Human-in-the-Loop Review...')
    r = client.post(f'/api/cases/{case_id}/review', json={
        'reviewer_id': 'lead_architect',
        'action': 'ACCEPT',
        'notes': 'Verified and approved with the mitigations.'
    })
    assert r.status_code == 200, f'Human review failed: {r.text}'
    print('   Human review submitted.')
    
    print('8. What-If Sensitivity Analysis...')
    r = client.post(f'/api/cases/{case_id}/what-if', json={
        'condition': 'Staff retraining takes 6 months instead of 0',
        'variable_changed': 'Retraining timeline'
    })
    assert r.status_code == 200, f'What-if failed: {r.text}'
    print('   What-if analysis finished.')
    
    print('9. Listing Cases...')
    r = client.get('/api/cases')
    assert r.status_code == 200, f'List cases failed: {r.text}'
    print(f'   Cases listed: {len(r.json())} cases found.')
    
    print('\n=========================================')
    print('ALL 9 ENDPOINTS PASSED SUCCESSFULLY!')
    print('=========================================')

if __name__ == '__main__':
    test_all()

