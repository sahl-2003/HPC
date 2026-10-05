"""Independent output oracles and failure tests, executed in the Colab runtime."""
from pathlib import Path
from collections import Counter
import re
import json
import subprocess
import tempfile
import time
import math
import itertools
import sys
import platform
import shutil
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / 'Practical Task'
RESULTS = ROOT / 'evidence' / 'validation'
RESULTS.mkdir(parents=True, exist_ok=True)
RECORDS = []

def run(args, cwd, expected=0, input_text=None, timeout=180):
    started = time.perf_counter()
    p = subprocess.run([str(x) for x in args], cwd=cwd, text=True, input=input_text,
                       capture_output=True, timeout=timeout)
    if p.returncode != expected:
        raise AssertionError(f'{args}: exit {p.returncode}, expected {expected}\n{p.stdout}\n{p.stderr}')
    return p, time.perf_counter()-started

def record(name, details):
    RECORDS.append({'test': name, 'status': 'PASS', 'details': details})
    print(f'PASS: {name} ({details})', flush=True)

def check_words(executable, file, threads, work):
    p, seconds = run([executable, file, threads], work)
    counts = Counter(w.lower() for w in re.findall(r'[A-Za-z0-9]+', Path(file).read_text()))
    rows = (work/'result.txt').read_text().splitlines()
    assert rows[0] == 'Word\tFrequency'
    actual = {word: int(n) for word, n in (row.split('\t') for row in rows[1:])}
    assert actual == counts
    assert len(rows)-1 == len(actual)
    assert [row.split('\t')[0] for row in rows[1:]] == sorted(counts)
    assert sum(actual.values()) == sum(counts.values())
    return p.stdout, seconds, len(counts), sum(counts.values())

def task1():
    folder = TASKS/'Task 01'
    exe = folder/'WordOccurrence'
    run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Wpedantic','-pthread',folder/'WordOccurrence.c','-o',exe], folder)
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        for threads in [1,2,3,7,16]:
            log, seconds, unique, total = check_words(exe, folder/'WordOccurrenceDataset.txt', threads, work)
            (RESULTS/f'task1_threads_{threads}.log').write_text(log)
            record(f'Task 1 supplied dataset, {threads} threads', f'{total} words, {unique} unique, oracle equal')
        fixture = work/'words.txt'
        fixture.write_text("HELLO hello, don't CUDA_12\tworld\r\n"+'A'*20000+' end END 42')
        for threads in [1,3,17,128]: check_words(exe, fixture, threads, work)
        record('Task 1 word boundaries and remainder slices', '20,000-character word, punctuation, digits, CRLF, no final newline')
        fixture.write_text('')
        check_words(exe, fixture, 32, work)
        record('Task 1 empty file', 'header and zero counts')
        for argument in ['0','-1','abc','2x','1025']:
            run([exe, fixture, argument], work, expected=1)
        run([exe, work/'missing.txt', '4'], work, expected=1)
        run([exe], work, expected=1)
        record('Task 1 invalid arguments and missing file', 'clear errors and nonzero exits')
    run([exe, folder/'WordOccurrenceDataset.txt','4'], folder)

def read_matrices(path):
    lines = iter(Path(path).read_text().splitlines())
    matrices = []
    for line in lines:
        if not line.strip(): continue
        r,c = map(int,line.split(','))
        m = np.array([[float(v) for v in next(lines).split(',')] for _ in range(r)])
        assert m.shape == (r,c)
        matrices.append(m)
    assert len(matrices)%2 == 0
    return matrices

NAMES = ['Addition','Subtraction','Element-wise multiplication','Element-wise division',
         'Transpose A','Transpose B','Matrix multiplication']

def matrix_oracle(a,b):
    if a.shape == b.shape:
        with np.errstate(divide='ignore',invalid='ignore'):
            division = np.where(b==0,np.nan,a/b)
        answers = [a+b,a-b,a*b,division]
    else: answers = [None]*4
    return answers+[a.T,b.T,a@b if a.shape[1]==b.shape[0] else None]

