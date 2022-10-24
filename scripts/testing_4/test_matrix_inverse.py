from gwfish_matrix_inverse import invertSVD
import numpy as np
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays

@given(arrays(np.float64, (2, 2), elements=st.floats(min_value=1e-20)))
def test_matrix_inversion_hypothesis(matrix):
    
    # matrix = np.maximum(matrix, matrix.T)
    
    inverse = np.linalg.inv(matrix)
    # inverse = invertSVD(matrix)

    assert np.allclose(inverse@matrix, np.eye(*matrix.shape))
    assert np.allclose(matrix@inverse, np.eye(*matrix.shape))
