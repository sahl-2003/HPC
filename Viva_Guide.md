# High Performance Computing viva guide

Thaslim Mohammed Sahl | 2638120 | 6CS005

Open each source beside its notebook and trace a small example before the viva.
The tests establish the results; you still need to explain why the code obtains them.

## Task 01

- `pthread_create` starts `countWords` with one `ThreadArgs` structure. The
  argument array stays alive until all threads have joined.
- `pthread_join` waits for the specified worker. It does not cancel other
  workers. `pthread_exit` ends only the thread that calls it.
- The shared `nextByte` index needs a mutex. Without it, two workers could claim
  the same range and duplicate counts. Local arrays do not need that lock.
- The slice end extends across the final word. Try tracing a word that starts
  just before the proposed end and finishes just after it.
- Dynamic slicing lets a worker request another slice when it finishes.
  It does not promise exactly equal word counts in each thread.
- The programme lowercases ASCII letters; punctuation separates words.
- The host merges after joining. Worker timing or scheduling changes which
  thread handles a word, but it cannot change the final count.
- Explain why every word string is freed once, including duplicate strings
  removed during local compression, and why the merge holds borrowed pointers.

## Task 02

- `A.*B` multiplies corresponding elements. `A*B` uses a row-column dot product.
  For 2x3 and 3x2 inputs the product is 2x2, while element-wise operations are invalid.
- A transpose changes rows to columns. Element (i,j) becomes element (j,i).
- The result row count caps the number of OpenMP workers for this implementation.
  The loop runs over result rows, including for transposes.
- Each thread writes a separate row. Inputs are read-only, and the dot-product
  sum is local to one output cell. A single shared `sum` would be a race.
- The implicit OpenMP barrier completes the result before it is written.
- Division by zero produces `NaN`, because that value is required by the brief.
- Parsing needs line boundaries. A `%lf` scan alone could silently accept values
  from the following row. The growable line reader preserves the row count.
- Explain why `free(matrix)` alone would leak individually allocated rows.
- More threads can slow tiny matrices because creating a team has a cost.

## Task 03

- `__global__` marks the kernel that the CPU launches. `__device__` marks a
  GPU function. `__host__ __device__` compiles the crypt function for both sides.
- The thread index is `blockIdx.x * blockDim.x + threadIdx.x`. For block 2,
  256 threads per block and thread 7, its index is 519.
- Ten thousand passwords need 40 blocks of 256 threads: 10,240 launched
  threads, with the final 240 returning through the bounds check.
- The raw password is four characters plus its terminator. The encrypted
  password is ten characters plus its terminator. Allocation must include both.
- First-six-character filtering is valid because digits cannot change those
  encrypted positions. A complete ten-character comparison still decides a match.
- A `static` crypt buffer would be shared. A local array gives each thread its
  own candidate, so concurrent encryption does not overwrite another candidate.
- Output index N belongs to input line N. One output per thread removes the
  need for an atomic shared winner flag.
- The supplied boundary rule reflects or shifts characters; it is not the
  usual modulo rule. Replacing it would generate different encrypted strings.
- CUDA event time measures the kernel interval. It excludes file handling,
  allocation, transfers and programme startup.

## Task 04

- RGBA uses four bytes per pixel. Pixel i starts at byte `i*4`.
- The one-dimensional index converts to `x=i%width` and `y=i/width`.
- The lecturer's last-class example converts RGB to grayscale. This assignment
  extends that example by calculating the complete 3x3 Sobel convolution.
  Explain where the grayscale sample enters the Gx and Gy sums.
- The normal notebook demonstration uses one image, `download.png`. Its four
  views are the original image, the X gradient, the Y gradient and the combined
  Sobel magnitude. The CUDA command can still accept several PNGs; the separate
  regression tests check this batch capability.
- Gx measures left-right intensity changes, so it emphasises vertical edges.
  Gy measures top-bottom changes, so it emphasises horizontal edges. These are
  directions of intensity change, not the orientation of the visible edge.
