"""Read-only verification of this private GitHub backup, including LFS objects.

Uses existing Git Credential Manager credentials only. Never prints tokens,
authorization headers or signed LFS download URLs. Does not create/push anything.
"""
import base64
import hashlib
import json
import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.request

OWNER = 'HuangHuiKun'
REPO = 'ship-fault-kg'
ORIGIN = f'https://github.com/{OWNER}/{REPO}.git'
BASELINE = 'shipkg-v3-baseline-20261006'


def git(*args):
    result = subprocess.run(['git', *args], text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError('Git command failed: ' + ' '.join(args[:3]))
    return result.stdout.strip()


def main():
    if git('remote', 'get-url', 'origin') != ORIGIN:
        raise RuntimeError('Unexpected origin; refuse sending credentials elsewhere')
    if git('status', '--porcelain'):
        raise RuntimeError('Uncommitted files: commit/review before verifying full backup')
    credential = subprocess.run(['git', 'credential', 'fill'],
        input='protocol=https\nhost=github.com\n\n', text=True, capture_output=True,
        env=dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never'), timeout=20)
    fields = dict(line.split('=', 1) for line in credential.stdout.splitlines() if '=' in line)
    token = fields.get('password')
    if credential.returncode or not token:
        raise RuntimeError('GitHub credential unavailable; authenticate locally first')

    def api(path):
        req = urllib.request.Request('https://api.github.com' + path,
            headers={'Authorization': 'Bearer ' + token,
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2026-03-10', 'User-Agent': 'shipkg-backup-verification'})
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)

    print('Checking GitHub identity and private repository...', flush=True)
    user = api('/user')
    if user['login'].lower() != OWNER.lower():
        raise RuntimeError('Stored Git credential belongs to a different account')
    metadata = api(f'/repos/{OWNER}/{REPO}')
    if not metadata['private']:
        raise RuntimeError('Remote repository is not private')
    print('Checking remote main and baseline tag...', flush=True)
    local = git('rev-parse', 'HEAD')
    remote = git('ls-remote', '--heads', 'origin', 'refs/heads/main').split()[0]
    if remote != local:
        raise RuntimeError('Local HEAD does not match remote main')
    tag_local = git('rev-parse', BASELINE + '^{}')
    tag_rows = git('ls-remote', '--tags', 'origin', 'refs/tags/' + BASELINE + '*').splitlines()
    tag_remote = next((line.split()[0] for line in tag_rows if line.endswith('^{}')), None)
    if tag_local != tag_remote:
        raise RuntimeError('Remote baseline tag missing or different')

    files = json.loads(git('lfs', 'ls-files', '--json'))['files']
    objects = {row['oid']: {'oid': row['oid'], 'size': row['size']} for row in files}
    oid_list = list(objects)
    available = {}
    basic = base64.b64encode((user['login'] + ':' + token).encode()).decode()
    for offset in range(0, len(oid_list), 100):
        print(f'Checking remote LFS objects {offset + 1}-{min(offset + 100, len(oid_list))}...', flush=True)
        selection = oid_list[offset:offset + 100]
        payload = {'operation': 'download', 'transfers': ['basic'],
            'objects': [objects[oid] for oid in selection]}
        req = urllib.request.Request(ORIGIN + '/info/lfs/objects/batch',
            data=json.dumps(payload).encode(), headers={
                'Authorization': 'Basic ' + basic,
                'Accept': 'application/vnd.git-lfs+json',
                'Content-Type': 'application/vnd.git-lfs+json',
                'User-Agent': 'shipkg-backup-verification'})
        with urllib.request.urlopen(req, timeout=60) as response:
            batch = json.load(response)
        rows = batch.get('objects', [])
        if {row['oid'] for row in rows} != set(selection):
            raise RuntimeError('Unexpected/missing objects in LFS server response')
        for row in rows:
            if row.get('error') or row['size'] != objects[row['oid']]['size'] or not row.get('actions', {}).get('download'):
                raise RuntimeError('An LFS object is missing or not downloadable')
            available[row['oid']] = row

    # Download one real graph snapshot, not just its tiny Git pointer, and check
    # its SHA-256. Do not print the signed download URL or persist its headers.
    print('Downloading remote SQLite sample for SHA-256 verification...', flush=True)
    snapshot = next(row for row in files if row['name'] == 'ship_fault_kg/output/ship_fault_kg.sqlite')
    action = available[snapshot['oid']]['actions']['download']
    req = urllib.request.Request(action['href'], headers=action.get('header', {}))
    digest, size = hashlib.sha256(), 0
    with urllib.request.urlopen(req, timeout=60) as response:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    if digest.hexdigest() != snapshot['oid'] or size != snapshot['size']:
        raise RuntimeError('Remote SQLite download hash/size mismatch')
    print(json.dumps({'result': 'PASS', 'repository': metadata['html_url'], 'private': True,
        'local_head': local, 'remote_main': remote, 'baseline_tag': BASELINE,
        'baseline_commit': tag_remote, 'tracked_files': len(git('ls-files').splitlines()),
        'lfs_files': len(files), 'lfs_unique_objects_available': len(available),
        'lfs_unique_bytes': sum(row['size'] for row in objects.values()),
        'remote_sqlite_sha256_verified': True, 'worktree_clean': True}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print(f'FAIL: HTTP {exc.code}; credentials/URLs/response body omitted.')
        sys.exit(2)
    except urllib.error.URLError as exc:
        reason = exc.reason
        detail = type(reason).__name__
        if isinstance(reason, ssl.SSLCertVerificationError):
            detail += ': TLS verification code ' + str(reason.verify_code)
        elif getattr(reason, 'errno', None) is not None:
            detail += ': errno ' + str(reason.errno)
        print('FAIL: Secure connection unavailable (' + detail + '); credentials/URLs omitted.')
        sys.exit(2)
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print('FAIL: ' + str(exc) if isinstance(exc, RuntimeError) else 'FAIL: Command timed out.')
        sys.exit(2)
