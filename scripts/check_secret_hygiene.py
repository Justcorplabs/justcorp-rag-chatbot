"""Read-only repository guard. Diagnostics contain generic rule identifiers only."""
import ast
import contextlib
import io
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_NAME = re.compile(
    r'(^|/)(?:\.env(?:\..*)?|[^/]+\.env(?:\..*)?|credentials\.json|'
    r'service[-_]account[^/]*\.json|id_(?:rsa|ed25519)(?![^/]*\.pub$)[^/]*|'
    r'[^/]+\.(?:key|p12|pfx|jks|keystore))$|'
    r'(^|/)(?:\.aws|\.secrets|secrets)/'
)
SIGNATURES = re.compile(
    r'-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----|'
    r'\b(?:gsk_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|'
    r'(?:AKIA|ASIA)[A-Z0-9]{16}|gh[pousr]_[A-Za-z0-9]{20,}|'
    r'github_pat_[A-Za-z0-9_]{20,}|EA[A-Za-z0-9]{70,})\b|'
    r'\b[a-z][a-z0-9+.-]*://[^\s/:@]+:[^\s/@]+@'
)
# Literal assignments only; expressions and computed values require other review.
TOKEN_ASSIGNMENT = re.compile(
    r'''(?i)["']?\b(?:[a-z0-9]+[_-])*(?:token|api[_-]?key|secret|password)["']?\s*[:=]\s*["']?([a-z0-9_/+\-=]{16,})(?=["'\s,}]|$)'''
)
SECRET_KEY = re.compile(r'KEY|TOKEN|SECRET|PASSWORD|PHONE_NUMBER_ID')
PRIVATE_PROBES = [
    '.env', 'backend/.env', 'frontend/.env', 'backend/.env.production',
    'frontend/.env.local', 'backend/.env.backup', 'local.env',
    'keys/private.pem', 'keys/private.key', 'keys/id_rsa', 'keys/id_ed25519',
    'keys/id_rsa.backup', 'keys/id_ed25519.old',
    'credentials.json', 'service-account-private.json', '.aws/credentials',
    'secrets/token.txt',
]
PUBLIC_PROBES = [
    '.env.example', 'backend/.env.example', 'frontend/.env.example',
    'local.env.example', '.env.development.example',
    'keys/id_rsa.pub', 'keys/id_ed25519.pub', 'keys/public.pub',
    'keys/public.pem', 'keys/certificate.pem',
]


MAX_FILE_BYTES = 1024 * 1024
MAX_CONFIG_CHARS = 64 * 1024
MAX_CONFIG_PUNCTUATION = 512
MAX_CONFIG_TOKENS = 2048
PUBLIC_PEM = re.compile(
    r'\s*-----BEGIN (PUBLIC KEY|RSA PUBLIC KEY|CERTIFICATE)-----\s+'
    r'[A-Za-z0-9+/=\s]+?-----END \1-----\s*'
)


def safe_public_pem(content):
    """Accept only complete public envelopes, without additional material."""
    position = 0
    while position < len(content):
        match = PUBLIC_PEM.match(content, position)
        if not match:
            return False
        position = match.end()
    return bool(position)


def parse_config(content):
    # Bound input and grammar punctuation before parsing: even unary chains
    # can exhaust CPython's parser before an AST can be inspected.
    if (len(content) > MAX_CONFIG_CHARS or
            sum(not (c.isalnum() or c.isspace() or c == '_') for c in content)
            > MAX_CONFIG_PUNCTUATION or
            sum(1 for _ in re.finditer(r'\w+|[^\w\s]', content)) > MAX_CONFIG_TOKENS):
        raise CheckFailure('configuration: parsing complexity limit exceeded')
    try:
        return ast.parse(content)
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        raise CheckFailure('configuration: invalid or excessive Python input') from None


class CheckFailure(Exception):
    """Controlled diagnostic only; never wrap exception text."""


def git(root, *args):
    try:
        return subprocess.run(['git', *args], cwd=root, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, check=False)
    except (OSError, subprocess.SubprocessError):
        raise CheckFailure('repository: Git command unavailable or failed') from None


def safe_placeholder(value):
    return not value or re.fullmatch(r'your_[a-z0-9_]+_here', value) is not None


