#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <limits.h>
#include <errno.h>
#include <ctype.h>
#include <math.h>
#include <omp.h>

struct Matrix {
    int rows, cols;
    double **values;
};

void freeMatrix(struct Matrix *m)
{
    if (m->values) {
        for (int i = 0; i < m->rows; i++) free(m->values[i]);
        free(m->values);
    }
    m->values = NULL;
}

int allocateMatrix(struct Matrix *m, int rows, int cols)
{
    m->rows = rows; m->cols = cols; m->values = NULL;
    if (rows < 1 || cols < 1 || (size_t)rows > SIZE_MAX / sizeof(double *) ||
        (size_t)cols > SIZE_MAX / sizeof(double) ||
        (size_t)rows > SIZE_MAX / ((size_t)cols * sizeof(double))) return 0;
    m->values = malloc((size_t)rows * sizeof(double *));
    if (!m->values) return 0;
    for (int i = 0; i < rows; i++) m->values[i] = NULL;
    for (int i = 0; i < rows; i++) {
        m->values[i] = malloc((size_t)cols * sizeof(double));
        if (!m->values[i]) { freeMatrix(m); return 0; }
    }
    return 1;
}

/* fscanf reads the file; a growable line keeps row boundaries significant. */
int readLine(FILE *fp, char **line, size_t *capacity, size_t *lineNumber)
{
    size_t length = 0;
    char c;
    int found = 0;
    while (fscanf(fp, "%c", &c) == 1) {
        found = 1;
        if (c == '\n') break;
        if (length + 1 >= *capacity) {
            size_t next = *capacity ? *capacity * 2 : 256;
            if (next <= *capacity) return -1;
            char *grown = realloc(*line, next);
            if (!grown) return -1;
            *line = grown; *capacity = next;
        }
        (*line)[length++] = c;
    }
    if (ferror(fp)) return -1;
    if (!found) return 0;
    if (!*line) {
        *line = malloc(1); *capacity = 1;
        if (!*line) return -1;
    }
    (*line)[length] = '\0';
    (*lineNumber)++;
    return 1;
}

char *skipSpaces(char *p)
{
    while (isspace((unsigned char)*p)) p++;
    return p;
}

int parseHeader(char *line, int *rows, int *cols)
{
    char *p = skipSpaces(line), *end;
    errno = 0;
    long r = strtol(p, &end, 10);
    if (p == end || errno || r < 1 || r > INT_MAX) return 0;
    p = skipSpaces(end);
    if (*p++ != ',') return 0;
    p = skipSpaces(p);
    errno = 0;
    long c = strtol(p, &end, 10);
    if (p == end || errno || c < 1 || c > INT_MAX || *skipSpaces(end)) return 0;
    *rows = (int)r; *cols = (int)c;
    return 1;
}

int parseRow(char *line, double *row, int cols)
{
    char *p = line, *end;
    for (int j = 0; j < cols; j++) {
        p = skipSpaces(p);
        errno = 0;
        row[j] = strtod(p, &end);
        if (p == end || errno || !isfinite(row[j])) return 0;
        p = skipSpaces(end);
        if (j < cols - 1) {
            if (*p != ',') return 0;
            p++;
        } else if (*p) return 0;
    }
    return 1;
}

int readMatrices(const char *filename, struct Matrix **matrices, size_t *count)
{
    FILE *fp = fopen(filename, "r");
    if (!fp) { perror(filename); return 0; }
    char *line = NULL;
    size_t capacity = 0, lineNumber = 0;
    int status = 0, lineStatus;
    struct Matrix current = {0, 0, NULL};
    while ((lineStatus = readLine(fp, &line, &capacity, &lineNumber)) > 0) {
        if (!*skipSpaces(line)) continue;
        int rows, cols;
        if (!parseHeader(line, &rows, &cols)) {
            fprintf(stderr, "Line %zu: invalid matrix header; expected positive rows,cols.\n", lineNumber);
            goto cleanup;
        }
        if (!allocateMatrix(&current, rows, cols)) {
            fprintf(stderr, "Line %zu: matrix dimensions exceed available memory.\n", lineNumber);
            goto cleanup;
        }
        for (int i = 0; i < rows; i++) {
            lineStatus = readLine(fp, &line, &capacity, &lineNumber);
            if (lineStatus <= 0 || !parseRow(line, current.values[i], cols)) {
                fprintf(stderr, "Matrix %zu, row %d (near line %zu): expected exactly %d numeric comma-separated values.\n",
                        *count + 1, i + 1, lineNumber, cols);
                goto cleanup;
            }
        }
        if (*count == SIZE_MAX / sizeof(**matrices)) goto cleanup;
        struct Matrix *grown = realloc(*matrices, (*count + 1) * sizeof(*grown));
        if (!grown) { fprintf(stderr, "Not enough matrix list memory.\n"); goto cleanup; }
        *matrices = grown;
        (*matrices)[(*count)++] = current;
        current.values = NULL;
    }
    if (lineStatus < 0) { fprintf(stderr, "Input read or allocation error.\n"); goto cleanup; }
    if (!*count || *count % 2) {
        fprintf(stderr, "Input must contain a non-empty, even number of matrices; found %zu.\n", *count);
        goto cleanup;
    }
    status = 1;
cleanup:
    freeMatrix(&current); free(line);
    if (fclose(fp)) status = 0;
    return status;
}

