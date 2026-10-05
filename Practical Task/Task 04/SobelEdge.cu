#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <limits.h>
#include <math.h>
#include <time.h>
#include <sys/stat.h>
#include <cuda_runtime.h>
#include "lodepng.h"

__host__ __device__ int grey(const unsigned char *pixel)
{
    return (77 * (int)pixel[0] + 150 * (int)pixel[1] + 29 * (int)pixel[2]) >> 8;
}

__global__ void sobelEdge(const unsigned char *inImg, unsigned char *outImg, int width, int height)
{
    size_t threadID = (size_t)blockIdx.x * blockDim.x + threadIdx.x;
    if (threadID >= (size_t)width * height) return;
    int x = (int)(threadID % width);
    int y = (int)(threadID / width);
    const int gxKernel[3][3] = {{-1, 0, 1}, {-2, 0, 2}, {-1, 0, 1}};
    const int gyKernel[3][3] = {{-1, -2, -1}, {0, 0, 0}, {1, 2, 1}};
    int gx = 0, gy = 0;
    for (int row = -1; row <= 1; row++) {
        for (int col = -1; col <= 1; col++) {
            int nx = x + col, ny = y + row;
            int value = 0; /* Zero padding outside the image. */
            if (nx >= 0 && nx < width && ny >= 0 && ny < height)
                value = grey(inImg + ((size_t)ny * width + nx) * 4);
            gx += value * gxKernel[row + 1][col + 1];
            gy += value * gyKernel[row + 1][col + 1];
        }
    }
    int magnitude = (int)sqrtf((float)(gx * gx + gy * gy));
    unsigned char edge = (unsigned char)(magnitude > 255 ? 255 : magnitude);
    size_t pixel = threadID * 4;
    outImg[pixel] = edge;
    outImg[pixel + 1] = edge;
    outImg[pixel + 2] = edge;
    outImg[pixel + 3] = inImg[pixel + 3];
}

/* A serial reference expands the two kernels into their neighbour sums. */
void sobelCPU(const unsigned char *input, unsigned char *output, int width, int height)
{
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int neighbourhood[3][3] = {{0}};
            for (int r = 0; r < 3; r++) for (int c = 0; c < 3; c++) {
                int nx = x + c - 1, ny = y + r - 1;
                if (nx >= 0 && nx < width && ny >= 0 && ny < height)
                    neighbourhood[r][c] = grey(input + ((size_t)ny * width + nx) * 4);
            }
            int gx = -neighbourhood[0][0] + neighbourhood[0][2]
                   - 2 * neighbourhood[1][0] + 2 * neighbourhood[1][2]
                   - neighbourhood[2][0] + neighbourhood[2][2];
            int gy = -neighbourhood[0][0] - 2 * neighbourhood[0][1] - neighbourhood[0][2]
                   + neighbourhood[2][0] + 2 * neighbourhood[2][1] + neighbourhood[2][2];
            int magnitude = (int)sqrtf((float)(gx * gx + gy * gy));
            size_t pixel = ((size_t)y * width + x) * 4;
            output[pixel] = output[pixel + 1] = output[pixel + 2] =
                (unsigned char)(magnitude > 255 ? 255 : magnitude);
            output[pixel + 3] = input[pixel + 3];
        }
    }
}

int checkCuda(cudaError_t error, const char *action)
{
    if (error == cudaSuccess) return 1;
    fprintf(stderr, "CUDA %s: %s\n", action, cudaGetErrorString(error)); return 0;
}

double wallTime(void)
{
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    return now.tv_sec + now.tv_nsec / 1e9;
}