def read_text(root, name):
    try:
        with (root / name).open('rb') as source:
            data = source.read(MAX_FILE_BYTES + 1)
    except OSError:
        raise CheckFailure('file: missing or unreadable') from None
    if len(data) > MAX_FILE_BYTES:
        raise CheckFailure('file: size limit exceeded')
    # Only known repository image formats are exempt from text decoding.
    suffix = Path(name).suffix.lower()
    if ((suffix == '.png' and data.startswith(b'\x89PNG\r\n\x1a\n')) or
            (suffix in {'.jpg', '.jpeg'} and data.startswith(b'\xff\xd8\xff'))):
        return None
    try:
        if data.startswith((b'\xff\xfe', b'\xfe\xff')):
            text = data.decode('utf-16')
        else:
            text = data.decode('utf-8-sig')
        if '\0' in text:
            raise ValueError
        return text
    except (UnicodeError, ValueError):
        raise CheckFailure('file: unsupported or malformed text encoding') from None


def main(root=ROOT):
    # Cover allocation failures throughout reading, decoding, regex scanning,
    # Git inventory handling, and AST inspection. Catch only resource errors;
    # unexpected programming errors must still surface.
    try:
        return scan(root)
    except (MemoryError, RecursionError):
        print('scanner: resource limit exceeded')
        return 1


def scan(root):
    failures = []
    try:
        result = git(root, 'ls-files', '-z')
        if result.returncode:
            raise CheckFailure('repository: tracked file listing failed')
        try:
            tracked = result.stdout.decode('utf-8').split('\0')
        except UnicodeError:
            raise CheckFailure('repository: unsupported filename encoding') from None
        for name in filter(None, tracked):
            if PRIVATE_NAME.search(name) and not name.endswith('.env.example') and not re.search(r'\.env\..+\.example$', name):
                failures.append('tracked-file: private credential filename')
            try:
                content = read_text(root, name)
            except CheckFailure as error:
                failures.append(str(error))
                continue
            if content is None:
                continue
            if Path(name).suffix.lower() == '.pem' and not safe_public_pem(content):
                failures.append('tracked-file: private or ambiguous PEM material')
            for number, line in enumerate(content.splitlines(), 1):
                if SIGNATURES.search(line) or any(
                    not safe_placeholder(match.group(1))
                    for match in TOKEN_ASSIGNMENT.finditer(line)
                ):
                    failures.append('tracked-file: credential signature')

        name = 'backend/app/config.py'
        try:
            content = read_text(root, name)
            if content is None:
                raise CheckFailure('configuration: invalid Python configuration')
            config = parse_config(content)
            backend_keys = {
                node.args[0].value for node in ast.walk(config)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name) and node.func.value.id == 'os'
                and node.func.attr == 'getenv' and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            }
            for name, expected in [('backend/.env.example', backend_keys),
                                   ('frontend/.env.example', {'VITE_API_BASE_URL'})]:
                content = read_text(root, name)
                if content is None:
                    raise CheckFailure('example: invalid example encoding')
                entries = []
                for number, line in enumerate(content.splitlines(), 1):
                    if not line.strip() or line.lstrip().startswith('#'):
                        continue
                    match = re.fullmatch(r'([A-Z][A-Z0-9_]*)=(.*)', line)
                    if not match:
                        failures.append('example: invalid example assignment')
                        continue
                    key, value = match.groups()
                    entries.append(key)
                    if SECRET_KEY.search(key) and not safe_placeholder(value):
                        failures.append('example: credential must be empty or a safe placeholder')
                if len(entries) != len(set(entries)) or set(entries) != expected:
                    failures.append('example: duplicate, missing, or unexpected variable names')
        except CheckFailure as error:
            failures.append(str(error))
        for probes, expected_code, rule in [
            (PRIVATE_PROBES, 0, 'ignore rule missing or check failed'),
            (PUBLIC_PROBES, 1, 'public file ignored or check failed'),
        ]:
            for name in probes:
                if git(root, 'check-ignore', '--no-index', '-q', name).returncode != expected_code:
                    failures.append(f'ignore-policy: {rule}')
    except CheckFailure as error:
        failures.append(str(error))
    for failure in failures:
        print(failure)
    if not failures:
        print('Secret hygiene checks passed (tracked working tree, examples, ignore rules).')
    return int(bool(failures))


