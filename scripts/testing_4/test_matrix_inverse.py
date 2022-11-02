from gwfish_matrix_inverse import invertSVD
import numpy as np
from hypothesis import given, reject, target, seed
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays
import pytest

MATRIX_DIMENSION=4
ABS_TOLERANCE=1e-1
REL_TOLERANCE=1e-2
MIN_NORM=1e-5
MAX_NORM=1e5


@seed(1)
@given(
    vector_norms=arrays(
        np.float64, 
        (MATRIX_DIMENSION,), 
        elements=st.floats(
            min_value=MIN_NORM,
            max_value=MAX_NORM,
        ),
        unique=True,
    ),
    cosines=arrays(
        np.float64, 
        (MATRIX_DIMENSION,MATRIX_DIMENSION), 
        elements=st.floats(
            min_value=-1.0, 
            max_value=1.0,
        ),
        unique=True,
    ),
)
def test_matrix_inversion_hypothesis(vector_norms, cosines):
    
    cosines[np.arange(MATRIX_DIMENSION), np.arange(MATRIX_DIMENSION)] = 1
    cosines = np.maximum(cosines, cosines.T)
    
    matrix = np.outer(vector_norms, vector_norms) * cosines
    
    inverse = invertSVD(matrix)

    assert np.allclose(inverse@matrix@inverse, inverse, atol=ABS_TOLERANCE, rtol=REL_TOLERANCE)
    assert np.allclose(matrix@inverse@matrix, matrix, atol=ABS_TOLERANCE, rtol=REL_TOLERANCE)
