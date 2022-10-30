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

    for p1 in np.arange(nd):
        deriv1_p = fisher_parameters[p1]
        deriv1 = derivative(waveform, parameter_values, deriv1_p, detector)
        # sum Fisher matrices from different components of same detector (e.g., in the case of ET)
        fm[p1, p1] = np.sum(aux.scalar_product(deriv1, deriv1, detector), axis=0)
        for p2 in np.arange(p1+1, nd):
            deriv2_p = fisher_parameters[p2]
            deriv2 = derivative(waveform, parameter_values, deriv2_p, detector)
            fm[p1, p2] = np.sum(aux.scalar_product(deriv1, deriv2, detector), axis=0)
            fm[p2, p1] = fm[p1, p2]

    return fm

def analyzeFisherErrors(
    network: det.Network,
    parameter_values: pd.DataFrame,
    fisher_parameters: list[str],
    population: str,
    networks_ids: list[list[int]],
) -> None:
    """
    Analyze parameter errors.
    """

    # Check if sky-location parameters are part of Fisher analysis. If yes, sky-location error will be calculated.
    signals_havesky = False
    if ("ra" in fisher_parameters) and ("dec" in fisher_parameters):
        signals_havesky = True
        i_ra = fisher_parameters.index("ra")
        i_dec = fisher_parameters.index("dec")
    signals_haveids = False
    if "id" in parameter_values.columns:
        signals_haveids = True
        signal_ids = parameter_values["id"]
        parameter_values.drop("id", inplace=True, axis=1)

    npar = len(fisher_parameters)
    ns = len(network.detectors[0].fisher_matrix[:, 0, 0])  # number of signals
    N = len(networks_ids)

    detect_SNR = network.detection_SNR

    network_names = []
    for n in np.arange(N):
        network_names.append(
            "_".join([network.detectors[k].name for k in networks_ids[n]])
        )

    for n in np.arange(N):
        parameter_errors = np.zeros((ns, npar))
        sky_localization = np.zeros((ns,))
        networkSNR = np.zeros((ns,))
        for d in networks_ids[n]:
            networkSNR += network.detectors[d].SNR ** 2
        networkSNR = np.sqrt(networkSNR)

        for k in np.arange(ns):
            network_fisher_matrix = np.zeros((npar, npar))

            if networkSNR[k] > detect_SNR[1]:
                for d in networks_ids[n]:
                    if network.detectors[d].SNR[k] > detect_SNR[0]:
                        network_fisher_matrix += np.squeeze(
                            network.detectors[d].fisher_matrix[k, :, :]
                        )

                if npar > 0:
                    network_fisher_inverse = invertSVD(network_fisher_matrix)
                    parameter_errors[k, :] = np.sqrt(
                        np.diagonal(network_fisher_inverse)
                    )

                    if signals_havesky:
                        sky_localization[k] = (
                            np.pi
                            * np.abs(np.cos(parameter_values["dec"].iloc[k]))
                            * np.sqrt(
                                network_fisher_inverse[i_ra, i_ra]
                                * network_fisher_inverse[i_dec, i_dec]
                                - network_fisher_inverse[i_ra, i_dec] ** 2
                            )
                        )
        delim = " "
        header = (
            "network_SNR "
            + delim.join(parameter_values.keys())
            + " "
            + delim.join(["err_" + x for x in fisher_parameters])
        )

        ii = np.where(networkSNR > detect_SNR[1])[0]
        save_data = np.c_[
            networkSNR[ii], parameter_values.iloc[ii], parameter_errors[ii, :]
        ]
        if signals_havesky:
            header += " err_sky_location"
            save_data = np.c_[save_data, sky_localization[ii]]
        if signals_haveids:
            header = "signal " + header
            save_data = np.c_[signal_ids.iloc[ii], save_data]

        file_name = (
            "Errors_"
            + network_names[n]
            + "_"
            + population
            + "_SNR"
            + str(detect_SNR[1])
            + ".txt"
        )

        if signals_haveids and (len(save_data) > 0):
            row_format = "%s " + " ".join(
                ["%.3E" for _ in range(len(save_data[0, :]) - 1)]
            )
            np.savetxt(
                file_name,
                save_data,
                delimiter=" ",
                fmt=row_format,
                header=header,
                comments="",
            )
        else:
            np.savetxt(file_name, save_data, delimiter=" ", header=header, comments="")
