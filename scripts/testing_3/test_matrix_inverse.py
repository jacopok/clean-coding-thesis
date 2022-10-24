from gwfish_matrix_inverse import invertSVD
import numpy as np

MATRIX = np.array([[1, 3], [3, 4]])

def test_matrix_inversion_constant_matrix(matrix = MATRIX):

    inverse = invertSVD(matrix)

    assert np.allclose(inverse@matrix, np.eye(*matrix.shape))
    assert np.allclose(matrix@inverse, np.eye(*matrix.shape))
