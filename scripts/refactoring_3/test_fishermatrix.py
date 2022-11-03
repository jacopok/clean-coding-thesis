import pytest
from fishermatrix import analyzeFisherErrors
import fishermatrix
import waveforms
import detection
from detection import Network, Detector
import pandas as pd
import numpy as np


def test_fisher_analysis_output(mocker):

    params = {
        "mass_1": 1.4,
        "mass_2": 1.4,
        "redshift": 0.01,
        "luminosity_distance": 40,
        "theta_jn": 5 / 6 * np.pi,
        "ra": 3.45,
        "dec": -0.41,
        "psi": 1.6,
        "phase": 0,
        "geocent_time": 1187008882,
    }

    parameter_values = pd.DataFrame()
    for key, item in params.items():
        parameter_values[key] = np.full((1,), item)

    fisher_parameters = list(params.keys())

    network = Network(
        detector_ids=["ET"],
        parameters=parameter_values,
        fisher_parameters=fisher_parameters,
        config="detectors.yaml",
    )

    wave, t_of_f = waveforms.hphc_amplitudes(
        "gwfish_TaylorF2",
        parameter_values.iloc[0],
        network.detectors[0].frequencyvector,
    )
    signal = detection.projection(
        parameter_values.iloc[0], network.detectors[0], wave, t_of_f
    )

    network.detectors[0].fisher_matrix[0, :, :] = fishermatrix.FisherMatrix(
        "gwfish_TaylorF2",
        parameter_values.iloc[0],
        fisher_parameters,
        network.detectors[0],
    )

    network.detectors[0].SNR[0] = 100

    analyzeFisherErrors(
        network=network,
        parameter_values=parameter_values,
        fisher_parameters=fisher_parameters,
        population="test",
        networks_ids=[[0]],
    )