int processImage(const char *inputName, const char *outputName)
{
    unsigned char *c_inImg = NULL, *c_outImg = NULL, *c_reference = NULL;
    unsigned char *d_inImg = NULL, *d_outImg = NULL;
    unsigned int width = 0, height = 0;
    int status = 0;
    cudaEvent_t begin = NULL, finish = NULL;
    unsigned int pngError = lodepng_decode32_file(&c_inImg, &width, &height, inputName);
    if (pngError) {
        fprintf(stderr, "%s: PNG decode error %u: %s\n", inputName, pngError, lodepng_error_text(pngError));
        goto cleanup;
    }
    if (!width || !height || width > INT_MAX || height > INT_MAX ||
        (size_t)width > SIZE_MAX / 4 / height) {
        fprintf(stderr, "%s: unsupported image dimensions.\n", inputName); goto cleanup;
    }
    {
        size_t pixels = (size_t)width * height;
        size_t bytes = pixels * 4;
        cudaDeviceProp device;
        if (!checkCuda(cudaGetDeviceProperties(&device, 0), "device query")) goto cleanup;
        int threads = 256;
        if (threads > device.maxThreadsPerBlock) threads = device.maxThreadsPerBlock;
        size_t blocks = (pixels + threads - 1) / threads;
        if (blocks > (size_t)device.maxGridSize[0]) {
            fprintf(stderr, "%s: image exceeds the device grid limit.\n", inputName); goto cleanup;
        }
        c_outImg = (unsigned char *)malloc(bytes);
        c_reference = (unsigned char *)malloc(bytes);
        if (!c_outImg || !c_reference) { fprintf(stderr, "Not enough host image memory.\n"); goto cleanup; }
        if (!checkCuda(cudaMalloc((void **)&d_inImg, bytes), "input allocation") ||
            !checkCuda(cudaMalloc((void **)&d_outImg, bytes), "output allocation") ||
            !checkCuda(cudaEventCreate(&begin), "start event") ||
            !checkCuda(cudaEventCreate(&finish), "end event")) goto cleanup;
        double gpuStart = wallTime();
        if (!checkCuda(cudaMemcpy(d_inImg, c_inImg, bytes, cudaMemcpyHostToDevice), "host to device") ||
            !checkCuda(cudaEventRecord(begin), "record start")) goto cleanup;
        sobelEdge<<<(unsigned int)blocks, threads>>>(d_inImg, d_outImg, (int)width, (int)height);
        if (!checkCuda(cudaGetLastError(), "kernel launch") ||
            !checkCuda(cudaEventRecord(finish), "record end") ||
            !checkCuda(cudaDeviceSynchronize(), "kernel execution") ||
            !checkCuda(cudaMemcpy(c_outImg, d_outImg, bytes, cudaMemcpyDeviceToHost), "device to host")) goto cleanup;
        double gpuMilliseconds = (wallTime() - gpuStart) * 1000;
        float kernelMilliseconds;
        if (!checkCuda(cudaEventElapsedTime(&kernelMilliseconds, begin, finish), "kernel timing")) goto cleanup;
        double cpuStart = wallTime();
        sobelCPU(c_inImg, c_reference, (int)width, (int)height);
        double cpuMilliseconds = (wallTime() - cpuStart) * 1000;
        if (memcmp(c_outImg, c_reference, bytes)) {
            fprintf(stderr, "%s: GPU output differs from serial CPU reference.\n", inputName); goto cleanup;
        }
        pngError = lodepng_encode32_file(outputName, c_outImg, width, height);
        if (pngError) {
            fprintf(stderr, "%s: PNG encode error %u: %s\n", outputName, pngError, lodepng_error_text(pngError));
            goto cleanup;
        }
        printf("%s: %ux%u; %zu x blocks; %d threads/block\n", inputName, width, height, blocks, threads);
        printf("CPU compute: %.3f ms; CUDA kernel: %.3f ms; CUDA transfers + kernel: %.3f ms\n",
               cpuMilliseconds, kernelMilliseconds, gpuMilliseconds);
        printf("All RGBA bytes match CPU reference: PASS\nOutput: %s\n\n", outputName);
        status = 1;
    }
cleanup:
    if (d_inImg && !checkCuda(cudaFree(d_inImg), "free input")) status = 0;
    if (d_outImg && !checkCuda(cudaFree(d_outImg), "free output")) status = 0;
    if (begin && !checkCuda(cudaEventDestroy(begin), "destroy start event")) status = 0;
    if (finish && !checkCuda(cudaEventDestroy(finish), "destroy end event")) status = 0;
    free(c_inImg); free(c_outImg); free(c_reference);
    return status;
}

const char *baseName(const char *path)
{
    const char *slash = strrchr(path, '/');
    return slash ? slash + 1 : path;
}

int main(int argc, char *argv[])
{
    if (argc < 3) {
        fprintf(stderr, "Usage: %s output_directory image1.png [image2.png ...]\n", argv[0]); return 1;
    }
    struct stat directory;
    if (stat(argv[1], &directory) || !S_ISDIR(directory.st_mode)) {
        fprintf(stderr, "Output directory does not exist: %s\n", argv[1]); return 1;
    }
    /* Duplicate basenames would overwrite a previous image's result. */
    for (int i = 2; i < argc; i++) for (int j = 2; j < i; j++)
        if (!strcmp(baseName(argv[i]), baseName(argv[j]))) {
            fprintf(stderr, "Input images must have distinct basenames.\n"); return 1;
        }
    cudaDeviceProp device;
    if (!checkCuda(cudaGetDeviceProperties(&device, 0), "device query")) return 1;
    printf("GPU: %s\n\n", device.name);
    int completed = 0;
    for (int i = 2; i < argc; i++) {
        const char *name = baseName(argv[i]);
        size_t capacity = strlen(argv[1]) + strlen(name) + 16;
        char *outputName = (char *)malloc(capacity);
        if (!outputName) { fprintf(stderr, "Filename allocation failed.\n"); return 1; }
        snprintf(outputName, capacity, "%s/outImg_%s", argv[1], name);
        completed += processImage(argv[i], outputName);
        free(outputName);
    }
    printf("Successfully processed %d/%d PNG images.\n", completed, argc - 2);
    return completed == argc - 2 ? 0 : 1;
}
