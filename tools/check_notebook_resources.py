import ast
import io
import json
from pathlib import Path
import re
import tokenize

ROOT = Path(__file__).resolve().parents[1]
RESOURCE_COMMIT = '2ae868943d23e75e6a6cf5c2a7420c23cf15872b'
SOURCES = {1: 'WordOccurrence.c', 2: 'MatrixOperations.c',
           3: 'PWCrack.cu', 4: 'SobelEdge.cu'}
RESOURCES = {1: ['WordOccurrenceDataset.txt'], 2: ['MatData.txt'],
             3: ['passwords.txt', 'expected_passwords.txt'],
             4: ['lodepng.cpp', 'lodepng.h', 'images/download.png']}


def c_tokens(source):
    pattern = r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*[\s\S]*?\*/|//[^\n]*|[A-Za-z_][A-Za-z_0-9]*|[0-9]+|\S'
    return [token for token in re.findall(pattern, source)
            if not token.startswith(('/*', '//'))]


def assignment(tree, name):
    return next(ast.literal_eval(node.value) for node in tree.body
                if isinstance(node, ast.Assign) and
                any(isinstance(target, ast.Name) and target.id == name
                    for target in node.targets))


def check_python(source):
    tree = ast.parse(source)
    assert not any(token.type == tokenize.COMMENT
                   for token in tokenize.generate_tokens(io.StringIO(source).readline))
    assert all(marker not in source for marker in
               ('files.upload', 'drive.mount', 'RESOURCE_COPY', 'RESOURCE_SHA256', 'base64'))
    downloads = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and
                 isinstance(node.func, ast.Name) and node.func.id == 'urlopen']
    for call in downloads:
        assert any(keyword.arg == 'timeout' and ast.literal_eval(keyword.value) == 30
                   for keyword in call.keywords)
    return tree, downloads


checked = []
for number in range(1, 5):
    folder = ROOT / 'Practical Task' / f'Task {number:02d}'
    path = folder / f'Task_{number:02d}.ipynb'
    content = json.loads(path.read_text(encoding='utf-8'))
    cells = content['cells']
    assert len(cells) == 5 and all(cell['cell_type'] == 'code' for cell in cells)
    assert len({cell['id'] for cell in cells}) == len(cells)
    sources = [''.join(cell['source']) for cell in cells]
    assert all('RESOURCE_COPY' not in source and 'RESOURCE_SHA256' not in source and
               'base64' not in source and 'viva' not in source.lower() and
               'files.upload' not in source for source in sources)
    setup = sources[0]
    tree, downloads = check_python(setup)
    assert len(setup.splitlines()) <= 15 and len(downloads) == 1
    base = f'https://raw.githubusercontent.com/sahl-2003/HPC/{RESOURCE_COMMIT}/Practical%20Task/Task%20{number:02d}/'
    assert assignment(tree, 'base') == base
    assert assignment(tree, 'resources') == RESOURCES[number]
    assert all((folder / name).is_file() for name in RESOURCES[number])
    assert f"folder = Path('/content/Task_{number:02d}')" in setup
    assert 'folder.mkdir(parents=True, exist_ok=True)' in setup
    assert 'destination.parent.mkdir(parents=True, exist_ok=True)' in setup
    assert 'os.chdir(folder)' in setup
    assert 'urlopen(base + name, timeout=30)' in setup
    assert 'destination.write_bytes(response.read())' in setup
    assert sources[1].split('\n', 1)[0] == '%%writefile ' + SOURCES[number]
    assert c_tokens(sources[1].split('\n', 1)[1]) == c_tokens(
        (folder / SOURCES[number]).read_text(encoding='utf-8'))
    assert sources[2].startswith('%%bash\nset -e\n')
    assert sources[3].startswith('%%bash\nset -e\n')
    check_python(sources[4])
    if number == 4:
        assert 'Gradient in X direction' in sources[4]
        assert 'Gradient in Y direction' in sources[4]
    assert content['metadata']['accelerator'] == 'GPU'
    assert content['metadata']['colab']['gpuType'] == 'T4'
    checked.append(path.name)
    print(f'PASS: {path.name}, T4 GPU, five code cells, automatic public resources, unchanged algorithm tokens')

validation = ROOT / 'tools' / 'HPC_Validation.ipynb'
content = json.loads(validation.read_text(encoding='utf-8'))
assert len(content['cells']) == 3
assert len({cell['id'] for cell in content['cells']}) == 3
for cell in content['cells']:
    assert cell['cell_type'] == 'code'
    source = ''.join(cell['source'])
    check_python(source)
    assert 'viva' not in source.lower()
setup = ''.join(content['cells'][0]['source'])
tree, downloads = check_python(setup)
assert len(downloads) == 1
assert ast.literal_eval(downloads[0].args[0]) == f'https://codeload.github.com/sahl-2003/HPC/zip/{RESOURCE_COMMIT}'
assert 'destination.mkdir(parents=True, exist_ok=True)' in setup
assert 'archive.extractall(destination)' in setup
assert "verifier = next(destination.rglob('tools/verify.py'))" in setup
assert content['metadata']['accelerator'] == 'GPU'
assert content['metadata']['colab']['gpuType'] == 'T4'
working_validation = ROOT.parent / 'working' / 'HPC_Validation.ipynb'
if working_validation.exists():
    assert validation.read_bytes() == working_validation.read_bytes()
print('PASS: repository validation helper automatically downloads the pinned project ZIP')

result = {'status': 'PASS', 'notebooks': checked, 'resource_commit': RESOURCE_COMMIT,
          'checked_resources': sum(len(names) for names in RESOURCES.values()),
          'checks': ['Five executable code cells in each task notebook',
                     'Public pinned GitHub resource URLs with a 30-second timeout',
                     'Automatic downloads create required runtime folders and files',
                     'C/CUDA tokens match the separate sources after comment removal',
                     'Notebook cells contain executable task code only',
                     'Python setup and display cells parse successfully',
                     'Published repository validation helper downloads the pinned source ZIP',
                     'T4 GPU metadata for all four tasks']}
output = ROOT / 'evidence' / 'resource_validation.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