def check_matrices(exe, data, threads, work):
    p,seconds = run([exe,data,threads],work)
    lines = iter((work/'results.txt').read_text().splitlines())
    nonempty = iter(line for line in lines if line)
    matrices = read_matrices(data)
    for pair,(a,b) in enumerate(zip(matrices[::2],matrices[1::2]),1):
        assert next(nonempty) == f'Pair {pair}: A={a.shape[0]},{a.shape[1]} B={b.shape[0]},{b.shape[1]}'
        for name, expected in zip(NAMES,matrix_oracle(a,b)):
            header = next(nonempty)
            if expected is None:
                assert header.startswith(name+' cannot be done')
            else:
                assert header == f'{name} - {expected.shape[0]},{expected.shape[1]}'
                actual = np.array([[float(v) for v in next(nonempty).split(',')] for _ in range(expected.shape[0])])
                np.testing.assert_allclose(actual,expected,rtol=1e-12,atol=1e-10,equal_nan=True)
    assert next(nonempty,None) is None
    for rows,cols,requested,capped,actual in re.findall(r': (\d+)x(\d+); threads requested=(\d+) capped=(\d+) actual=(\d+)',p.stdout):
        assert int(capped) == min(int(requested),int(rows))
        assert 1 <= int(actual) <= int(capped)
    return p.stdout,seconds,len(matrices)//2

def task2():
    folder = TASKS/'Task 02'
    exe = folder/'MatrixOperations'
    run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Wpedantic','-fopenmp',folder/'MatrixOperations.c','-lm','-o',exe],folder)
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        for threads in [1,4,64]:
            log,seconds,pairs = check_matrices(exe,folder/'MatData.txt',threads,work)
            (RESULTS/f'task2_threads_{threads}.log').write_text(log)
            record(f'Task 2 supplied matrices, {threads} requested threads', f'{pairs} pairs, all operations equal NumPy')
        fixture = work/'matrices.txt'
        fixture.write_text('2,2\n1,2\n3,4\n\n2,2\n0,5\n6,0\n\n2,3\n1,2,3\n4,5,6\n3,1\n1\n2\n3\n1,3\n4,5,6\n2,1\n7\n8\n')
        for threads in [1,3,100]: check_matrices(exe,fixture,threads,work)
        record('Task 2 operation applicability, NaN and thread cap', 'square, rectangular, incompatible and 1-row matrices')
        invalid = ['0,2\n','2x,2\n','1,2,3\n','2,2\n1,2\n','1,2\n1,no\n',
                   '1,2\n1,2,3\n','1,2\n1\n','1,1\nnan\n','1,1\ninf\n',
                   '1,1\n3\n','', '1,1\n3\n\n1,1\n\n4\n','1,1\n1e9999\n']
        for text in invalid:
            fixture.write_text(text)
            run([exe,fixture,'4'],work,expected=1)
        run([exe,work/'missing.txt','4'],work,expected=1)
        for argument in ['0','-2','text','3x']:
            run([exe,folder/'MatData.txt',argument],work,expected=1)
        record('Task 2 malformed headers, row counts and numeric tokens', f'{len(invalid)} invalid files rejected')
    run([exe,folder/'MatData.txt','4'],folder)

def encrypt(raw):
    values = [ord(raw[0])+2,ord(raw[0])-2,ord(raw[0])+1,ord(raw[1])+3,
              ord(raw[1])-3,ord(raw[1])-1,ord(raw[2])+2,ord(raw[2])-2,ord(raw[3])+4,ord(raw[3])-4]
    for i,v in enumerate(values):
        lo,hi = (97,122) if i<6 else (48,57)
        values[i] = v-hi+lo if v>hi else lo-v+lo if v<lo else v
    return ''.join(map(chr,values))

