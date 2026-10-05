#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <limits.h>
#include <cuda_runtime.h>

/* Exact character transformation supplied in CryptForCuda.c.
   Each caller provides its own buffer; a shared static buffer would race. */
__host__ __device__ void cudaCrypt(const char *rawPassword, char *newPassword)
{
    newPassword[0] = rawPassword[0] + 2;
    newPassword[1] = rawPassword[0] - 2;
    newPassword[2] = rawPassword[0] + 1;
    newPassword[3] = rawPassword[1] + 3;
    newPassword[4] = rawPassword[1] - 3;
    newPassword[5] = rawPassword[1] - 1;
    newPassword[6] = rawPassword[2] + 2;
    newPassword[7] = rawPassword[2] - 2;
    newPassword[8] = rawPassword[3] + 4;
    newPassword[9] = rawPassword[3] - 4;
    newPassword[10] = '\0';
    for (int i = 0; i < 10; i++) {
        if (i < 6) {
            if (newPassword[i] > 122) newPassword[i] = (newPassword[i] - 122) + 97;
            else if (newPassword[i] < 97) newPassword[i] = (97 - newPassword[i]) + 97;
        } else {
            if (newPassword[i] > 57) newPassword[i] = (newPassword[i] - 57) + 48;
            else if (newPassword[i] < 48) newPassword[i] = (48 - newPassword[i]) + 48;
        }
    }
}

__device__ int matches(const char *a, const char *b, int length)
{
    for (int i = 0; i < length; i++) if (a[i] != b[i]) return 0;
    return 1;
}

__global__ void crackPasswords(const char *encrypted, char *decrypted, int *found, int count)
{
    size_t threadID = (size_t)blockIdx.x * blockDim.x + threadIdx.x;
    if (threadID >= (size_t)count) return;
    const char *target = encrypted + threadID * 11;
    char rawPassword[5] = {'a', 'a', '0', '0', '\0'};
    char candidate[11];
    found[threadID] = 0;
    for (int i = 0; i < 5; i++) decrypted[threadID * 5 + i] = '\0';

    for (int a = 0; a < 26; a++) {
        rawPassword[0] = (char)('a' + a);
        for (int b = 0; b < 26; b++) {
            rawPassword[1] = (char)('a' + b);
            cudaCrypt(rawPassword, candidate);
            /* Digits cannot change the first six encrypted characters.
               Reject the letter pair before trying its 100 digit pairs. */
            if (!matches(candidate, target, 6)) continue;
            for (int c = 0; c < 10; c++) {
                rawPassword[2] = (char)('0' + c);
                for (int d = 0; d < 10; d++) {
                    rawPassword[3] = (char)('0' + d);
                    cudaCrypt(rawPassword, candidate);
                    if (matches(candidate, target, 10)) {
                        for (int i = 0; i < 5; i++) decrypted[threadID * 5 + i] = rawPassword[i];
                        found[threadID] = 1;
                        return;
                    }
                }
            }
        }
    }
}

int checkCuda(cudaError_t error, const char *action)
{
    if (error == cudaSuccess) return 1;
    fprintf(stderr, "CUDA %s: %s\n", action, cudaGetErrorString(error));
    return 0;
}

int readPasswords(const char *filename, char **passwords, int *count)
{
    FILE *fp = fopen(filename, "r");
    if (!fp) { perror(filename); return 0; }
    char line[32];
    size_t capacity = 0;
    int status = 0;
    while (fgets(line, sizeof(line), fp)) {
        size_t length = strlen(line);
        if (length && line[length - 1] == '\n') line[--length] = '\0';
        if (length && line[length - 1] == '\r') line[--length] = '\0';
        if (length != 10) {
            fprintf(stderr, "Line %d: expected exactly 10 encrypted characters.\n", *count + 1); goto cleanup;
        }
        for (int i = 0; i < 10; i++) {
            if ((i < 6 && (line[i] < 'a' || line[i] > 'z')) ||
                (i >= 6 && (line[i] < '0' || line[i] > '9'))) {
                fprintf(stderr, "Line %d: expected six lowercase letters and four digits.\n", *count + 1); goto cleanup;
            }
        }
        if (*count == INT_MAX || (size_t)*count >= SIZE_MAX / 11 - 1) {
            fprintf(stderr, "Too many password records.\n"); goto cleanup;
        }
        if ((size_t)*count == capacity) {
            size_t next = capacity ? capacity * 2 : 256;
            if (next > SIZE_MAX / 11) { fprintf(stderr, "Password size overflow.\n"); goto cleanup; }
            char *grown = (char *)realloc(*passwords, next * 11);
            if (!grown) { fprintf(stderr, "Not enough host memory.\n"); goto cleanup; }
            *passwords = grown; capacity = next;
        }
        memcpy(*passwords + (size_t)(*count) * 11, line, 11);
        (*count)++;
    }
    if (ferror(fp)) { fprintf(stderr, "Input read failed.\n"); goto cleanup; }
    if (!*count) { fprintf(stderr, "Password file is empty.\n"); goto cleanup; }
    status = 1;
cleanup:
    if (fclose(fp)) status = 0;
    return status;
}

