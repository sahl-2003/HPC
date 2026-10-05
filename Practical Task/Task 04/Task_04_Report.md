# Task 04 Sobel Edge Detection using Cuda across many PNG images

Thaslim Mohammed Sahl | 2638120 | 6CS005

[Open task notebook in Colab](https://colab.research.google.com/github/sahl-2003/HPC/blob/main/Practical%20Task/Task%2004/Task_04.ipynb)

[Executed Colab notebook](https://colab.research.google.com/drive/1N2NxvodTA4TeiNAUY0JtYP0_kALg1uOE)

## Objective

Decode multiple PNG images, apply the Sobel horizontal and vertical kernels on the GPU with zero padding, and save each resulting edge image with the original width, height and alpha channel.


## Implementation

LodePNG decodes each file into an RGBA host array. Its original copyright and licence notices are retained. The input images are original repeatable test patterns: shapes at 512x384, a gradient at 640x480 and a checkerboard at 257x193. The final dimensions deliberately include a non-divisible pixel count.

Integer luminance is (77*R + 150*G + 29*B) / 256, rounded down. The 3x3 Gx matrix is [-1,0,1; -2,0,2; -1,0,1], and Gy is [-1,-2,-1; 0,0,0; 1,2,1]. Each thread visits its pixel's 3x3 neighbourhood and treats any out-of-image sample as zero.

The edge magnitude is sqrt(Gx*Gx + Gy*Gy), truncated to an integer and capped at 255. That edge value is written to R, G and B; alpha is copied from the original pixel. Reading always uses the separate input buffer, so one pixel's output cannot change a neighbour's input.

GPU memory is sized as width*height*4 bytes for each input and output array. The x grid uses ceil(pixel_count/256) blocks, with a bounds guard in the kernel. The command accepts an output directory and any number of input images. Result names are outImg_ followed by the input basename. Distinct basenames avoid accidental overwriting.


## Synchronisation and memory

After launch and execution checks, the output is copied to the host. A serial C reference expresses the gradients as neighbour sums and compares every RGBA byte. An independent NumPy checker also uses padded image arrays and validates the complete output, including alpha.

Every successful output has exactly the original image dimensions. Zero padding can produce a visible edge around a constant bright image because its boundary neighbours are black. This is expected under the specified padding rule. PNG decode or encode failures and CUDA failures return errors; the batch can continue to a later valid input.

Images are processed one at a time, releasing host buffers, device buffers and events after each image. The CPU reference needs a third host array for verification. Peak working memory depends on the largest image, rather than the sum of every image in the batch.


## Results and tests

All pixels matched both references for ten PNGs: the three main patterns, 3x3 black and white inputs, a single pixel, a 6x4 input, and random RGBA inputs of 2x5, 17x19 and 1025x2. Tests covered zero padding, saturation, preserved transparency and padded launch threads.

Corrupt PNGs, missing files, missing output directories and duplicate basenames were tested. A corrupt image followed by a valid image confirmed that the valid image still processed and the overall command reported the batch failure.

The recorded 640x480 gradient run took 14.651 ms for serial CPU computation, 0.035 ms for the CUDA kernel, and 0.754 ms for transfers plus kernel. These are single-run observations. GPU allocation, PNG decoding and encoding are outside the transfer-and-kernel interval. The first CUDA invocation has additional startup overhead, so timings are not stable benchmark estimates.


## Performance and limits

The implementation uses global memory and a basic one-thread-per-pixel kernel, matching the taught CUDA model. It does not use shared-memory tiling or concurrent image streams. Reading overlapping neighbourhoods repeats memory accesses, but the independent output ownership makes correctness straightforward.

Converting colour to luminance detects intensity edges. It does not preserve coloured edge directions. Very small images can be slower on the GPU once transfer and launch costs are included. The report separates the timing intervals to avoid implying that kernel speed is total application speed.

## Build and run

```sh
nvcc -O2 -arch=sm_75 lodepng.cpp SobelEdge.cu -o SobelEdge
mkdir -p outputs
./SobelEdge outputs images/shapes.png images/gradient.png images/checkerboard.png
```