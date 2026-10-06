from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
TASKS = ROOT / 'Practical Task'
SOURCES = {1: 'WordOccurrence.c', 2: 'MatrixOperations.c',
           3: 'PWCrack.cu', 4: 'SobelEdge.cu'}
UPLOADS = {1: ['WordOccurrenceDataset.txt'], 2: ['MatData.txt'],
           3: ['passwords.txt', 'expected_passwords.txt'],
           4: ['lodepng.cpp', 'lodepng.h']}


def strip_c_comments(source):
    pattern = r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*[\s\S]*?\*/|//[^\n]*'

    def replace(match):
        text = match.group(0)
        if not text.startswith('/'):
            return text
        if 'copyright' in text.lower() or 'license' in text.lower() or 'licence' in text.lower():
            return text
        return ' ' + '\n' * text.count('\n')

    cleaned = re.sub(pattern, replace, source)
    return re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+', '\n\n',
                  '\n'.join(line.rstrip() for line in cleaned.splitlines())) + '\n'


def cell(source, identifier):
    return {'cell_type': 'code', 'id': identifier, 'metadata': {},
            'source': source.splitlines(keepends=True),
            'execution_count': None, 'outputs': []}


def notebook(cells):
    return {'nbformat': 4, 'nbformat_minor': 5, 'metadata': {
        'accelerator': 'GPU', 'colab': {'provenance': [], 'gpuType': 'T4'},
        'kernelspec': {'name': 'python3', 'display_name': 'Python 3'},
        'language_info': {'name': 'python'}}, 'cells': cells}


def preserve_outputs(cells, previous):
    for new in cells:
        for old in previous.get('cells', []):
            if old.get('cell_type') != 'code':
                continue
            before, after = ''.join(old['source']), ''.join(new['source'])
            if before.startswith('%%writefile ') and after.startswith('%%writefile '):
                before = before.split('\n', 1)[0] + '\n' + strip_c_comments(before.split('\n', 1)[1])
            if before == after:
                new['execution_count'] = old.get('execution_count')
                new['outputs'] = old.get('outputs', [])
                break


