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
- Trace Gx and Gy on a 3x3 patch. Gx measures left-right intensity changes;
  Gy measures top-bottom changes. Magnitude combines them using a square root.
- Zero padding means a neighbour outside the image has intensity zero. This
  can create boundary edges in a constant white image.
- Input and output must be separate. In-place writes would change neighbour
  samples while other threads are still reading them.
- Integer luminance uses weights 77, 150 and 29 with division by 256.
  The edge map caps the magnitude at 255 and preserves alpha.
- PNG compression is handled by LodePNG on the CPU. The decoded pixel
  computation is the CUDA kernel; PNG decoding itself is not GPU work.
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
