# Task 03 Password Cracking with Files using CUDA

Thaslim Mohammed Sahl | 2638120 | 6CS005

[Open task notebook in Colab](https://colab.research.google.com/github/sahl-2003/HPC/blob/main/Practical%20Task/Task%2003/Task_03.ipynb)

[Executed Colab notebook](https://colab.research.google.com/drive/1MpOg0Lu-xRw5LR4jO0s7i9EdtIcUu-lQ)

## Objective

Read every encrypted line from the command-line file, recover its two lowercase letters and two digits on the GPU, and write one plaintext answer per line to decrypted.txt in the original order.


## Implementation

The supplied CryptForCuda.c transformation creates ten encrypted characters from four raw characters. Its additions, subtractions, and boundary adjustments are retained exactly. The boundary adjustment is not replaced with conventional modulo wrapping. The device function writes into a caller-owned char[11] buffer, avoiding the shared static buffer used in the original serial example.

The host validates each line as six lowercase letters followed by four digits. It allocates 11*N encrypted bytes, 5*N plaintext bytes, and N*sizeof(int) status bytes, and copies the encrypted array to device memory. The x thread index is blockIdx.x * blockDim.x + threadIdx.x; a boundary guard excludes padded threads.

One CUDA thread owns one encrypted password. Nested loops generate the 26*26 letter pairs. The first six encrypted characters depend only on the letters, so a non-matching pair is rejected before trying the 100 digit pairs. A complete ten-character comparison determines success. This retains the lecturer's candidate-encryption logic while removing digit trials that cannot succeed.

For 10,000 records the launch is 40 x blocks with 256 threads per block. Smaller inputs use a smaller block size and at least two x blocks. Larger inputs derive the number of blocks from the record count and device limit. Each thread writes only its own result and status, so no global success flag or atomic operation is needed.


## Synchronisation and memory

The CPU copies plaintext and status arrays back after checking the kernel launch and completion. Every recovered plaintext is re-encrypted on the host and compared with its original encrypted line before it is accepted. An uncrackable but syntactically valid record writes NOT_FOUND in its position and returns exit code 2.

Input ordering is preserved by the fixed offsets record*11 and record*5. Every CUDA allocation, transfer, event, execution check and deallocation reports errors. Device buffers and events are released, and all host arrays are freed, including failure paths.


## Results and tests

The normal dataset contains 10,000 synthetic passwords created with seed 6005 and the supplied encryption logic. It includes boundary cases such as aa00, zz99, az09 and za90. All 10,000 recovered values matched the known plaintext file exactly.

An exhaustive independent test generated all 67,600 possible raw passwords, checked that their encrypted values were distinct within this domain, and recovered every one in order. Input sizes of 1, 2 and 257 tested launch padding and multiple blocks. A separate test compiled and ran the lecturer's PasswordGeneratorToText.c and recovered its 25 generated records.

Empty files, short lines, long lines, uppercase characters, invalid digits and blank lines were rejected. The valid-shaped string aaaaaa0000 had no candidate and correctly produced NOT_FOUND. The recorded kernel time for 10,000 records was 0.303 ms on the Tesla T4; file reads, allocation, transfers and output writes are excluded from that event timing.


## Performance and limits

This is the assessment's synthetic character transformation, not an attack on a real authentication service. Candidate filtering is valid because encrypted positions 0..5 depend only on the two letters. Without this property, the same pruning would not be valid.

All records are held in host and device memory at once. Memory demand therefore grows linearly with file size, and files that cannot be allocated fail clearly. Kernel time alone must not be reported as end-to-end application time or compared with a CPU program that includes file I/O.

## Build and run

```sh
nvcc -O2 -arch=sm_75 PWCrack.cu -o PWCrack
./PWCrack passwords.txt
```