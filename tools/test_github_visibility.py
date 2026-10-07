"""Offline checks; mock credentials and GitHub requests, never publish a repo."""
import contextlib
import io
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

import github_private_repo as subject


def metadata(private=True, admin=True, owner='HuangHuiKun', name='ship-fault-kg'):
    return {'private': private, 'owner': {'login': owner},
            'full_name': f'{owner}/{name}', 'permissions': {'admin': admin},
            'html_url': f'https://github.com/{owner}/{name}',
            'clone_url': f'https://github.com/{owner}/{name}.git', 'default_branch': 'main'}


class GithubVisibilityTests(unittest.TestCase):
    def run_cli(self, args, initial=None):
        current = metadata() if initial is None else dict(initial)
        calls = []

        def request(req, **kwargs):
            calls.append((req.get_method(), req.full_url, req.data))
            if req.full_url.endswith('/user'):
                body = {'login': 'HuangHuiKun'}
            else:
                if req.get_method() == 'PATCH':
                    current['private'] = json.loads(req.data)['private']
                body = current
            return io.BytesIO(json.dumps(body).encode())

        credential = subprocess.CompletedProcess([], 0, stdout='password=TEST_CREDENTIAL\n', stderr='')
        output = io.StringIO()
        with patch.object(sys, 'argv', ['github_private_repo.py', *args]), \
                patch.object(subject.subprocess, 'run', return_value=credential), \
                patch.object(subject.urllib.request, 'urlopen', side_effect=request), \
                contextlib.redirect_stdout(output):
            result = subject.main()
        self.assertNotIn('TEST_CREDENTIAL', output.getvalue())
        return result, calls, output.getvalue()

    def test_metadata_accepts_public_and_private(self):
        self.assertEqual(subject.validate_repository(metadata(), 'HuangHuiKun', 'ship-fault-kg'), 'private')
        self.assertEqual(subject.validate_repository(metadata(False), 'HuangHuiKun', 'ship-fault-kg'), 'public')

    def test_wrong_owner_name_or_visibility_rejected(self):
        for row in [metadata(owner='Other'), metadata(name='other')]:
            with self.assertRaises(RuntimeError):
                subject.validate_repository(row, 'HuangHuiKun', 'ship-fault-kg')
        with self.assertRaises(RuntimeError):
            subject.validate_repository(metadata(), 'HuangHuiKun', 'ship-fault-kg', 'public')

    def test_default_public_check_never_mutates(self):
        result, calls, output = self.run_cli([], metadata(False))
        self.assertEqual(result, 0)
        self.assertTrue(all(method == 'GET' for method, _, _ in calls))
        self.assertFalse(json.loads(output)['private'])

    def test_publish_requires_exact_confirmation_before_credentials(self):
        with patch.object(sys, 'argv', ['tool', '--make-public']), \
                patch.object(subject.subprocess, 'run') as credential, \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                subject.main()
        credential.assert_not_called()

    def test_explicit_publication_patches_only_private_setting(self):
        result, calls, output = self.run_cli(['--make-public', '--confirm-public',
                                            'HuangHuiKun/ship-fault-kg', '--expect-visibility', 'public'])
        self.assertEqual(result, 0)
        mutations = [(url, json.loads(body)) for method, url, body in calls if method != 'GET']
        self.assertEqual(mutations, [('https://api.github.com/repos/HuangHuiKun/ship-fault-kg', {'private': False})])
        self.assertTrue(json.loads(output)['visibility_changed'])
        self.assertFalse(json.loads(output)['private'])

    def test_publication_is_idempotent(self):
        result, calls, output = self.run_cli(['--make-public', '--confirm-public',
                                            'HuangHuiKun/ship-fault-kg'], metadata(False))
        self.assertEqual(result, 0)
        self.assertTrue(all(method == 'GET' for method, _, _ in calls))
        self.assertFalse(json.loads(output)['visibility_changed'])

    def test_missing_admin_refuses_publication(self):
        result, calls, _ = self.run_cli(['--make-public', '--confirm-public',
                                       'HuangHuiKun/ship-fault-kg'], metadata(admin=False))
        self.assertEqual(result, 2)
        self.assertTrue(all(method == 'GET' for method, _, _ in calls))


if __name__ == '__main__':
    unittest.main()