int main(int argc, char *argv[])
{
    if (argc != 2) { fprintf(stderr, "Usage: %s encrypted_password_file\n", argv[0]); return 1; }
    char *c_encrypted = NULL, *c_decrypted = NULL;
    char *d_encrypted = NULL, *d_decrypted = NULL;
    int *c_found = NULL, *d_found = NULL;
    int count = 0, status = 1, recovered = 0;
    FILE *output = NULL;
    cudaEvent_t begin = NULL, finish = NULL;
    cudaDeviceProp device;
    if (!readPasswords(argv[1], &c_encrypted, &count)) goto cleanup;
    if (!checkCuda(cudaGetDeviceProperties(&device, 0), "device query")) goto cleanup;
    {
        size_t encryptedBytes = (size_t)count * 11;
        size_t decryptedBytes = (size_t)count * 5;
        size_t foundBytes = (size_t)count * sizeof(int);
        c_decrypted = (char *)malloc(decryptedBytes);
        c_found = (int *)malloc(foundBytes);
        if (!c_decrypted || !c_found) { fprintf(stderr, "Not enough result memory.\n"); goto cleanup; }
        if (!checkCuda(cudaMalloc((void **)&d_encrypted, encryptedBytes), "input allocation") ||
            !checkCuda(cudaMalloc((void **)&d_decrypted, decryptedBytes), "output allocation") ||
            !checkCuda(cudaMalloc((void **)&d_found, foundBytes), "status allocation")) goto cleanup;
        if (!checkCuda(cudaMemcpy(d_encrypted, c_encrypted, encryptedBytes, cudaMemcpyHostToDevice), "host to device")) goto cleanup;
        int threads = count < 512 ? (count + 1) / 2 : 256;
        if (threads > device.maxThreadsPerBlock) threads = device.maxThreadsPerBlock;
        unsigned int blocks = (unsigned int)(((size_t)count + threads - 1) / threads);
        if (blocks < 2) blocks = 2;
        if (blocks > (unsigned int)device.maxGridSize[0]) {
            fprintf(stderr, "Password file exceeds this device's x grid limit.\n"); goto cleanup;
        }
        printf("GPU: %s\nPasswords: %d; x blocks: %u; threads per block: %d\n", device.name, count, blocks, threads);
        if (!checkCuda(cudaEventCreate(&begin), "start event") || !checkCuda(cudaEventCreate(&finish), "end event") ||
            !checkCuda(cudaEventRecord(begin), "record start")) goto cleanup;
        crackPasswords<<<blocks, threads>>>(d_encrypted, d_decrypted, d_found, count);
        if (!checkCuda(cudaGetLastError(), "kernel launch") || !checkCuda(cudaEventRecord(finish), "record end") ||
            !checkCuda(cudaDeviceSynchronize(), "kernel execution")) goto cleanup;
        float milliseconds;
        if (!checkCuda(cudaEventElapsedTime(&milliseconds, begin, finish), "kernel timing") ||
            !checkCuda(cudaMemcpy(c_decrypted, d_decrypted, decryptedBytes, cudaMemcpyDeviceToHost), "output to host") ||
            !checkCuda(cudaMemcpy(c_found, d_found, foundBytes, cudaMemcpyDeviceToHost), "status to host")) goto cleanup;
        printf("CUDA kernel time: %.3f ms\n", milliseconds);
    }
    output = fopen("decrypted.txt", "w");
    if (!output) { perror("decrypted.txt"); goto cleanup; }
    for (int i = 0; i < count; i++) {
        char verified[11];
        if (c_found[i]) {
            cudaCrypt(c_decrypted + (size_t)i * 5, verified);
            if (strcmp(verified, c_encrypted + (size_t)i * 11)) {
                fprintf(stderr, "Host verification failed on line %d.\n", i + 1); goto cleanup;
            }
            recovered++;
        }
        const char *answer = c_found[i] ? c_decrypted + (size_t)i * 5 : "NOT_FOUND";
        fprintf(output, "%s\n", answer);
        if (i < 10) printf("Line %d: %s -> %s\n", i + 1, c_encrypted + (size_t)i * 11, answer);
    }
    if (ferror(output)) { fprintf(stderr, "Error writing decrypted.txt.\n"); goto cleanup; }
    printf("Recovered and verified: %d/%d. Output: decrypted.txt\n", recovered, count);
    status = recovered == count ? 0 : 2;
cleanup:
    if (output && fclose(output)) status = 1;
    if (d_encrypted && !checkCuda(cudaFree(d_encrypted), "free input")) status = 1;
    if (d_decrypted && !checkCuda(cudaFree(d_decrypted), "free output")) status = 1;
    if (d_found && !checkCuda(cudaFree(d_found), "free status")) status = 1;
    if (begin && !checkCuda(cudaEventDestroy(begin), "destroy start event")) status = 1;
    if (finish && !checkCuda(cudaEventDestroy(finish), "destroy end event")) status = 1;
    free(c_encrypted); free(c_decrypted); free(c_found);
    return status;
}
