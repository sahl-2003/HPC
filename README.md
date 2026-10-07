# 6CS005 High Performance Computing

Student: Thaslim Mohammed Sahl, 2638120.

This project follows the 2025/26 assessment brief. The four tasks are word
occurrence counting with Pthreads, seven matrix operations with OpenMP,
password recovery from a file with CUDA, and Sobel edges across multiple PNGs.

Each folder under `Practical Task` contains its own source, input resources,
Colab notebook and task report. The CUDA programs remain separate `.cu` files.
The notebooks use Python 3 for setup, checks and output display. Tasks 01 and
02 run on the CPU; Tasks 03 and 04 use a T4 GPU. The assessed computations run
in C and CUDA.

The notebooks download their required files automatically from the public
GitHub project, create the source file, compile and run the program, and
display its output. The first cell downloads these resources:

- Task 01: WordOccurrenceDataset.txt
- Task 02: MatData.txt
- Task 03: passwords.txt and expected_passwords.txt
- Task 04: lodepng.cpp, lodepng.h and images/download.png

The resources come from a fixed GitHub revision, so each fresh runtime uses
the same files. No manual file upload, GitHub login or Google Drive mount is
needed to download them. Task 04 uses the unchanged lecturer image stored in
the project's GitHub mirror. Its original public source is recorded in
images/public_images.json and images/SOURCES.md. The notebook uses
/content/Task_04 and shows the original image, both gradients and the final
Sobel output.

The senior portfolio informed folder organisation only. Its earlier tasks
differ from this year's assessment. The programs here follow the current brief.

The report is named
`2638120_Thaslim_Mohammed_Sahl_High_Performance_Computing`.

## Colab notebooks

- [Task 01](https://colab.research.google.com/drive/17fYWnnA4bQEIOrRJl5N6sbBfPTEnoz9i)
- [Task 02](https://colab.research.google.com/drive/1mOq3OAuv3eOWKYj5IPSLim6wXH0npTHJ)
- [Task 03](https://colab.research.google.com/drive/1MpOg0Lu-xRw5LR4jO0s7i9EdtIcUu-lQ)
- [Task 04](https://colab.research.google.com/drive/1N2NxvodTA4TeiNAUY0JtYP0_kALg1uOE)

These links open the saved notebooks using their Google Drive sharing settings.
The notebook files in the public GitHub project can also be opened in Colab.

Executed notebooks saved in Colab:

- [Task 01 word occurrences](https://colab.research.google.com/drive/17fYWnnA4bQEIOrRJl5N6sbBfPTEnoz9i)
- [Task 02 matrix operations](https://colab.research.google.com/drive/1mOq3OAuv3eOWKYj5IPSLim6wXH0npTHJ)
- [Task 03 password recovery](https://colab.research.google.com/drive/1MpOg0Lu-xRw5LR4jO0s7i9EdtIcUu-lQ)
- [Task 04 Sobel edges](https://colab.research.google.com/drive/1N2NxvodTA4TeiNAUY0JtYP0_kALg1uOE)

All four notebooks allow anyone with the link to view the code. To run a
notebook, open it in Colab and save a copy to your own Drive. The GitHub project
is public and includes the sources, inputs, output files and report.

## Assignment downloads

[Download the complete submission, task ZIPs, report and recordings](https://github.com/sahl-2003/HPC/releases/latest).
The complete submission includes all four task folders, notebooks, input
resources, output files, the Word report and four execution recordings.
Individual task ZIPs and recordings are also available on the same page.

## Running a task

Open a notebook in Colab and select Run all. Tasks 01 and 02 use a CPU runtime.
For Tasks 03 and 04, choose Runtime > Change runtime type > Python 3 > T4 GPU.
The first cell downloads the files automatically, then the remaining cells
write the source, compile and run the program, and display its output. Each
notebook can start from a fresh runtime. The password output is compared with
expected_passwords.txt, and the Sobel program compares its CUDA result with a
serial CPU reference.

The word and matrix programs use the CPU in that runtime. Password recovery
and Sobel detection use its T4 GPU. A Colab GPU allocation is required to run
the CUDA programs. No local CUDA installation is needed for these notebooks.

Task 04 follows the lecturer's last-class RGBA decoding and `rgbToGray` style.
Grayscale intensity is `(30*R + 59*G + 11*B)/100`, with integer truncation.
The complete assignment applies the 3x3 Gx and Gy Sobel kernels with zero
padding. For this one input, the notebook displays four views: the original image,
the X gradient, the Y gradient and the combined Sobel magnitude. Gx measures
left-right intensity changes, so it emphasises vertical edges; Gy measures
top-bottom changes, so it emphasises horizontal edges.

The program saves `outImg_Gx_<basename>` and `outImg_Gy_<basename>` as grayscale
PNGs, using `lodepng_encode_file` with `LCT_GREY` and 8-bit samples as taught in
class. The displayed gradient intensities are `min(abs(Gx),255)` and
`min(abs(Gy),255)`. The final `outImg_<basename>` is calculated from the signed,
unclipped sums as `min(sqrt(Gx*Gx + Gy*Gy),255)` and preserves the input alpha
channel. Each pixel's CUDA thread writes its own output values. The CUDA command
still accepts multiple PNGs, and the separate regression tests check batch
processing as required by the brief.
`%%writefile` creates `SobelEdge.cu`, which `nvcc` compiles together with
`lodepng.cpp`. See `Practical Task/Task 04/Task_04_Requirements.md` for the
question's requirements and their implementation.

## Outputs and evidence

The required output files are saved beside each task source. `evidence/validation`
contains the initial full T4 validation logs and its 23-group PASS manifest.
The saved Task 04 validation records cover fourteen inputs and forty-two
output PNGs, including direction ramps, grayscale rounding and the 6-8-10
example. Full regression checks remain in tools/verify.py and can be run
with [the development validation notebook](https://colab.research.google.com/github/sahl-2003/HPC/blob/main/tools/HPC_Validation.ipynb).
The validation notebook automatically downloads the project source ZIP from
the same fixed GitHub revision, then runs tools/verify.py. It needs no manual
ZIP upload.
The local `evidence` directory also contains one MP4 browser recording per task. Those
recordings capture the live Colab viewport while the program is rerun and its
output is displayed, preserving elapsed time at a reduced frame rate.
Videos are excluded from Git history and available in the public downloads.

Each task has a separate `Task_01_Report.md` to `Task_04_Report.md` answer.
The combined Word report includes the actual executed Colab links, source
notebook links, algorithms, memory handling, tests and timing observations.

For submission, use the four separate Task ZIP archives as required by the
brief. The full portfolio ZIP is a backup of the report, tasks and
evidence. Archives are available in the public downloads and excluded from Git history.

The requested submission layout is produced by `tools/package_submission.py`.
It creates `HPC_Submission` beside this project, with `Evidence/Notebooks`,
`Evidence/Report`, `Evidence/Videos` and `Task1` to `Task4`. The four notebooks
are named `Task1.ipynb` to `Task4.ipynb`. Verified source and output filenames
are retained, and Task 4 inputs and output PNGs are placed beside its CUDA
source. The complete `HPC_Submission.zip` and four separate
`2638120_Task1.zip` to `2638120_Task4.zip` archives are created beside it.
Every copy and archived file is checked against its SHA-256 checksum.