def task3():
    folder = TASKS/'Task 03'
    exe = folder/'PWCrack'
    run(['nvcc','-O2','-lineinfo','-arch=sm_75','-Xcompiler=-Wall,-Wextra',folder/'PWCrack.cu','-o',exe],folder)
    all_raw = [a+b+c+d for a,b,c,d in itertools.product('abcdefghijklmnopqrstuvwxyz','abcdefghijklmnopqrstuvwxyz','0123456789','0123456789')]
    all_encrypted = [encrypt(p) for p in all_raw]
    assert len(set(all_encrypted)) == len(all_raw)
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        for n in [1,2,257,10000,67600]:
            raw = all_raw if n==67600 else (folder/'expected_passwords.txt').read_text().splitlines()[:n]
            data = work/'passwords.txt'
            data.write_text('\n'.join(map(encrypt,raw))+'\n')
            p,seconds = run([exe,data],work)
            assert (work/'decrypted.txt').read_text().splitlines()==raw
            (RESULTS/f'task3_{n}_passwords.log').write_text(p.stdout)
            record(f'Task 3 {n} passwords', 'exact recovery and input order, independent encryption oracle')
        data = work/'invalid.txt'
        for text in ['', 'short\n','ABCdef1234\n','abcdefghijk1234567890\n','abcdef123x\n','\n']:
            data.write_text(text)
            run([exe,data],work,expected=1)
        data.write_text('aaaaaa0000\n')
        run([exe,data],work,expected=2)
        assert (work/'decrypted.txt').read_text()=='NOT_FOUND\n'
        record('Task 3 invalid and uncrackable records', 'malformed files rejected; NOT_FOUND preserves line')
        # Confirm that files produced by the lecturer's generator also work.
        generator = work/'PasswordGeneratorToText'
        run(['gcc',folder/'PasswordGeneratorToText.c','-o',generator],work)
        run([generator],work,input_text='25\n')
        run([exe,work/'passwords.txt'],work)
        assert list(map(encrypt,(work/'decrypted.txt').read_text().splitlines())) == (work/'passwords.txt').read_text().splitlines()
        record('Task 3 lecturer generator compatibility', '25 generated encrypted records verified')
    run([exe,folder/'passwords.txt'],folder)

def sobel_oracle(image):
    rgba=np.asarray(image.convert('RGBA')).astype(np.int32)
    grey=(30*rgba[:,:,0]+59*rgba[:,:,1]+11*rgba[:,:,2])//100
    h,w=grey.shape
    padded=np.pad(grey,1,mode='constant')
    gx=-padded[0:h,0:w]+padded[0:h,2:w+2]-2*padded[1:h+1,0:w]+2*padded[1:h+1,2:w+2]-padded[2:h+2,0:w]+padded[2:h+2,2:w+2]
    gy=-padded[0:h,0:w]-2*padded[0:h,1:w+1]-padded[0:h,2:w+2]+padded[2:h+2,0:w]+2*padded[2:h+2,1:w+1]+padded[2:h+2,2:w+2]
    edge=np.minimum(255,np.sqrt((gx*gx+gy*gy).astype(np.float32))).astype(np.uint8)
    result=np.empty_like(rgba,dtype=np.uint8)
    result[:,:,:3]=edge[:,:,None]
    result[:,:,3]=rgba[:,:,3]
    return result

