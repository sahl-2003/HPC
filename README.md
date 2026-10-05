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

## Outputs and evidence

The required output files are saved beside each task source. `evidence/validation`
contains the full T4 validation logs and its 23-group PASS manifest. The local
`evidence` directory also contains one MP4 browser recording per task. Those
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
