import numpy as np

def invertSVD(matrix):
    thresh = 1e-10

    dm = np.sqrt(np.diag(matrix))
    normalizer = np.outer(dm, dm)
    matrix_norm = matrix / normalizer

    [U, S, Vh] = np.linalg.svd(matrix_norm)

    kVal = sum(S > thresh)
    matrix_inverse_norm = U[:, 0:kVal] @ np.diag(1. / S[0:kVal]) @ Vh[0:kVal, :]

    return matrix_inverse_norm / normalizer

def test_matrix_inversion():

    matrix = np.array([[1, 3], [3, 4]])
    inverse = invertSVD(matrix)

    inverse_should_be = np.array([[-4/5, 3/5], [3/5, -1/5]])
    return np.allclose(inverse, inverse_should_be)

if __name__ == '__main__':
    print(test_matrix_inversion())