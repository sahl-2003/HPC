# 6CS005 High Performance Computing

Student: Thaslim Mohammed Sahl, 2638120.

This project follows the 2025/26 assessment brief. The four tasks are word
occurrence counting with Pthreads, seven matrix operations with OpenMP,
password recovery from a file with CUDA, and Sobel edges across multiple PNGs.

Each folder under `Practical Task` contains its own source, input resources,
Colab notebook and task report. The CUDA programs remain separate `.cu` files.
The runtime is Python 3 with a T4 GPU; Python only prepares files, checks
answers and displays results. The assessed computations run in C and CUDA.

The repository remains private during development as requested. Each notebook
contains a compressed resource copy for private development runs. Its setup
first tries the GitHub resource URLs, then uses that copy when the repository
is private. No Google Drive mount is needed. Public unauthenticated GitHub
downloads require a later visibility change authorised by the student.

Task 04's normal demonstration uses only the lecturer's `download.png` image.
Its setup uses `wget` to fetch the image from its public URL, even while this
repository is private. Its checksum and PNG dimensions are checked before
processing. If the host is unavailable or the image changes,
setup reports that it is using the verified bundled copy.
`Practical Task/Task 04/images/public_images.json` records the sources and
checksum; `image_downloads.json` records how the image was loaded during a run.
See the Task 04 `images/SOURCES.md` for the public image link and attribution.
The notebook uses `/content/HPC_Task_04_OneImage`, which keeps previous
multi-image notebook resources separate.

The senior portfolio informed folder organisation only. Its earlier tasks
differ from this year's assessment. The programs here follow the current brief.

The report is named
`2638120_Thaslim_Mohammed_Sahl_High_Performance_Computing`.

## Colab notebooks

- [Task 01](https://colab.research.google.com/github/sahl-2003/HPC/blob/main/Practical%20Task/Task%2001/Task_01.ipynb)
- [Task 02](https://colab.research.google.com/github/sahl-2003/HPC/blob/main/Practical%20Task/Task%2002/Task_02.ipynb)
- [Task 03](https://colab.research.google.com/github/sahl-2003/HPC/blob/main/Practical%20Task/Task%2003/Task_03.ipynb)
- [Task 04](https://colab.research.google.com/github/sahl-2003/HPC/blob/main/Practical%20Task/Task%2004/Task_04.ipynb)

These links require repository access while HPC is private. The local `.ipynb`
files can also be opened using Colab's Upload notebook option.

Executed notebooks saved in Colab:

- [Task 01 word occurrences](https://colab.research.google.com/drive/17fYWnnA4bQEIOrRJl5N6sbBfPTEnoz9i)
- [Task 02 matrix operations](https://colab.research.google.com/drive/1mOq3OAuv3eOWKYj5IPSLim6wXH0npTHJ)
- [Task 03 password recovery](https://colab.research.google.com/drive/1MpOg0Lu-xRw5LR4jO0s7i9EdtIcUu-lQ)
- [Task 04 Sobel edges](https://colab.research.google.com/drive/1N2NxvodTA4TeiNAUY0JtYP0_kALg1uOE)

Sharing permissions remain as they were. The student can approve final access
when the private development version is ready to share.

## Running a task

Open its notebook, choose Runtime > Change runtime type > Python 3 > T4 GPU,
keep the latest runtime version, and select Run all. The notebook loads its
resources, writes the separate source, compiles, runs the program, shows the
output, and runs independent checks. Each notebook can start from a fresh
runtime. Resources are verified by SHA-256 in both download and bundled modes.

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
The Task 04 notebook writes a separate `task4_validation.json` after checking
the X gradient, Y gradient and final magnitude against an independent pixel
calculation. That separate cell creates thirteen small temporary PNG fixtures,
including grayscale rounding cases, direction ramps and the 6-8-10 example.
Together with `download.png`, it checks fourteen inputs and forty-two output
PNGs. Its checks also cover corrupt files and invalid paths. The manifest
records the result of that run; these test fixtures are separate from the normal
one-image demonstration.
The local `evidence` directory also contains one MP4 browser recording per task. Those
recordings capture the live Colab viewport while the program is rerun and its
output is displayed, preserving elapsed time at a reduced frame rate.
Videos are excluded from Git history and included in local archives.

Each task has a separate `Task_01_Report.md` to `Task_04_Report.md` answer.
The combined Word report includes the actual executed Colab links, source
notebook links, algorithms, memory handling, tests and timing observations.
`Viva_Guide.md` explains the code and gives questions to practise.

For submission, use the four separate Task ZIP archives as required by the
brief. The full portfolio ZIP is a backup of the report, tasks, viva guide and
evidence. Archives are local deliverables and are excluded from Git history.

The requested submission layout is produced by `tools/package_submission.py`.
It creates `HPC_Submission` beside this project, with `Evidence/Notebooks`,
`Evidence/Report`, `Evidence/Videos` and `Task1` to `Task4`. The four notebooks
are named `Task1.ipynb` to `Task4.ipynb`. Verified source and output filenames
are retained, and Task 4 inputs and output PNGs are placed beside its CUDA
source. The complete `HPC_Submission.zip` and four separate
`2638120_Task1.zip` to `2638120_Task4.zip` archives are created beside it.
Every copy and archived file is checked against its SHA-256 checksum.
