"""Package the assessed task folders and the complete local portfolio."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = '2638120_Thaslim_Mohammed_Sahl_High_Performance_Computing'

def files_under(folder):
    for path in sorted(folder.rglob('*')):
        if path.is_file() and '.git' not in path.parts and '__pycache__' not in path.parts:
            if path.name == 'Viva_Guide.md':
                continue
            if path.suffix not in ('.zip', '.pyc'):
                relative = path.relative_to(ROOT)
                if relative.parts[0] == 'evidence' and path.name.startswith('figure_'):
                    continue  # The report now uses screenshots from the actual Colab run.
                if relative.parts[:2] == ('Practical Task', 'Task 04'):
                    if path.suffix == '.png' and path.name not in {
                            'download.png', 'outImg_download.png',
                            'outImg_Gx_download.png', 'outImg_Gy_download.png'}:
                        continue
                    if path.name == 'OpenCV_LICENSE.txt':
                        continue
                yield path

def package(destination, files):
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None, 'Archive verification failed.'
        print(destination.name, len(archive.namelist()), 'files', destination.stat().st_size, 'bytes')

for number in range(1, 5):
    folder = ROOT / 'Practical Task' / f'Task {number:02d}'
    files = list(files_under(folder))
    files += [ROOT / 'tools' / 'verify.py', ROOT / 'README.md', ROOT / 'colab_links.json']
    files += [ROOT / 'evidence' / f'Task_{number:02d}.mp4', ROOT / 'evidence' / f'Task_{number:02d}_Colab.jpg']
    files.append(ROOT / 'evidence' / f'Task_{number:02d}_Code_Colab.jpg')
    if number == 4:
        files.append(ROOT / 'evidence/Task_04_Four_Views_Colab.jpg')
        files.append(ROOT / 'evidence/Task_04_Validation_Colab.jpg')
    files += list((ROOT / 'evidence' / 'validation').glob(f'task{number}_*'))
    package(ROOT / f'Task_{number:02d}.zip', files)

package(ROOT / (NAME + '.zip'), list(files_under(ROOT)))
