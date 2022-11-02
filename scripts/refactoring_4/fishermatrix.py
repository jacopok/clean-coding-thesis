"""Reformatted, typed code.
"""

import numpy as np
import pandas as pd
import time

import waveforms as wf
import detection as det
import auxiliary as aux

def invertSVD(matrix):
    thresh = 1e-10

    dm = np.sqrt(np.diag(matrix))
    normalizer = np.outer(dm, dm)
    matrix_norm = matrix / normalizer

    [U, S, Vh] = np.linalg.svd(matrix_norm)

    kVal = sum(S > thresh)
    matrix_inverse_norm = U[:, 0:kVal] @ np.diag(1.0 / S[0:kVal]) @ Vh[0:kVal, :]

    return matrix_inverse_norm / normalizer


def derivative(waveform, parameter_values, p, detector):

    """
    Calculates derivatives with respect to geocent_time, merger phase, and distance analytically.
    Derivatives of other parameters are calculated numerically.
    """

    local_params = parameter_values.copy()

    tc = local_params['geocent_time']

    if p == 'luminosity_distance':
        wave, t_of_f = wf.hphc_amplitudes(waveform, local_params, detector.frequencyvector)
        derivative = -1. / local_params[p] * det.projection(local_params, detector, wave, t_of_f)
    elif p == 'geocent_time':
        wave, t_of_f = wf.hphc_amplitudes(waveform, local_params, detector.frequencyvector)
        derivative = 2j * np.pi * detector.frequencyvector * det.projection(local_params, detector, wave, t_of_f)
    elif p == 'phase':
        wave, t_of_f = wf.hphc_amplitudes(waveform, local_params, detector.frequencyvector)
        derivative = -1j * det.projection(local_params, detector, wave, t_of_f)
    else:
        pv = local_params[p]
        eps = 1e-5  # this follows the simple "cube root of numerical precision" recommendation, which is 1e-16 for double
        dp = np.maximum(eps, eps * pv)

        pv_set1 = parameter_values.copy()
        pv_set2 = parameter_values.copy()

        pv_set1[p] = pv - dp / 2.
        pv_set2[p] = pv + dp / 2.

        if p in ['ra', 'dec', 'psi']:  # these parameters do not influence the waveform
            wave, t_of_f = wf.hphc_amplitudes(waveform, local_params, detector.frequencyvector)

            signal1 = det.projection(pv_set1, detector, wave, t_of_f)
            signal2 = det.projection(pv_set2, detector, wave, t_of_f)

            derivative = (signal2 - signal1) / dp
        else:
            pv_set1['geocent_time'] = 0.  # to improve precision of numerical differentiation
            pv_set2['geocent_time'] = 0.
            wave1, t_of_f1 = wf.hphc_amplitudes(waveform, pv_set1, detector.frequencyvector)
            wave2, t_of_f2 = wf.hphc_amplitudes(waveform, pv_set2, detector.frequencyvector)

            pv_set1['geocent_time'] = tc
            pv_set2['geocent_time'] = tc
            signal1 = det.projection(pv_set1, detector, wave1, t_of_f1+tc)
            signal2 = det.projection(pv_set2, detector, wave2, t_of_f2+tc)

            derivative = np.exp(2j * np.pi * detector.frequencyvector * tc) * (signal2 - signal1) / dp

    # print(fisher_parameters[p] + ': ' + str(derivative))
    return derivative


def FisherMatrix(waveform, parameter_values, fisher_parameters, detector):

    nd = len(fisher_parameters)
    fm = np.zeros((nd, nd))

    for p1 in range(nd):
        deriv1_p = fisher_parameters[p1]
        deriv1 = derivative(waveform, parameter_values, deriv1_p, detector)
        # sum Fisher matrices from different components of same detector (e.g., in the case of ET)
        fm[p1, p1] = np.sum(aux.scalar_product(deriv1, deriv1, detector), axis=0)
        for p2 in range(p1+1, nd):
            deriv2_p = fisher_parameters[p2]
            deriv2 = derivative(waveform, parameter_values, deriv2_p, detector)
            fm[p1, p2] = np.sum(aux.scalar_product(deriv1, deriv2, detector), axis=0)
            fm[p2, p1] = fm[p1, p2]

    return fm

