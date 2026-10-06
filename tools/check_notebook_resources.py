import ast
import io
import json
from pathlib import Path
import re
import tokenize

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {1: 'WordOccurrence.c', 2: 'MatrixOperations.c',
           3: 'PWCrack.cu', 4: 'SobelEdge.cu'}
UPLOADS = {1: ['WordOccurrenceDataset.txt'], 2: ['MatData.txt'],
           3: ['passwords.txt', 'expected_passwords.txt'],
           4: ['lodepng.cpp', 'lodepng.h']}


def c_tokens(source):
    pattern = r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*[\s\S]*?\*/|//[^\n]*|[A-Za-z_][A-Za-z_0-9]*|[0-9]+|\S'
    return [token for token in re.findall(pattern, source)
            if not token.startswith(('/*', '//'))]


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
               'base64' not in source and 'viva' not in source.lower() for source in sources)
    setup = sources[0]
    assert 'files.upload()' in setup and len(setup.splitlines()) <= 20
    assignments = ast.parse(setup).body
    required = next(ast.literal_eval(node.value) for node in assignments
                    if isinstance(node, ast.Assign) and
                    any(isinstance(target, ast.Name) and target.id == 'required'
                        for target in node.targets))
    assert required == UPLOADS[number]
    assert all((folder / name).is_file() for name in required)
    assert sources[1].split('\n', 1)[0] == '%%writefile ' + SOURCES[number]
    assert c_tokens(sources[1].split('\n', 1)[1]) == c_tokens(
        (folder / SOURCES[number]).read_text(encoding='utf-8'))
    assert sources[2].startswith('%%bash\nset -e\n')
    assert sources[3].startswith('%%bash\nset -e\n')
    for source in (sources[0], sources[4]):
        ast.parse(source)
        assert not any(token.type == tokenize.COMMENT
                       for token in tokenize.generate_tokens(io.StringIO(source).readline))
    if number == 4:
        assert 'wget' in setup and 'https://i.ibb.co/5gB80K0Z/download.png' in setup
        assert "'images/download.png'" in setup
        assert 'Gradient in X direction' in sources[4]
        assert 'Gradient in Y direction' in sources[4]
    assert content['metadata']['accelerator'] == 'GPU'
    assert content['metadata']['colab']['gpuType'] == 'T4'
    checked.append(path.name)
    print(f'PASS: {path.name}, five code cells, short uploads, unchanged algorithm tokens')

validation = ROOT.parent / 'working' / 'HPC_Validation.ipynb'
content = json.loads(validation.read_text(encoding='utf-8'))
assert len(content['cells']) == 3
for cell in content['cells']:
    assert cell['cell_type'] == 'code'
    source = ''.join(cell['source'])
    ast.parse(source)
    assert 'base64' not in source and 'viva' not in source.lower()
assert 'files.upload()' in ''.join(content['cells'][0]['source'])
print('PASS: development validation uses a project ZIP upload and three code cells')

result = {'status': 'PASS', 'notebooks': checked,
          'checked_resources': sum(len(names) for names in UPLOADS.values()),
          'checks': ['Five executable code cells in each task notebook',
                     'Short Colab file uploads with supplied resource filenames',
                     'C/CUDA tokens match the separate sources after comment removal',
                     'Notebook cells contain executable task code only',
                     'Python setup and display cells parse successfully',
                     'Development validation uses a project ZIP upload',
                     'Each notebook requests a T4 GPU runtime']}
output = ROOT / 'evidence' / 'resource_validation.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
