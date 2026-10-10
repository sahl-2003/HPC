from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
TASKS = ROOT / 'Practical Task'
SOURCES = {1: 'WordOccurrence.c', 2: 'MatrixOperations.c',
           3: 'PWCrack.cu', 4: 'SobelEdge.cu'}
RESOURCE_COMMIT = '2ae868943d23e75e6a6cf5c2a7420c23cf15872b'
RESOURCES = {1: ['WordOccurrenceDataset.txt'], 2: ['MatData.txt'],
             3: ['passwords.txt', 'expected_passwords.txt'],
             4: ['lodepng.cpp', 'lodepng.h', 'images/download.png']}


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
    metadata = {
        'colab': {'provenance': []},
        'kernelspec': {'name': 'python3', 'display_name': 'Python 3'},
        'language_info': {'name': 'python'}}
    metadata['accelerator'] = 'GPU'
    metadata['colab']['gpuType'] = 'T4'
    return {'nbformat': 4, 'nbformat_minor': 5, 'metadata': metadata, 'cells': cells}


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
    runtime_folder = f'/content/Task_{number:02d}'
    base = f'https://raw.githubusercontent.com/sahl-2003/HPC/{RESOURCE_COMMIT}/Practical%20Task/Task%20{number:02d}/'
    download_folder = runtime_folder + ('/images' if number == 4 else '')
    setup = '\n'.join([
        'from pathlib import Path',
        f'!mkdir -p {download_folder}',
        f'%cd {runtime_folder}',
        *[f'!wget --timeout=30 --tries=3 -O {name} {base}{name}'
          for name in RESOURCES[number]],
        ''])
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
    setup = f'''from pathlib import Path
import zipfile, subprocess, sys, shutil
!wget --timeout=30 --tries=3 -O /content/HPC_validation.zip https://codeload.github.com/sahl-2003/HPC/zip/{RESOURCE_COMMIT}
destination = Path('/content/HPC_validation')
destination.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile('/content/HPC_validation.zip') as archive:
    archive.extractall(destination)
verifier = next(destination.rglob('tools/verify.py'))
ROOT = verifier.parent.parent
'''
    cells = [cell(setup, 'validation_setup'),
             cell("p = subprocess.run([sys.executable, str(verifier)], text=True, capture_output=True)\nprint(p.stdout)\nprint(p.stderr)\nassert p.returncode == 0, 'Validation failed.'", 'validation_run'),
             cell("from google.colab import files\nshutil.make_archive('/content/HPC_run_results', 'zip', ROOT)\nfiles.download('/content/HPC_run_results.zip')", 'validation_download')]
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