def self_test():
    """Synthetic fixtures only, in temporary repositories; no production writes."""
    class RegressionTests(unittest.TestCase):
        def test_cases(self):
            sentinel = 'SYNTHETIC_' + 'SENTINEL_92837465'
            cases = [
                ('clean', None, None, 0),
                ('scanner-self-inclusion', 'scripts/check_secret_hygiene.py', Path(__file__).read_bytes(), 0),
                ('filename-signature', sentinel + '.txt', 'gsk_' + 'A' * 24, 1),
                ('filename-private', sentinel + '.key', 'public', 1),
                ('filename-missing', sentinel + '.txt', None, 1),
                ('filename-encoding', sentinel + '.txt', b'\xff', 1),
                ('unary-complexity', 'backend/app/config.py', 'x=' + '+' * 10000 + '1 # ' + sentinel, 1),
                ('keyword-complexity', 'backend/app/config.py', 'x=' + 'not ' * 10000 + '1 # ' + sentinel, 1),
                ('nested-complexity', 'backend/app/config.py', 'x=' + '(' * 10000 + '1' + ')' * 10000 + '# ' + sentinel, 1),
                ('config-size', 'backend/app/config.py', '# ' + sentinel + 'A' * MAX_CONFIG_CHARS, 1),
                ('file-size', 'probe.txt', sentinel + 'A' * MAX_FILE_BYTES, 1),
                ('parser-memory', None, None, 1),
                ('parser-recursion', None, None, 1),
                ('public-pem', 'keys/public.pem', '-----BEGIN PUBLIC KEY-----\nU1lOVEhFVElD\n-----END PUBLIC KEY-----\n', 0),
                ('certificate-pem', 'keys/certificate.pem', '-----BEGIN CERTIFICATE-----\nU1lOVEhFVElD\n-----END CERTIFICATE-----\n', 0),
                ('rsa-public-pem', 'keys/public.pem', '-----BEGIN RSA PUBLIC KEY-----\nU1lOVEhFVElD\n-----END RSA PUBLIC KEY-----\n', 0),
                ('private-pem', 'keys/unknown.pem', '-----BEGIN ' + 'PRIVATE KEY-----\n' + sentinel, 1),
                ('ambiguous-pem', 'keys/unknown.pem', sentinel, 1),
                ('mixed-pem', 'keys/public.pem', '-----BEGIN PUBLIC KEY-----\nU1lOVEhFVElD\n-----END PUBLIC KEY-----\n' + sentinel, 1),
                ('groq', 'probe.txt', 'gsk_' + 'A' * 24 + ' ' + sentinel, 1),
                ('openai', 'probe.txt', 'sk-' + 'A' * 24 + sentinel, 1),
                ('github', 'probe.txt', 'ghp_' + 'A' * 24 + ' ' + sentinel, 1),
                ('github-pat', 'probe.txt', 'github_' + 'pat_' + 'A' * 24 + sentinel, 1),
                ('aws', 'probe.txt', 'AKIA' + 'A' * 16 + ' ' + sentinel, 1),
                ('aws-temporary', 'probe.txt', 'ASIA' + 'A' * 16 + ' ' + sentinel, 1),
                ('meta', 'probe.txt', 'EA' + 'A' * 75 + ' ' + sentinel, 1),
                ('private-key', 'probe.txt', '-----BEGIN ' + 'PRIVATE KEY-----\n' + sentinel, 1),
                ('token', 'probe.txt', 'access_token="' + sentinel + '"', 1),
                ('json-token', 'probe.txt', '{"token": "' + sentinel + '"}', 1),
                ('syntax', 'backend/app/config.py', 'value = "' + sentinel, 1),
                ('assignment', 'backend/.env.example', 'TOKEN "' + sentinel, 1),
                ('missing', 'backend/app/config.py', None, 1),
                ('missing-example', 'backend/.env.example', None, 1),
                ('missing-tracked', 'probe.txt', None, 1),
                ('invalid-utf8', 'probe.txt', b'\xff' + sentinel.encode(), 1),
                ('utf16', 'probe.txt', ('token=' + sentinel).encode('utf-16'), 1),
                ('utf16-be', 'probe.txt', b'\xfe\xff' + ('token=' + sentinel).encode('utf-16-be'), 1),
                ('utf16-no-bom', 'probe.txt', ('token=' + sentinel).encode('utf-16-le'), 1),
                ('duplicate', 'backend/.env.example', 'TOKEN=\nTOKEN=\n', 1),
                ('unsafe-placeholder', 'backend/.env.example', 'TOKEN=unsafe_' + sentinel, 1),
                ('public-key', 'keys/id_rsa.pub', 'ssh-rsa SYNTHETICPUBLIC', 0),
                ('public-ed25519', 'keys/id_ed25519.pub', 'ssh-ed25519 SYNTHETICPUBLIC', 0),
                ('environment-example', 'local.env.example', 'VALUE=public', 0),
                ('ignored-secret', '.env', 'TOKEN=' + sentinel, 0),
                ('unreadable', 'probe.txt', 'public', 1),
                ('file-memory', 'probe.txt', 'public', 1),
                ('file-recursion', 'probe.txt', 'public', 1),
                ('config-read-memory', None, None, 1),
                ('git-failure', None, None, 1),
                ('git-unavailable', None, None, 1),
            ]
            for label, target, value, expected in cases:
                with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    def write(name, data):
                        path = root / name
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(data if isinstance(data, bytes) else data.encode())
                    write('.gitignore', (ROOT / '.gitignore').read_bytes())
                    write('backend/app/config.py', 'import os\nTOKEN = os.getenv("TOKEN")\n')
                    write('backend/.env.example', 'TOKEN=\n')
                    write('frontend/.env.example', 'VITE_API_BASE_URL=http://localhost:8000\n')
                    if target:
                        write(target, value if value is not None else 'public')
                    for args in [('init', '-q'), ('add', '.')]:
                        if git(root, *args).returncode:
                            self.fail('synthetic repository setup failed')
                    if label == 'filename-private':
                        if git(root, 'add', '-f', '--', target).returncode:
                            self.fail('synthetic private filename setup failed')
                    if target and value is None:
                        (root / target).unlink()
                    stdout, stderr = io.StringIO(), io.StringIO()
                    original_read = Path.open
                    def read(path, *args, **kwargs):
                        failure_target = ('backend/app/config.py'
                                          if label == 'config-read-memory' else 'probe.txt')
                        if path == root / failure_target:
                            error = (MemoryError if label in {'file-memory', 'config-read-memory'}
                                     else RecursionError if label == 'file-recursion'
                                     else PermissionError)
                            raise error(sentinel)
                        return original_read(path, *args, **kwargs)
                    patch = contextlib.nullcontext()
                    if label in {'unreadable', 'file-memory', 'file-recursion', 'config-read-memory'}:
                        patch = mock.patch.object(Path, 'open', read)
                    elif label in {'parser-memory', 'parser-recursion'}:
                        error = MemoryError if label == 'parser-memory' else RecursionError
                        patch = mock.patch.object(ast, 'parse', side_effect=error(sentinel))
                    elif label == 'git-failure':
                        patch = mock.patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 2, sentinel.encode(), sentinel.encode()))
                    elif label == 'git-unavailable':
                        patch = mock.patch.object(subprocess, 'run', side_effect=OSError(sentinel))
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr), patch:
                        actual = main(root)
                    # Never put captured output or credential fixtures in assertion messages.
                    self.assertTrue(sentinel not in stdout.getvalue(), 'stdout disclosure')
                    self.assertTrue(sentinel not in stderr.getvalue(), 'stderr disclosure')
                    self.assertEqual(actual, expected, 'unexpected exit code')
                    if label in {'file-memory', 'file-recursion', 'config-read-memory'}:
                        self.assertEqual(stdout.getvalue(), 'scanner: resource limit exceeded\n')
                        self.assertEqual(stderr.getvalue(), '')
                    if label in {'scanner-self-inclusion', 'file-memory', 'file-recursion', 'config-read-memory'}:
                        print(f'{label}: passed (exit {actual}; no sentinel in stdout/stderr)')
            print(f'Synthetic cases checked: {len(cases)}')
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(RegressionTests))
    return int(not result.wasSuccessful())


if __name__ == '__main__':
    sys.exit(self_test() if sys.argv[1:] == ['--self-test'] else main())