- Trace the grayscale patch `[[0,0,0],[0,0,3],[0,4,0]]`. At its centre, the
  Sobel sums are `Gx=6` and `Gy=8`; the combined magnitude is
  `sqrt(6*6 + 8*8)=10`.
- Zero padding means a neighbour outside the image has intensity zero. This
  can create boundary edges in a constant white image.
- Input and output must be separate. In-place writes would change neighbour
  samples while other threads are still reading them.
- `rgbToGray(inImg, i)` reads RGB at byte index i and uses
  `(30*R + 59*G + 11*B)/100`. These are the lecturer's 0.30, 0.59 and 0.11
  weights. Integer division truncates the result consistently on CPU and GPU;
  for RGB `(0,23,13)` the result is 15. The independent NumPy tests include
  colors that detect the previous grayscale coefficients and rounding errors.
- The gradient PNGs show `min(abs(Gx),255)` and `min(abs(Gy),255)`, because a
  grayscale PNG cannot store a negative intensity. The signed, unclipped Gx
  and Gy values still enter `sqrt(Gx*Gx + Gy*Gy)`. Clipping either sum before
  this calculation would give the wrong final magnitude.
- The final `outImg_<basename>` caps the magnitude at 255 and preserves alpha.
  Alpha does not enter the intensity calculation. `outImg_Gx_<basename>` and
  `outImg_Gy_<basename>` contain one grayscale byte per pixel and use
  `lodepng_encode_file(..., LCT_GREY, 8)`, matching the lecturer's grayscale
  encoding example. The final RGBA buffer has four bytes per pixel.
- Explain the `c_` host buffers, the `d_` device buffers and the transfers
  between them. Each buffer is allocated for its own pixel format and freed
  when processing that image finishes.
- Blocks contain 256 threads, and the block count rounds the pixel count up.
  Threads past the final pixel return through the bounds check. Using image
  height as the block's thread count can exceed a GPU's block limit, so this
  launch works for varying image dimensions.
- PNG compression is handled by LodePNG on the CPU. The decoded pixel
  computation is the CUDA kernel; PNG decoding itself is not GPU work.
- `%%writefile` saves the separate CUDA source. Direct `nvcc` compilation links
  it with `lodepng.cpp`; the `nvcc4jupyter` extension is optional for this file
  compilation workflow.
- The notebook downloads only `download.png` from the lecturer's public URL
  with `wget`, so its source can be accessed without this repository's login.
  SHA-256 and PNG dimensions are verified before use.
  `image_downloads.json` records a public download or a reported bundled-copy
  fallback if the host is unavailable or its bytes have changed.
- The normal demonstration has one input. The independent validation cell
  creates thirteen small temporary fixtures for boundaries, colour rounding,
  alpha, both gradient directions and the 6-8-10 example. Its batch checks are
  separate from the four-view demonstration. The isolated runtime folder keeps
  earlier multi-image resources out of that run.
- Explain kernel time, transfer-plus-kernel time, and total application time.
  A kernel speedup cannot be used as an end-to-end speedup.
- Compare a single pixel and a large image. GPU startup and transfer costs
  matter much more for a very small input.

## Concepts from the module

Concurrency allows work to make progress in overlapping periods. Parallelism
means work actually executes at the same time. Pthreads and OpenMP use shared
host memory; CUDA has explicit host and device storage in these programmes.

A race condition needs an unsafe concurrent access to shared state, with at
least one write. A mutex gives one thread access to a protected section at a
time. A barrier waits for participating threads to reach a common point.
An atomic operation protects one supported update; it does not make an entire
multi-step algorithm safe automatically.

OpenMP uses the fork-join model. A reduction makes private accumulators and
combines them, which is useful for a total sum. Matrix multiplication here
needs a separate sum per output cell, so its sum stays local instead.

MPI was covered as message passing across processes. The assessment requires
Pthreads, OpenMP and CUDA, so these task implementations do not add MPI.

If one portion is serial, adding workers cannot remove that portion. File
loading, output formatting and some merging are serial here. Colab provides a
shared environment, so repeated measurements and clearly stated timing
intervals are needed for dependable performance claims.
