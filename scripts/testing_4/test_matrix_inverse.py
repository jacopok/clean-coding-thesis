from gwfish_matrix_inverse import invertSVD
import numpy as np
from hypothesis import given, reject, target
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays
import pytest

N=4

@given(
    vector_norms=arrays(
        np.float64, 
        (N,), 
        elements=st.floats(
            min_value=1e-3,
            max_value=1e3,
        ),
        unique=True,
    ),
    cosines=arrays(
        np.float64, 
        (N,N,), 
        elements=st.floats(
            min_value=-1.0, 
            max_value=1.0,
        ),
        unique=True,
    ),
)
@pytest.mark.parametrize('inverter', [
    np.linalg.pinv, 
    invertSVD
])
def test_matrix_inversion_hypothesis(inverter, vector_norms, cosines):
    
    cosines[np.arange(N), np.arange(N)] = 1
    cosines = np.maximum(cosines, cosines.T)
    
    matrix = np.outer(vector_norms, vector_norms) * cosines
    
    inverse = inverter(matrix)

    assert np.allclose(inverse@matrix@inverse, inverse, atol=1e-3)
    assert np.allclose(matrix@inverse@matrix, matrix, atol=1e-3)