def task4():
    folder=TASKS/'Task 04'
    exe=folder/'SobelEdge'
    run(['nvcc','-O2','-lineinfo','-arch=sm_75','-Xcompiler=-Wall,-Wextra',folder/'lodepng.cpp',folder/'SobelEdge.cu','-o',exe],folder)
    with tempfile.TemporaryDirectory() as temp:
        work=Path(temp)
        fixtures=[]
        for name,shape,value in [('black',(3,3),(0,0,0,255)),('white',(3,3),(255,255,255,255)),
                                  ('single',(1,1),(120,30,50,70)),('wide',(6,4),(50,180,40,255))]:
            path=work/(name+'.png'); Image.new('RGBA',shape,value).save(path); fixtures.append(path)
        rng=np.random.default_rng(6005)
        for w,h in [(2,5),(17,19),(1025,2)]:
            path=work/f'random_{w}_{h}.png'; Image.fromarray(rng.integers(0,256,(h,w,4),dtype=np.uint8)).save(path); fixtures.append(path)
        # Separated colour impulses expose coefficient and rounding differences without
        # every edge being saturated. Alpha varies independently of the RGB values.
        colours=np.array([(0,23,13),(0,39,9),(0,255,0),(100,0,0),(0,0,100),(14,14,14)],dtype=np.int32)
        np.testing.assert_array_equal(colours @ np.array([30,59,11]) // 100,[15,24,150,30,11,14])
        colour_fixture=np.zeros((7,13,4),dtype=np.uint8)
        colour_fixture[:,:,3]=np.arange(91,dtype=np.uint8).reshape(7,13)
        for colour,(y,x) in zip(colours,[(2,2),(2,6),(2,10),(5,2),(5,6),(5,10)]):
            colour_fixture[y,x,:3]=colour
        path=work/'colour_weights.png'; Image.fromarray(colour_fixture).save(path); fixtures.append(path)
        fixtures += sorted((folder/'images').glob('*.png'))
        p,seconds=run([exe,work,*fixtures],work)
        (RESULTS/'task4_images.log').write_text(p.stdout)
        for path in fixtures:
            actual=np.asarray(Image.open(work/('outImg_'+path.name)).convert('RGBA'))
            expected=sobel_oracle(Image.open(path))
            np.testing.assert_array_equal(actual,expected)
        record('Task 4 full pixel oracle', f'{len(fixtures)} PNGs, zero padding, saturation, alpha and non-multiple sizes')
        bad=work/'bad.png'; bad.write_text('not a PNG')
        run([exe,work,bad,fixtures[0]],work,expected=1)
        run([exe,work,work/'missing.png'],work,expected=1)
        run([exe,work/'missing-dir',fixtures[0]],work,expected=1)
        run([exe,work,fixtures[0],fixtures[0]],work,expected=1)
        record('Task 4 corrupt files and invalid paths', 'reports failures, continues to valid image, rejects name collisions')
    outputs=folder/'outputs'; outputs.mkdir(exist_ok=True)
    run([exe,outputs,*sorted((folder/'images').glob('*.png'))],folder)

def cpu_memory_checks():
    with tempfile.TemporaryDirectory() as temp:
        work=Path(temp)
        for task,name,args in [(1,'WordOccurrence',['WordOccurrenceDataset.txt','7']), (2,'MatrixOperations',['MatData.txt','64'])]:
            folder=TASKS/f'Task {task:02d}'; exe=work/name
            flags=['-pthread'] if task==1 else ['-fopenmp','-lm']
            run(['gcc','-std=c11','-g','-O1','-fsanitize=address,undefined',folder/(name+'.c'),*flags,'-o',exe],folder)
            p,_=run([exe,folder/args[0],args[1]],work)
            assert 'AddressSanitizer' not in p.stderr and 'runtime error:' not in p.stderr
        record('CPU memory and undefined-behaviour checks', 'AddressSanitizer and UBSan on both supplied datasets')

def main():
    task=int(sys.argv[1]) if len(sys.argv)>1 else 0
    functions={1:task1,2:task2,3:task3,4:task4}
    try:
        for number,function in functions.items():
            if task in (0,number): function()
        if task==0: cpu_memory_checks()
        manifest={'status':'PASS','python':platform.python_version(),'platform':platform.platform(),
                  'tests':RECORDS,'run_task':task}
        gpu=subprocess.run(['nvidia-smi','--query-gpu=name,driver_version','--format=csv,noheader'],capture_output=True,text=True)
        manifest['gpu']=gpu.stdout.strip()
        (RESULTS/f'task{task}_validation.json').write_text(json.dumps(manifest,indent=2))
        print(f'All {len(RECORDS)} test groups passed.',flush=True)
    except Exception as error:
        (RESULTS/f'task{task}_validation.json').write_text(json.dumps({'status':'FAIL','tests':RECORDS,'error':str(error)},indent=2))
        raise

if __name__=='__main__': main()
