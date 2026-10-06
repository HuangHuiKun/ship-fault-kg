"""Create/check the user's private repository using existing Git credentials.

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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--create', action='store_true')
    parser.add_argument('--owner', default='HuangHuiKun')
    parser.add_argument('--name', default='ship-fault-kg')
    args = parser.parse_args()
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

    def request(path, payload=None):
        data = None if payload is None else json.dumps(payload).encode('utf-8')
        req = urllib.request.Request('https://api.github.com' + path, data=data,
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
        if not repo.get('private') or repo['owner']['login'].lower() != args.owner.lower():
            print('BLOCKED: Repository is not private or not owned by the expected user; do not push.')
            return 2
        print(json.dumps({'created': created, 'private': repo['private'],
            'full_name': repo['full_name'], 'html_url': repo['html_url'],
            'clone_url': repo['clone_url'], 'default_branch': repo['default_branch']}, ensure_ascii=False))
        return 0
    except urllib.error.HTTPError as exc:
        print(f'BLOCKED: GitHub API HTTP {exc.code}; no token or response body printed.')
        return 2
    except urllib.error.URLError:
        print('BLOCKED: Could not reach GitHub API securely; no credentials printed.')
        return 2


if __name__ == '__main__':
    sys.exit(main())