void writeMatrix(FILE *fp, const char *name, const struct Matrix *m)
{
    fprintf(fp, "%s - %d,%d\n", name, m->rows, m->cols);
    for (int i = 0; i < m->rows; i++) {
        for (int j = 0; j < m->cols; j++) {
            if (j) fprintf(fp, ",");
            if (isnan(m->values[i][j])) fprintf(fp, "NaN");
            else fprintf(fp, "%.17g", m->values[i][j]);
        }
        fprintf(fp, "\n");
    }
    fprintf(fp, "\n");
}

/* 0..3 element-wise, 4/5 transposes, 6 the matrix product. */
int operation(FILE *fp, const struct Matrix *a, const struct Matrix *b, int op, int requested)
{
    const char *names[] = {"Addition", "Subtraction", "Element-wise multiplication",
        "Element-wise division", "Transpose A", "Transpose B", "Matrix multiplication"};
    if (op < 4 && (a->rows != b->rows || a->cols != b->cols)) {
        fprintf(fp, "%s cannot be done (shapes differ).\n\n", names[op]); return 1;
    }
    if (op == 6 && a->cols != b->rows) {
        fprintf(fp, "%s cannot be done (A.cols != B.rows).\n\n", names[op]); return 1;
    }
    const struct Matrix *source = op == 5 ? b : a;
    int transpose = op == 4 || op == 5;
    int rows = transpose ? source->cols : a->rows;
    int cols = transpose ? source->rows : (op == 6 ? b->cols : a->cols);
    struct Matrix result = {0, 0, NULL};
    if (!allocateMatrix(&result, rows, cols)) {
        fprintf(stderr, "Cannot allocate %s result.\n", names[op]); return 0;
    }
    int threadCount = requested < rows ? requested : rows;
    int actualThreads = 1;
    double begin = omp_get_wtime();
    #pragma omp parallel num_threads(threadCount) shared(result, actualThreads)
    {
        #pragma omp single
        actualThreads = omp_get_num_threads();
        #pragma omp for schedule(static)
        for (int i = 0; i < rows; i++) {
            for (int j = 0; j < cols; j++) {
                if (transpose) result.values[i][j] = source->values[j][i];
                else if (op == 0) result.values[i][j] = a->values[i][j] + b->values[i][j];
                else if (op == 1) result.values[i][j] = a->values[i][j] - b->values[i][j];
                else if (op == 2) result.values[i][j] = a->values[i][j] * b->values[i][j];
                else if (op == 3) result.values[i][j] = b->values[i][j] == 0.0 ? NAN : a->values[i][j] / b->values[i][j];
                else {
                    double sum = 0.0; /* A separate sum for each output cell. */
                    for (int k = 0; k < a->cols; k++) sum += a->values[i][k] * b->values[k][j];
                    result.values[i][j] = sum;
                }
            }
        }
    }
    double seconds = omp_get_wtime() - begin;
    printf("%s: %dx%d; threads requested=%d capped=%d actual=%d; compute=%.6f s\n",
           names[op], rows, cols, requested, threadCount, actualThreads, seconds);
    writeMatrix(fp, names[op], &result);
    freeMatrix(&result);
    return !ferror(fp);
}

int main(int argc, char *argv[])
{
    if (argc != 3) {
        fprintf(stderr, "Usage: %s input_file number_of_threads\n", argv[0]); return 1;
    }
    char *end;
    errno = 0;
    long requested = strtol(argv[2], &end, 10);
    if (errno || end == argv[2] || *end || requested < 1 || requested > INT_MAX) {
        fprintf(stderr, "Thread count must be a positive integer.\n"); return 1;
    }
    struct Matrix *matrices = NULL;
    size_t count = 0;
    int status = 1;
    FILE *output = NULL;
    if (!readMatrices(argv[1], &matrices, &count)) goto cleanup;
    output = fopen("results.txt", "w");
    if (!output) { perror("results.txt"); goto cleanup; }
    omp_set_dynamic(0);
    for (size_t pair = 0; pair < count / 2; pair++) {
        const struct Matrix *a = &matrices[pair * 2], *b = &matrices[pair * 2 + 1];
        fprintf(output, "Pair %zu: A=%d,%d B=%d,%d\n\n", pair + 1, a->rows, a->cols, b->rows, b->cols);
        printf("\nPair %zu: A=%dx%d B=%dx%d\n", pair + 1, a->rows, a->cols, b->rows, b->cols);
        for (int op = 0; op < 7; op++)
            if (!operation(output, a, b, op, (int)requested)) goto cleanup;
    }
    if (ferror(output)) goto cleanup;
    status = 0;
    printf("\nProcessed %zu matrices in %zu pairs. Output: results.txt\n", count, count / 2);
cleanup:
    if (output && fclose(output)) { fprintf(stderr, "Error closing results.txt.\n"); status = 1; }
    for (size_t i = 0; i < count; i++) freeMatrix(&matrices[i]);
    free(matrices);
    return status;
}
