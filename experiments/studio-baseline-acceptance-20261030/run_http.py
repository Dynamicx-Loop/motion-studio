"""Run the full official-default G1 cohort exclusively through local Studio HTTP.

Start the final-code Studio service with host CUDA and a fresh state directory
first. --evidence must be a fresh directory; inputs and old runs are never edited.
"""
import argparse
import json
from pathlib import Path
import time
import urllib.request
from urllib.parse import urlsplit

CHECKOUT = Path('/data/workspace/motion_studio/externals/UMR')
SOURCE = CHECKOUT / 'sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz'
SETTINGS = {'sampling_seed': 0, 'epochs': 500, 'trajectory_filter': 'LQR'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8900')
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    parsed = urlsplit(args.url)
    if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1':
        parser.error('Use the printed IPv4 loopback HTTP service URL')
    args.evidence.mkdir(parents=True, exist_ok=False)
    events = []

    def save(name, value):
        (args.evidence / name).write_text(json.dumps(value, indent=2) + '\n')

    def request(path, body=None):
        started = time.monotonic()
        req = urllib.request.Request(args.url + path,
            None if body is None else json.dumps(body).encode(),
            {} if body is None else {'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=900) as response:
            result = json.load(response)
        events.append({'method': 'GET' if body is None else 'POST', 'path': path,
                       'body': body, 'elapsed_seconds': time.monotonic() - started})
        save('http-events.json', events)
        return result

    robot = request('/api/robots', {'source_path': str(CHECKOUT / 'assets/g1/g1_29dof.xml'),
                                   'derive_free_root': True})
    pose = request(f"/api/robots/{robot['asset_id']}/official-pose")
    run = request('/api/runs', {'name': 'Final reviewed G1 full 5468-frame official-default acceptance'})
    run_id = run['run_id']
    run = request(f'/api/runs/{run_id}/robot-pose', {'asset_id': robot['asset_id'],
        'name': pose['name'], 'qpos': pose['qpos'], 'torso_body': pose['torso_body']})
    motion = request('/api/motions', {'source_path': str(SOURCE), 'metadata': {}})
    assert motion['frame_count'] == 5468
    run = request(f'/api/runs/{run_id}/motion', {'asset_id': motion['asset_id']})
    request('/api/selection', {'run_id': run_id})
    payload = {'through': 'retargeting', 'settings': SETTINGS}
    plan = request(f'/api/runs/{run_id}/plan', payload)
    save('launch-plan.json', plan)
    assert plan['ready'] and plan['stages'] == ['sampling', 'training', 'binding', 'retargeting']
    save('inputs.json', {'robot': robot, 'pose': pose, 'motion': motion, 'run': run})
    job = request(f'/api/runs/{run_id}/execute', payload)
    save('launched-job.json', job)
    observations = []
    while True:
        job = request('/api/jobs/' + job['job_id'])
        observations.append(job)
        print(json.dumps({key: job.get(key) for key in ('job_id', 'status', 'stage', 'progress')}), flush=True)
        if job['status'] not in ('queued', 'running', 'cancelling'):
            break
        time.sleep(5)
    save('job-observations.json', observations)
    save('completed-job.json', job)
    assert job['status'] == 'completed', job['message']
    receipts = {stage: request(f"/api/runs/{run_id}/revisions/{run['revision_id']}/stages/{stage}/receipt")
                for stage in ('sampling', 'training', 'binding', 'retargeting')}
    save('receipts.json', receipts)
    exports = []
    for stage in ('sampling', 'training', 'binding', 'motion'):
        started = time.monotonic()
        result = request(f'/api/runs/{run_id}/inspections/{stage}', {'revision_id': run['revision_id']})
        result['elapsed_seconds'] = time.monotonic() - started
        exports.append(result)
        save('exports.json', exports)
        print(json.dumps(result), flush=True)
    save('completed-state.json', request('/api/state'))


if __name__ == '__main__':
    main()