def sky_localization_error(
    fisher_matrix: np.ndarray, 
    declination_angle: np.ndarray, 
    right_ascension_index: int,
    declination_index: int,
    ):
    return (
        np.pi
        * np.abs(np.cos(declination_angle))
        * np.sqrt(
            network_fisher_inverse[i_ra, i_ra]
            * network_fisher_inverse[i_dec, i_dec]
            - network_fisher_inverse[i_ra, i_dec] ** 2
        )
    )


def compute_fisher_errors(
    network: det.Network,
    parameter_values: pd.DataFrame,
    fisher_parameters: list[str],
    network_ids: list[int],
) -> None:
    """
    Compute Fisher matrix errors. 
    """

    n_params = len(fisher_parameters)
    n_signals = len(network.detectors[0].fisher_matrix[:, 0, 0])

    signals_havesky = False
    if ("ra" in fisher_parameters) and ("dec" in fisher_parameters):
        signals_havesky = True
        i_ra = fisher_parameters.index("ra")
        i_dec = fisher_parameters.index("dec")

    detector_SNR_thr, network_SNR_thr = network.detection_SNR

    parameter_errors = np.zeros((n_signals, n_params))
    sky_localization = np.zeros((n_signals,))
    networkSNR = np.zeros((n_signals,))
    
    detectors = [network.detectors[d] for d in network_ids]
    
    networkSNR = np.sqrt(sum([detector.SNR**2 for detector in detectors]))
    
    for k in range(n_signals):
        network_fisher_matrix = np.zeros((n_params, n_params))

        for detector in detectors:
            if detector.SNR[k] > network_SNR:
                network_fisher_matrix += np.squeeze(
                    detector.fisher_matrix[k, :, :]
                )

        network_fisher_inverse = invertSVD(network_fisher_matrix)
        parameter_errors[k, :] = np.sqrt(
            np.diagonal(network_fisher_inverse)
        )

        if signals_havesky:
            sky_localization[k] = sky_localization_error(
                network_fisher_matrix, 
                parameter_values["dec"].iloc[k], 
                i_ra, 
                i_dec)

    detected = np.where(networkSNR > network_SNR_thr)[0]
    
    return networkSNR[detected], parameter_errors[detected, :], sky_localization[detected]


def output_to_file(
    parameter_values: pd.DataFrame, 
    networkSNR: np.ndarray, 
    parameter_errors: np.ndarray, 
    sky_localization: np.ndarray,
    fisher_parameters: list[str],
    population: str,
    ):

    delim = " "
    header = (
        "network_SNR "
        + delim.join(parameter_values.keys())
        + " "
        + delim.join(["err_" + x for x in fisher_parameters])
    )
    save_data = np.c_[
        networkSNR, parameter_values, parameter_errors
    ]
    header += " err_sky_location"
    save_data = np.c_[save_data, sky_localization]

    # if signals_haveids and (len(save_data) > 0):
    row_format = "%s " + " ".join(
        ["%.3E" for _ in range(len(save_data[0, :]) - 1)]
    )
    
    file_name = (
        "Errors_"
        + network_names[n]
        + "_"
        + population
        + "_SNR"
        + str(detect_SNR[1])
    )

    np.savetxt(
        file_name + '.txt',
        save_data,
        delimiter=" ",
        header=header,
        comments="",
    )

def errors_file_name(network, detector_ids):
        network_names = []
    for n in range(N):
        network_names.append(
            "_".join([network.detectors[k].name for k in networks_ids[n]])
        )
