# Task 04 Sobel Edge Detection using Cuda across many PNG images

Thaslim Mohammed Sahl | 2638120 | 6CS005

[Open task notebook in Colab](https://colab.research.google.com/github/sahl-2003/HPC/blob/main/Practical%20Task/Task%2004/Task_04.ipynb)

[Executed Colab notebook](https://colab.research.google.com/drive/1N2NxvodTA4TeiNAUY0JtYP0_kALg1uOE)

## Objective

Decode multiple PNG images, apply the Sobel horizontal and vertical kernels on the GPU with zero padding, and save each resulting edge image with the original width, height and alpha channel.


## Implementation

The notebook uses wget to download download.png (300x300) from the lecturer's public image URL, plus smarties.png (413x356) and sudoku.png (558x563) from pinned public OpenCV sample URLs. SHA-256 and PNG dimensions are checked before use; image_downloads.json records the source and load mode. These images require no private GitHub login or Drive mount. LodePNG decodes each file into an RGBA host array, with its original licence notices retained.

The last-class sample demonstrates PNG decoding, explicit CUDA memory transfers and rgbToGray; its final kernel stops at grayscale conversion. This implementation extends that workflow with the assessed Sobel convolution. Luminance uses the lecturer's 0.30R + 0.59G + 0.11B weights as (30*R + 59*G + 11*B) / 100, rounded down. Integer arithmetic gives identical CPU and GPU truncation. Gx is [-1,0,1; -2,0,2; -1,0,1] and Gy is [-1,-2,-1; 0,0,0; 1,2,1]. Out-of-image neighbours are zero.

The edge magnitude is sqrt(Gx*Gx + Gy*Gy), truncated to an integer and capped at 255. That edge value is written to R, G and B; alpha is copied from the original pixel. Reading always uses the separate input buffer, so one pixel's output cannot change a neighbour's input.

GPU memory is sized as width*height*4 bytes for each input and output array. The x grid uses ceil(pixel_count/256) blocks, with a bounds guard in the kernel. The command accepts an output directory and any number of input images. Result names are outImg_ followed by the input basename. Distinct basenames avoid accidental overwriting.


## Synchronisation and memory

After launch and execution checks, the output is copied to the host. A serial C reference expresses the gradients as neighbour sums and compares every RGBA byte. An independent NumPy checker also uses padded image arrays and validates the complete output, including alpha.

Every successful output has exactly the original image dimensions. Zero padding can produce a visible edge around a constant bright image because its boundary neighbours are black. This is expected under the specified padding rule. PNG decode or encode failures and CUDA failures return errors; the batch can continue to a later valid input.

Images are processed one at a time, releasing host buffers, device buffers and events after each image. The CPU reference needs a third host array for verification. Peak working memory depends on the largest image, rather than the sum of every image in the batch.


## Results and tests

The updated notebook downloaded all three demonstration PNGs live from their public URLs on the Tesla T4. All pixels matched the serial C reference and independent NumPy oracle for fourteen PNGs: these three public inputs, three original synthetic patterns, 3x3 black and white inputs, a single pixel, a 6x4 input, random RGBA inputs of 2x5, 17x19 and 1025x2, and a coloured rounding fixture. That fixture detects the previous grayscale weights and checks changing alpha values. Tests covered zero padding, saturation, transparency and padded launch threads.

Corrupt PNGs, missing files, missing output directories and duplicate basenames were tested. A corrupt image followed by a valid image confirmed that the valid image still processed and the overall command reported the batch failure.

The updated 413x356 smarties.png run took 9.062 ms for serial CPU computation, 0.030 ms for the CUDA kernel, and 0.487 ms for transfers plus kernel. These are single-run observations. GPU allocation, PNG decoding and encoding are outside the transfer-and-kernel interval. The first CUDA invocation has additional startup overhead, so timings are not stable benchmark estimates.


## Performance and limits

The implementation uses global memory and a basic one-thread-per-pixel kernel, matching the taught CUDA model. It does not use shared-memory tiling or concurrent image streams. Reading overlapping neighbourhoods repeats memory accesses, but the independent output ownership makes correctness straightforward.

Converting colour to luminance detects intensity edges. It does not preserve coloured edge directions. Very small images can be slower on the GPU once transfer and launch costs are included. The report separates the timing intervals to avoid implying that kernel speed is total application speed.

## Build and run

```sh
nvcc -O2 -arch=sm_75 lodepng.cpp SobelEdge.cu -o SobelEdge
mkdir -p outputs
./SobelEdge outputs images/download.png images/smarties.png images/sudoku.png
```