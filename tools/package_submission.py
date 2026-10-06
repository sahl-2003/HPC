"""Copy verified coursework into the student's requested submission layout."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile
import sys
from datetime import datetime

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parent
DESTINATION = WORKSPACE / 'HPC_Submission'
REPORT = '2638120_Thaslim_Mohammed_Sahl_High_Performance_Computing.docx'
COPIES = []
UPDATE = '--update' in sys.argv
PREVIOUS = {}
previous_manifest = DESTINATION / 'Evidence/Report/Submission_Validation.json'
if previous_manifest.exists():
    PREVIOUS = {entry['file']: entry['sha256']
                for entry in json.loads(previous_manifest.read_text())['files']}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy(source, relative, report_links=False):
    target = DESTINATION / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    contents = source.read_bytes()
    if report_links:
        contents = contents.replace(b'(../../evidence/', b'(./')
    expected = hashlib.sha256(contents).hexdigest()
    if target.exists() and digest(target) != expected:
        if not UPDATE or PREVIOUS.get(relative.as_posix()) != digest(target):
            raise RuntimeError(f'Refusing to overwrite an unverified file: {target}')
    if report_links:
        target.write_bytes(contents)
    else:
        shutil.copy2(source, target)
    assert expected == digest(target)
    COPIES.append({'file': relative.as_posix(), 'sha256': digest(target)})


def write(relative, text):
    target = DESTINATION / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_text(encoding='utf-8') != text:
        if not UPDATE:
            raise RuntimeError(f'Refusing to overwrite a different file: {target}')
    target.write_text(text, encoding='utf-8', newline='\n')


def archive(destination, paths):
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(paths):
            bundle.write(path, Path('HPC_Submission') / path.relative_to(DESTINATION))
    with zipfile.ZipFile(destination) as bundle:
        assert bundle.testzip() is None
        for path in paths:
            name = (Path('HPC_Submission') / path.relative_to(DESTINATION)).as_posix()
            assert hashlib.sha256(bundle.read(name)).hexdigest() == digest(path)


DESTINATION.mkdir(parents=True, exist_ok=True)
if UPDATE and PREVIOUS:
    for relative, expected in PREVIOUS.items():
        existing = DESTINATION / relative
        if existing.exists() and digest(existing) != expected:
            raise RuntimeError(f'Submission file changed outside the builder: {existing}')
    backup = WORKSPACE / 'working/submission_backups' / datetime.now().strftime('%Y%m%d_%H%M%S')
    backup.mkdir(parents=True, exist_ok=False)
    archive(backup / 'HPC_Submission.zip',
            [path for path in DESTINATION.rglob('*') if path.is_file()])
    print(f'Previous submission backed up: {backup}')
for number in range(1, 5):
    folder = PROJECT / 'Practical Task' / f'Task {number:02d}'
    target = Path(f'Task{number}')
    for source in sorted(folder.rglob('*')):
        if not source.is_file() or '__pycache__' in source.parts:
            continue
        if source.suffix in ('.ipynb', '.zip', '.pyc'):
            continue
        if number == 4 and source.suffix == '.png' and source.name not in {
                'download.png', 'outImg_download.png',
                'outImg_Gx_download.png', 'outImg_Gy_download.png'}:
            continue
        if number == 4 and source.name == 'OpenCV_LICENSE.txt':
            continue
        if source.suffix == '.md' and source.name.endswith('_Report.md'):
            copy(source, Path('Evidence/Report') / source.name, report_links=True)
        else:
            # Inputs and outputs sit beside the source, as in the supplied example.
            copy(source, target / source.name)
    copy(folder / f'Task_{number:02d}.ipynb',
         Path('Evidence/Notebooks') / f'Task{number}.ipynb')
    copy(PROJECT / 'evidence' / f'Task_{number:02d}.mp4',
         Path('Evidence/Videos') / f'Task_{number:02d}.mp4')
    copy(PROJECT / 'evidence' / f'Task_{number:02d}_Colab.jpg',
         Path('Evidence/Report') / f'Task_{number:02d}_Colab.jpg')
    copy(PROJECT / 'evidence' / f'Task_{number:02d}_Code_Colab.jpg',
         Path('Evidence/Report') / f'Task_{number:02d}_Code_Colab.jpg')

copy(PROJECT / REPORT, Path('Evidence/Report') / REPORT)
copy(PROJECT / 'Viva_Guide.md', Path('Evidence/Report/Viva_Guide.md'))
copy(PROJECT / 'colab_links.json', Path('Evidence/Notebooks/colab_links.json'))
copy(PROJECT / 'evidence/recordings.json', Path('Evidence/Videos/recordings.json'))
copy(PROJECT / 'evidence/Task_04_Four_Views_Colab.jpg',
     Path('Evidence/Report/Task_04_Four_Views_Colab.jpg'))
copy(PROJECT / 'evidence/Task_04_Validation_Colab.jpg',
     Path('Evidence/Report/Task_04_Validation_Colab.jpg'))
for source in sorted((PROJECT / 'evidence/validation').glob('*')):
    if source.is_file():
        copy(source, Path('Evidence/Report/Validation') / source.name)
copy(PROJECT / 'evidence/resource_validation.json',
     Path('Evidence/Report/Validation/resource_validation.json'))

# Keep the full upstream notice without modifying either supplied codec source.
codec = (PROJECT / 'Practical Task/Task 04/lodepng.cpp').read_text(encoding='utf-8')
notice = codec.split('/*', 1)[1].split('*/', 1)[0].strip() + '\n'
write(Path('Task4/LODEPNG_LICENSE.txt'), notice)

write(Path('README.txt'), '''High Performance Computing submission
Thaslim Mohammed Sahl | Student number 2638120 | 6CS005

Evidence/Notebooks contains Task1.ipynb to Task4.ipynb.
Evidence/Report contains the Word report, separate task answers, viva guide,
actual Colab screenshots and validation records.
Evidence/Videos contains one real Colab execution recording for each task.
Task1 to Task4 contain the separate C/CUDA programs, inputs and saved outputs.

The source, inputs, outputs, notebooks, Word report and recordings are copied
from the verified project without changing their contents. Screenshot links
in the separate Markdown task answers point to their new local folder.
The notebook filenames
follow the requested submission layout. Source filenames keep the tested names
used in the report and saved Colab notebooks. lodepng.cpp is kept as the C++
codec source compiled by nvcc, with its original licence and header.

Open a notebook in Google Colab, select Python 3 and T4 GPU, then Run all.
Its setup reconstructs the tested runtime folders from online resources or
checksum-verified bundled copies. No private Google Drive mount is needed.
Task 4 downloads the one public image listed in Task4/public_images.json.
The existing Colab links are in the Word report and colab_links.json.

Task 4 demonstrates one public input, download.png, with these output prefixes:
outImg_Gx_ for the X gradient, outImg_Gy_ for the Y gradient, and outImg_ for
the combined Sobel magnitude. Its notebook shows the four views together.
The flat Task4 folder is the submission layout; images/ and outputs/ in the
report describe the folders used during the actual Colab executions.

Optional terminal commands inside each task folder (Linux/Colab):
Task1: gcc -std=c11 -O2 -pthread WordOccurrence.c -o WordOccurrence
       ./WordOccurrence WordOccurrenceDataset.txt 4
Task2: gcc -std=c11 -O2 -fopenmp MatrixOperations.c -lm -o MatrixOperations
       ./MatrixOperations MatData.txt 4
Task3: nvcc -O2 -arch=sm_75 PWCrack.cu -o PWCrack
       ./PWCrack passwords.txt
Task4: nvcc -O2 -arch=sm_75 lodepng.cpp SobelEdge.cu -o SobelEdge
       ./SobelEdge . download.png

The GitHub repository remains private. This package does not change sharing.
''')

if UPDATE:
    current_files = {entry['file'] for entry in COPIES}
    for relative, expected in PREVIOUS.items():
        if relative in current_files:
            continue
        stale = (DESTINATION / relative).resolve()
        if not stale.is_relative_to(DESTINATION.resolve()):
            raise RuntimeError(f'Unsafe stale path: {stale}')
        if stale.exists():
            assert digest(stale) == expected
            stale.unlink()  # The verified previous copy is retained in the backup ZIP.

manifest = {'status': 'PASS', 'copied_files': len(COPIES),
            'checks': ['Copied bytes match the verified project, with Markdown screenshot paths adapted to this layout',
                       'Four notebooks, four MP4s and the student report exist',
                       'ZIP CRC and every archived file checksum match'],
            'files': sorted(COPIES, key=lambda entry: entry['file'])}
for number in range(1, 5):
    assert (DESTINATION / f'Evidence/Notebooks/Task{number}.ipynb').is_file()
    assert (DESTINATION / f'Evidence/Videos/Task_{number:02d}.mp4').stat().st_size > 0
    # These archives meet the brief's separate ZIP requirement for each task.
    paths = [path for path in (DESTINATION / f'Task{number}').rglob('*') if path.is_file()]
    paths += [DESTINATION / f'Evidence/Notebooks/Task{number}.ipynb',
              DESTINATION / f'Evidence/Videos/Task_{number:02d}.mp4',
              DESTINATION / f'Evidence/Report/Task_{number:02d}_Report.md',
              DESTINATION / f'Evidence/Report/Task_{number:02d}_Colab.jpg',
              DESTINATION / f'Evidence/Report/Task_{number:02d}_Code_Colab.jpg',
              DESTINATION / 'Evidence/Notebooks/colab_links.json',
              DESTINATION / 'README.txt']
    paths += [path for path in (DESTINATION / 'Evidence/Report/Validation').glob(f'task{number}_*')
              if path.is_file()]
    if number == 4:
        paths.append(DESTINATION / 'Evidence/Report/Task_04_Four_Views_Colab.jpg')
        paths.append(DESTINATION / 'Evidence/Report/Task_04_Validation_Colab.jpg')
    archive(WORKSPACE / f'2638120_Task{number}.zip', paths)

write(Path('Evidence/Report/Submission_Validation.json'),
      json.dumps(manifest, indent=2) + '\n')
all_files = [path for path in DESTINATION.rglob('*') if path.is_file()]
archive(WORKSPACE / 'HPC_Submission.zip', all_files)
print(f'Submission folder: {DESTINATION}')
print(f'Complete archive: {WORKSPACE / "HPC_Submission.zip"}')
print(f'Verified {len(COPIES)} copied files and {len(all_files)} archived files.')
print('Separate task archives: 2638120_Task1.zip to 2638120_Task4.zip')
