# Task 04 Sobel Edge Detection using Cuda across many PNG images

Thaslim Mohammed Sahl | 2638120 | 6CS005

[Open task notebook in Colab](https://colab.research.google.com/github/sahl-2003/HPC/blob/main/Practical%20Task/Task%2004/Task_04.ipynb)

[Executed Colab notebook](https://colab.research.google.com/drive/1N2NxvodTA4TeiNAUY0JtYP0_kALg1uOE)

## Objective

Process multiple PNG inputs with CUDA and reproduce the brief's four views for each input: Original Image, Gradient in X direction, Gradient in Y direction and Sobel Edge Detection. The four panels illustrate one input; the brief does not specify exactly four different inputs. Save both gradient maps and the combined edge map at the original dimensions.


## Implementation

The notebook uses wget to download download.png (300x300) from the lecturer's public image URL, plus smarties.png (413x356) and sudoku.png (558x563) from pinned public OpenCV sample URLs. SHA-256 and PNG dimensions are checked before use; image_downloads.json records the source and load mode. These images require no private GitHub login or Drive mount. LodePNG decodes each file into an RGBA host array, with its original licence notices retained.

The last-class sample demonstrates PNG decoding, explicit CUDA memory transfers and rgbToGray; its final kernel stops at grayscale conversion. This implementation extends that workflow with the assessed Sobel convolution. Luminance uses the lecturer's 0.30R + 0.59G + 0.11B weights as (30*R + 59*G + 11*B) / 100, rounded down. Integer arithmetic gives identical CPU and GPU truncation. Gx is [-1,0,1; -2,0,2; -1,0,1] and Gy is [-1,-2,-1; 0,0,0; 1,2,1]. Out-of-image neighbours are zero.

Gx measures left-to-right intensity changes and Gy measures top-to-bottom changes, following the written axis definitions. The kernel saves min(255, abs(Gx)) and min(255, abs(Gy)) in separate one-byte-per-pixel display buffers. The final magnitude uses the original signed sums: sqrt(Gx*Gx + Gy*Gy), then truncation and saturation at 255. Clipping a display map never changes that calculation. The final edge value fills RGB and preserves input alpha; the separate gradient maps contain grayscale intensity only.

RGBA input and final output arrays each use width*height*4 bytes. Each gradient array uses width*height bytes. The x grid has ceil(pixel_count/256) blocks and a guard for padded threads. The command accepts any number of PNGs. Output names are outImg_, outImg_Gx_ and outImg_Gy_ followed by the input basename. The host rejects duplicate or colliding generated names before processing. Gradient encoding uses lodepng_encode_file with LCT_GREY, 8, matching the lecturer's grayscale-buffer workflow.


## Synchronisation and memory

Checked kernel completion precedes device-to-host copies of all three maps. A serial C reference expresses the gradients as neighbour sums and compares every final RGBA byte and both gradient buffers. An independent NumPy checker verifies all saved maps and their dimensions, including alpha in the final edge image.

Every successful output has exactly the original image dimensions. Zero padding can produce a visible edge around a constant bright image because its boundary neighbours are black. This is expected under the specified padding rule. PNG decode or encode failures and CUDA failures return errors; the batch can continue to a later valid input.

Images are processed one at a time. Host image and reference buffers, all four device buffers and timing events are released after each image, including failure paths. Working memory depends on the largest image. Gradients are encoded losslessly from 8-bit grayscale buffers; LodePNG can optimise the file's storage without changing its decoded intensities.


## Results and tests

The revised notebook downloaded all three demonstration PNGs live on the Tesla T4. Every pixel in all three saved maps matched the references across 19 PNG inputs. Fixtures cover zero padding, saturation, final-image transparency, grayscale rounding and padded launches, as well as the public images and original synthetic patterns.

Directional fixtures independently check that a horizontal ramp has zero interior Gy and a vertical ramp has zero interior Gx. Negative gradients remain visible through their absolute values. A constructed 3x3 patch gives Gx=6, Gy=8 and final magnitude 10 at its centre, reproducing the brief's numerical example. Corrupt files, invalid paths, duplicate inputs and cross-output filename collisions are also tested; a batch continues to a valid image after a corrupt one.

The updated 413x356 smarties.png run took 4.657 ms for serial CPU computation, 0.021 ms for the CUDA kernel, and 0.461 ms for transfers plus kernel. These are single-run observations. GPU allocation, PNG decoding and encoding are outside the transfer-and-kernel interval. The first CUDA invocation has additional startup overhead, so timings are not stable benchmark estimates.


## Performance and limits

The implementation uses global memory and a basic one-thread-per-pixel kernel, matching the taught CUDA model. It does not use shared-memory tiling or concurrent image streams. Reading overlapping neighbourhoods repeats memory accesses, but the independent output ownership makes correctness straightforward.

Converting colour to luminance detects intensity edges. It does not preserve coloured edge directions. Very small images can be slower on the GPU once transfer and launch costs are included. The report separates the timing intervals to avoid implying that kernel speed is total application speed.

## Build and run

```sh
nvcc -O2 -arch=sm_75 lodepng.cpp SobelEdge.cu -o SobelEdge
mkdir -p outputs
./SobelEdge outputs images/download.png images/smarties.png images/sudoku.png
```