#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int rows;
    int cols;
    double *data;
} Matrix;

Matrix *matrix_create(int rows, int cols) {
    Matrix *m = malloc(sizeof(Matrix));
    m->rows = rows;
    m->cols = cols;
    m->data = calloc(rows * cols, sizeof(double));
    return m;
}

void matrix_free(Matrix *m) {
    free(m->data);
    free(m);
}

double matrix_get(const Matrix *m, int row, int col) {
    return m->data[row * m->cols + col];
}

void matrix_set(Matrix *m, int row, int col, double value) {
    m->data[row * m->cols + col] = value;
}

Matrix *matrix_multiply(const Matrix *a, const Matrix *b) {
    Matrix *result = matrix_create(a->rows, b->cols);
    for (int i = 0; i < a->rows; i++) {
        for (int j = 0; j < b->cols; j++) {
            double sum = 0.0;
            for (int k = 0; k < a->cols; k++) {
                sum += matrix_get(a, i, k) * matrix_get(b, k, j);
            }
            matrix_set(result, i, j, sum);
        }
    }
    return result;
}

int main(void) {
    Matrix *a = matrix_create(2, 2);
    matrix_set(a, 0, 0, 1.0);
    matrix_set(a, 0, 1, 2.0);
    matrix_set(a, 1, 0, 3.0);
    matrix_set(a, 1, 1, 4.0);

    Matrix *b = matrix_create(2, 2);
    matrix_set(b, 0, 0, 5.0);
    matrix_set(b, 0, 1, 6.0);
    matrix_set(b, 1, 0, 7.0);
    matrix_set(b, 1, 1, 8.0);

    Matrix *c = matrix_multiply(a, b);

    for (int i = 0; i < c->rows; i++) {
        for (int j = 0; j < c->cols; j++) {
            printf("%.1f ", matrix_get(c, i, j));
        }
        printf("\n");
    }

    matrix_free(a);
    matrix_free(b);
    matrix_free(c);
    return 0;
}
