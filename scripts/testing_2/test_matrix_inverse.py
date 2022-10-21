from gwfish_matrix_inverse import invertSVD
import numpy as np

def test_matrix_inversion():

    matrix = np.array([[1, 3], [3, 4]])
    inverse = invertSVD(matrix)

    inverse_should_be = np.array([[-4/5, 3/5], [3/5, -1/5]])
    assert np.allclose(inverse, inverse_should_be)

if __name__ == '__main__':
    test_matrix_inversion()