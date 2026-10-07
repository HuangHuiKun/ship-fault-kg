"""Check the user's repository, create privately, or explicitly publish it.

No token arguments, logging, files or interactive credential creation. Authenticate
with Git Credential Manager separately if the non-interactive lookup fails.
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request


def validate_repository(repo, owner, name, expected_visibility='any'):
    if (repo.get('owner', {}).get('login', '').lower() != owner.lower()
            or repo.get('full_name', '').lower() != f'{owner}/{name}'.lower()):
        raise RuntimeError('Unexpected repository identity; nothing changed.')
    if not isinstance(repo.get('private'), bool):
        raise RuntimeError('Repository visibility unavailable; nothing changed.')
    visibility = 'private' if repo['private'] else 'public'
    if expected_visibility != 'any' and visibility != expected_visibility:
        raise RuntimeError('Repository visibility differs from the requested check.')
    return visibility


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--create', action='store_true')
    parser.add_argument('--owner', default='HuangHuiKun')
    parser.add_argument('--name', default='ship-fault-kg')
    parser.add_argument('--expect-visibility', choices=['any', 'private', 'public'], default='any')
    parser.add_argument('--make-public', action='store_true',
        help='Publish an existing repository; requires --confirm-public OWNER/REPO')
    parser.add_argument('--confirm-public')
    args = parser.parse_args()
    if args.create and args.make_public:
        parser.error('Creation and publication are separate operations.')
    if args.make_public and args.confirm_public != f'{args.owner}/{args.name}':
        parser.error('Publication requires exact repository confirmation.')
    if args.confirm_public and not args.make_public:
        parser.error('--confirm-public requires --make-public.')
    if args.make_public and args.expect_visibility == 'private':
        parser.error('Cannot publish and require private visibility.')
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never')
    try:
        result = subprocess.run(['git', 'credential', 'fill'],
            input='protocol=https\nhost=github.com\n\n', text=True,
            capture_output=True, env=env, timeout=20)
    except subprocess.TimeoutExpired:
        print('BLOCKED: Git credential lookup timed out; no credential was printed.')
        return 2
    credentials = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    token = credentials.get('password')
    if result.returncode or not token:
        print('BLOCKED: No usable non-interactive GitHub credential in Git Credential Manager.')
        return 2

    def request(path, payload=None, method=None):
        data = None if payload is None else json.dumps(payload).encode('utf-8')
        req = urllib.request.Request('https://api.github.com' + path, data=data, method=method,
            headers={'Authorization': 'Bearer ' + token,
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2026-03-10',
                'Content-Type': 'application/json', 'User-Agent': 'ship-fault-kg-versioning'})
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)

    try:
        user = request('/user')
        if user['login'].lower() != args.owner.lower():
            print('BLOCKED: Stored Git credential belongs to a different account; nothing created.')
            return 2
        created = False
        try:
            repo = request(f'/repos/{args.owner}/{args.name}')
        except urllib.error.HTTPError as exc:
            if exc.code != 404 or not args.create:
                raise
            repo = request('/user/repos', {'name': args.name, 'private': True,
                'auto_init': False,
                'description': '船舶动力系统故障知识图谱：构建、溯源、Neo4j、RAG检索实验及研究资料'})
            created = True
        validate_repository(repo, args.owner, args.name)
        changed = False
        if args.make_public and repo['private']:
            if not repo.get('permissions', {}).get('admin'):
                raise RuntimeError('Repository administrator permission is required.')
            request(f'/repos/{args.owner}/{args.name}', {'private': False}, method='PATCH')
            repo = request(f'/repos/{args.owner}/{args.name}')
            validate_repository(repo, args.owner, args.name, 'public')
            changed = True
        visibility = validate_repository(repo, args.owner, args.name, args.expect_visibility)
        print(json.dumps({'created': created, 'private': repo['private'],
            'visibility': visibility, 'visibility_changed': changed,
            'full_name': repo['full_name'], 'html_url': repo['html_url'],
            'clone_url': repo['clone_url'], 'default_branch': repo['default_branch']}, ensure_ascii=False))
        return 0
    except urllib.error.HTTPError as exc:
        print(f'BLOCKED: GitHub API HTTP {exc.code}; no token or response body printed.')
        return 2
    except urllib.error.URLError:
        print('BLOCKED: Could not reach GitHub API securely; no credentials printed.')
        return 2
    except RuntimeError as exc:
        print('BLOCKED: ' + str(exc))
        return 2


if __name__ == '__main__':
    sys.exit(main())
