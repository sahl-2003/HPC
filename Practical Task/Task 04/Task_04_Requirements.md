# Task 04 requirements checked against the supplied brief

The source is `Assignment/6CS005 - Assessment 25-26.docx`, Task 04,
"Sobel Edge Detection using Cuda across many PNG images".

Its final illustration shows four views of one input image:

1. Original Image
2. Gradient in X direction
3. Gradient in Y direction
4. Sobel Edge Detection

It does not set an exact count of four input PNGs. This project processes three
public demonstration images in one invocation and displays these four views for
every image. The command accepts more PNGs when needed.

The written description defines Gx as intensity changes from left to right and
Gy as changes from top to bottom. The implementation follows those definitions:

```text
Gx = -1  0  1       Gy = -1 -2 -1
     -2  0  2             0  0  0
     -1  0  1             1  2  1
```

One embedded kernel diagram exchanges the Gx/Gy labels. The brief explicitly
allows changed signs or flipped kernels because the combined magnitude is
unchanged. The code and captions consistently use the written axis definitions.

Each pixel uses its 3x3 neighbourhood with zero-valued samples outside the
image. The output keeps the input width and height. The final calculation is
`sqrt(Gx*Gx + Gy*Gy)`, using the signed convolution sums before any display
conversion. The brief's example Gx=6, Gy=8 therefore gives magnitude 10.

The separate gradient PNGs display `min(255, abs(Gx))` and
`min(255, abs(Gy))`. They use 8-bit grayscale pixel buffers and the lecturer's
`lodepng_encode_file(..., LCT_GREY, 8)` workflow. The final Sobel PNG uses the
clamped magnitude in RGB and retains the input alpha channel.

| Marking criterion | Implementation |
| --- | --- |
| Read PNG image(s) into CPU memory (5 marks) | LodePNG decode into `c_inImg` |
| Allocate GPU memory and transfer input (20 marks) | Size-based `cudaMalloc` and host-to-device `cudaMemcpy` |
| Detect edges in the CUDA kernel (35 marks) | One pixel per thread; complete Gx and Gy 3x3 calculations; zero padding and magnitude |
| Transfer the output safely to the CPU (20 marks) | Checked completion and device-to-host copies of the edge and two gradient maps |
| Write output PNG image(s) (15 marks) | `outImg_`, `outImg_Gx_` and `outImg_Gy_` followed by the input basename |
| Free CPU and GPU memory (5 marks) | Host arrays, device arrays and timing events released on success and failure |

The brief does not prescribe fixed Task 04 filenames. The existing
`SobelEdge.cu` and `outImg_` naming pattern is retained, with clear X/Y names.
For `download.png`, the saved files are `outImg_download.png`,
`outImg_Gx_download.png` and `outImg_Gy_download.png`.

The assessed calculations use C and CUDA. Python downloads the public input
files, displays the four views and performs independent checks. It does not
replace the CUDA convolution with an image-processing library.