def build_task(number):
    folder = TASKS / f'Task {number:02d}'
    path = folder / f'Task_{number:02d}.ipynb'
    previous = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    setup = f'''from pathlib import Path
from google.colab import files
import os

folder = Path('/content/Task_{number:02d}')
folder.mkdir(parents=True, exist_ok=True)
os.chdir(folder)
uploaded = files.upload()
required = {UPLOADS[number]!r}
assert all(Path(name).is_file() for name in required), 'Upload: ' + ', '.join(required)
'''
    if number == 4:
        setup += '''
import subprocess
import hashlib
Path('images').mkdir(exist_ok=True)
subprocess.run(['wget', '--timeout=20', '--tries=2', '-q', '-O', 'images/download.png',
                'https://i.ibb.co/5gB80K0Z/download.png'], check=True)
assert hashlib.sha256(Path('images/download.png').read_bytes()).hexdigest() == 'bea2b0c28430f63466123f3db2d5f4b5d1a932aade1727d130bf318a490b6309'
'''
    compile_code = {
        1: 'gcc -std=c11 -O2 -Wall -Wextra -Wpedantic -pthread WordOccurrence.c -o WordOccurrence',
        2: 'gcc -std=c11 -O2 -Wall -Wextra -Wpedantic -fopenmp MatrixOperations.c -lm -o MatrixOperations',
        3: 'nvcc -O2 -lineinfo -arch=sm_75 -Xcompiler=-Wall,-Wextra PWCrack.cu -o PWCrack',
        4: 'nvcc -O2 -lineinfo -arch=sm_75 -Xcompiler=-Wall,-Wextra lodepng.cpp SobelEdge.cu -o SobelEdge'}[number]
    run_code = {
        1: './WordOccurrence WordOccurrenceDataset.txt 4',
        2: './MatrixOperations MatData.txt 4',
        3: './PWCrack passwords.txt',
        4: 'mkdir -p outputs\n./SobelEdge outputs images/download.png | tee task4_public_run.log\ntest ${PIPESTATUS[0]} -eq 0'}[number]
    displays = {
        1: "print(Path('result.txt').read_text())",
        2: "text = Path('results.txt').read_text()\nprint(text[:12000])\nprint('Complete output is saved in results.txt.')",
        3: "encrypted = Path('passwords.txt').read_text().splitlines()\nraw = Path('decrypted.txt').read_text().splitlines()\nassert raw == Path('expected_passwords.txt').read_text().splitlines()\nfor i, (a, b) in enumerate(zip(encrypted[:10], raw[:10]), 1):\n    print(f'{i}: {a} -> {b}')\nprint('All', len(raw), 'passwords match the known originals.')",
        4: "from PIL import Image\nimport matplotlib.pyplot as plt\nname = 'download.png'\nfig, axes = plt.subplots(2, 2, figsize=(12, 7))\nviews = [('Original Image', Path('images') / name),\n         ('Gradient in X direction', Path('outputs') / ('outImg_Gx_' + name)),\n         ('Gradient in Y direction', Path('outputs') / ('outImg_Gy_' + name)),\n         ('Sobel Edge Detection', Path('outputs') / ('outImg_' + name))]\nfor ax, (title, path) in zip(axes.flat, views):\n    ax.imshow(Image.open(path).convert('RGBA'))\n    ax.set_title(title)\n    ax.axis('off')\nfig.suptitle(name)\nplt.tight_layout()\nplt.show()"}[number]
    cells = [
        cell(setup, f'task{number}_setup'),
        cell('%%writefile ' + SOURCES[number] + '\n' +
             strip_c_comments((folder / SOURCES[number]).read_text(encoding='utf-8')),
             f'task{number}_source'),
        cell('%%bash\nset -e\n' + compile_code, f'task{number}_compile'),
        cell('%%bash\nset -e\n' + run_code, f'task{number}_run'),
        cell(displays, f'task{number}_display')]
    preserve_outputs(cells, previous)
    path.write_text(json.dumps(notebook(cells), indent=1), encoding='utf-8')
    return path


def build_validation():
    setup = '''from pathlib import Path
from google.colab import files
import io, zipfile, subprocess, sys, shutil

uploaded = files.upload()
project_zip = next(name for name in uploaded if name.endswith('.zip'))
destination = Path('/content/HPC_validation')
destination.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(io.BytesIO(uploaded[project_zip])) as archive:
    archive.extractall(destination)
verifier = next(destination.rglob('tools/verify.py'))
ROOT = verifier.parent.parent
'''
    cells = [cell(setup, 'validation_setup'),
             cell("p = subprocess.run([sys.executable, str(verifier)], text=True, capture_output=True)\nprint(p.stdout)\nprint(p.stderr)\nassert p.returncode == 0, 'Validation failed.'", 'validation_run'),
             cell("shutil.make_archive('/content/HPC_run_results', 'zip', ROOT)\nfiles.download('/content/HPC_run_results.zip')", 'validation_download')]
    path = ROOT / 'tools' / 'HPC_Validation.ipynb'
    path.parent.mkdir(parents=True, exist_ok=True)
    contents = json.dumps(notebook(cells), indent=1)
    path.write_text(contents, encoding='utf-8')
    working = WORKSPACE / 'working' / 'HPC_Validation.ipynb'
    working.parent.mkdir(parents=True, exist_ok=True)
    working.write_text(contents, encoding='utf-8')
    return path


if __name__ == '__main__':
    selected_tasks = [int(value) for value in sys.argv[1:]] if len(sys.argv) > 1 else range(1, 5)
    for task in selected_tasks:
        print('Updated', build_task(task))
    if len(sys.argv) == 1:
        print('Updated', build_validation())
