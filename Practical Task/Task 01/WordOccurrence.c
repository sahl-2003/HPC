#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <errno.h>
#include <pthread.h>
#include <time.h>

struct WordCount {
    char *word;
    size_t count;
};

struct SharedData {
    char *text;
    size_t size, nextByte, sliceSize;
    int failed;
    pthread_mutex_t lock;
};

struct ThreadArgs {
    int threadIndex;
    struct SharedData *shared;
    struct WordCount *counts;
    size_t uniqueWords, totalWords, slices;
};

/* The same word rule is used at slice boundaries and while counting. */
int isWord(unsigned char c)
{
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
           (c >= '0' && c <= '9');
}

int compareWords(const void *a, const void *b)
{
    return strcmp(((const struct WordCount *)a)->word,
                  ((const struct WordCount *)b)->word);
}

void setFailure(struct SharedData *shared)
{
    pthread_mutex_lock(&shared->lock);
    shared->failed = 1;
    pthread_mutex_unlock(&shared->lock);
}

void *countWords(void *p)
{
    struct ThreadArgs *args = (struct ThreadArgs *)p;
    struct SharedData *shared = args->shared;
    size_t capacity = 0;

    for (;;) {
        size_t start, finish;
        /* Only claiming a slice needs a lock. Counting is thread local. */
        pthread_mutex_lock(&shared->lock);
        if (shared->failed || shared->nextByte == shared->size) {
            pthread_mutex_unlock(&shared->lock);
            break;
        }
        start = shared->nextByte;
        finish = start + (shared->sliceSize < shared->size - start ?
                          shared->sliceSize : shared->size - start);
        /* Extend the slice so a word is never cut between two threads. */
        while (finish < shared->size && isWord((unsigned char)shared->text[finish]))
            finish++;
        shared->nextByte = finish;
        pthread_mutex_unlock(&shared->lock);
        args->slices++;

        for (size_t i = start; i < finish;) {
            if (!isWord((unsigned char)shared->text[i])) { i++; continue; }
            size_t first = i;
            while (i < finish && isWord((unsigned char)shared->text[i])) i++;
            size_t length = i - first;
            char *word = (char *)malloc(length + 1);
            if (!word) { setFailure(shared); goto done; }
            for (size_t j = 0; j < length; j++) {
                unsigned char c = (unsigned char)shared->text[first + j];
                word[j] = (char)(c >= 'A' && c <= 'Z' ? c + ('a' - 'A') : c);
            }
            word[length] = '\0';
            if (args->totalWords == capacity) {
                size_t next = capacity ? capacity * 2 : 256;
                if (next < capacity || next > SIZE_MAX / sizeof(*args->counts)) {
                    free(word); setFailure(shared); goto done;
                }
                struct WordCount *grown = realloc(args->counts, next * sizeof(*grown));
                if (!grown) { free(word); setFailure(shared); goto done; }
                args->counts = grown;
                capacity = next;
            }
            args->counts[args->totalWords].word = word;
            args->counts[args->totalWords++].count = 1;
        }
    }
done:
    if (args->totalWords) qsort(args->counts, args->totalWords, sizeof(*args->counts), compareWords);
    for (size_t i = 0; i < args->totalWords; i++) {
        if (args->uniqueWords && !strcmp(args->counts[args->uniqueWords - 1].word,
                                         args->counts[i].word)) {
            args->counts[args->uniqueWords - 1].count++;
            free(args->counts[i].word);
        } else {
            args->counts[args->uniqueWords++] = args->counts[i];
        }
    }
    return NULL;
}

int main(int argc, char *argv[])
{
    if (argc != 3) {
        fprintf(stderr, "Usage: %s input_file number_of_threads\n", argv[0]);
        return 1;
    }
    char *end;
    errno = 0;
    long requested = strtol(argv[2], &end, 10);
    if (errno || *end || end == argv[2] || requested < 1 || requested > 1024) {
        fprintf(stderr, "Thread count must be an integer from 1 to 1024.\n"); return 1;
    }
    FILE *fp = fopen(argv[1], "rb");
    if (!fp) { perror(argv[1]); return 1; }
    if (fseek(fp, 0, SEEK_END) || ftell(fp) < 0) {
        fprintf(stderr, "Cannot determine input size.\n"); fclose(fp); return 1;
    }
    long fileSize = ftell(fp);
    rewind(fp);
    char *text = malloc((size_t)fileSize + 1);
    if (!text) { fclose(fp); fprintf(stderr, "Not enough host memory.\n"); return 1; }
    size_t size = fread(text, 1, (size_t)fileSize, fp);
    int readError = ferror(fp);
    int closeError = fclose(fp);
    if (size != (size_t)fileSize || readError || closeError) {
        fprintf(stderr, "Error reading input file.\n"); free(text); return 1;
    }
    text[size] = '\0';
    int threadCount = (int)requested;
    if (size && (size_t)threadCount > size) threadCount = (int)size;
    if (!size) threadCount = 1;
    struct SharedData shared;
    memset(&shared, 0, sizeof(shared));
    shared.text = text; shared.size = size;
    shared.sliceSize = size / ((size_t)threadCount * 8);
    if (!shared.sliceSize) shared.sliceSize = 1;
    if (pthread_mutex_init(&shared.lock, NULL)) {
        free(text); fprintf(stderr, "Mutex initialisation failed.\n"); return 1;
    }
    pthread_t *tids = malloc((size_t)threadCount * sizeof(*tids));
    struct ThreadArgs *args = calloc((size_t)threadCount, sizeof(*args));
    struct WordCount *merged = NULL;
    int status = 1, created = 0;
    if (!tids || !args) { fprintf(stderr, "Not enough thread memory.\n"); goto cleanup; }
    struct timespec begin, finish;
    clock_gettime(CLOCK_MONOTONIC, &begin);
    for (int i = 0; i < threadCount; i++) {
        args[i].threadIndex = i;
        args[i].shared = &shared;
        int error = pthread_create(&tids[i], NULL, countWords, &args[i]);
        if (error) {
            fprintf(stderr, "pthread_create: %s\n", strerror(error)); setFailure(&shared); break;
        }
        created++;
    }
    for (int i = 0; i < created; i++) {
        int error = pthread_join(tids[i], NULL);
        if (error) { fprintf(stderr, "pthread_join: %s\n", strerror(error)); exit(1); }
    }
    if (shared.failed || created != threadCount) goto cleanup;
    size_t entries = 0, total = 0;
    for (int i = 0; i < threadCount; i++) {
        entries += args[i].uniqueWords;
        total += args[i].totalWords;
    }
    if (entries > SIZE_MAX / sizeof(*merged)) goto cleanup;
    merged = malloc((entries ? entries : 1) * sizeof(*merged));
    if (!merged) { fprintf(stderr, "Not enough merge memory.\n"); goto cleanup; }
    size_t at = 0;
    for (int i = 0; i < threadCount; i++)
        for (size_t j = 0; j < args[i].uniqueWords; j++) merged[at++] = args[i].counts[j];
    if (entries) qsort(merged, entries, sizeof(*merged), compareWords);
    size_t unique = 0;
    for (size_t i = 0; i < entries; i++) {
        if (unique && !strcmp(merged[unique - 1].word, merged[i].word))
            merged[unique - 1].count += merged[i].count;
        else merged[unique++] = merged[i];
    }
    clock_gettime(CLOCK_MONOTONIC, &finish);
    double seconds = finish.tv_sec - begin.tv_sec + (finish.tv_nsec - begin.tv_nsec) / 1e9;
    fp = fopen("result.txt", "w");
    if (!fp) { perror("result.txt"); goto cleanup; }
    fprintf(fp, "Word\tFrequency\n");
    for (size_t i = 0; i < unique; i++) fprintf(fp, "%s\t%zu\n", merged[i].word, merged[i].count);
    int writeError = ferror(fp);
    closeError = fclose(fp);
    if (writeError || closeError) { fprintf(stderr, "Error writing result.txt.\n"); goto cleanup; }
    for (int i = 0; i < threadCount; i++)
        printf("Thread %d: %zu slices, %zu words\n", i, args[i].slices, args[i].totalWords);
    printf("Requested threads: %ld; actual threads: %d\n", requested, threadCount);
    printf("Total words: %zu; unique words: %zu\n", total, unique);
    printf("Counting and merge time: %.6f seconds\nOutput: result.txt\n", seconds);
    status = 0;
cleanup:
    if (args) for (int i = 0; i < threadCount; i++) {
        for (size_t j = 0; j < args[i].uniqueWords; j++) free(args[i].counts[j].word);
        free(args[i].counts);
    }
    free(merged); free(args); free(tids); free(text);
    pthread_mutex_destroy(&shared.lock);
    return status;
}
