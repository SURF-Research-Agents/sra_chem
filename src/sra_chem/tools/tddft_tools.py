"""PySCF tools for Time-Dependent DFT (TD-DFT) calculations.

This module provides LangChain-compatible tools for running
PySCF-based TD-DFT excitation energy and oscillator strength computations.
"""

import os
import json
import subprocess
from pathlib import PosixPath
from typing import Dict, List, Any
from langchain_core.tools import tool
from langchain_surf.tools.utils.hpc_func import HPCFunc


def _td_dft_excitations(
    molecule_coordinate_filename: str,
    functional: str = "b3lyp",
    basis: str = "631g",
    n_states: int = 10,
    chkfile: str = 'pyscf.chk'
) -> Dict[str, Any]:
    """Compute TD-DFT excitation energies and oscillator strengths.

    Parameters
    ----------
    molecule_coordinate_filename : str
        Path to a file containing the molecular geometry in PySCF
        format (e.g. XYZ, Gaussian, or PySCF-native format).
    functional : str, optional
        Exchange-correlation functional to use. Default is "pbe".
        Common options include "pbe", "b3lyp", "wb97x", "lda",
        "pbesol", etc.
    basis : str, optional
        Basis set to use for the calculation. Default is "sto-3g".
        Common options include "sto-3g", "3-21g", "6-31g", "6-31g*",
        "cc-pvdz", "cc-pvtz", etc.
    n_states : int, optional
        Number of low-lying excited states to compute. Default is 10.
    chkfile: str, optional
        Path ot the checkpoint file of the calculation

    Returns
    -------
    Dict[str, Any]
        Dictionary containing:
        - hf_energy: Hartree-Fock/DFT ground state energy in Hartree
        - n_states: number of excited states computed
        - excitations: list of dicts with keys:
            - state: state index (1-based)
            - energy_ev: excitation energy in eV
            - energy_ha: excitation energy in Hartree
            - wavelength_nm: absorption wavelength in nm
            - oscillator_strength: oscillator strength f
            - transition: transition type (e.g. "S1", "T1")
            - components: top excitation components (coefficients and orbital pairs)

    Raises
    ------
    FileNotFoundError
        If the specified coordinate file does not exist.
    Exception
        If the TD-DFT calculation fails to converge or encounters
        an error.
    """
    from pyscf import gto
    from pyscf import dft, tddft

    mol = gto.M(atom=molecule_coordinate_filename, basis=basis)
    mf = dft.RKS(mol, xc=functional)
    mf.chkfile = chkfile
    ehf = mf.kernel()

    # TD-DFT on top of UHF/UKS
    tds = tddft.TDDFT(mf)
    ncs = tds.nstates if tds.nstates else n_states
    ncs = min(ncs, n_states)
    tds.nstates = ncs
    e_a, _ = tds.kernel()
    tds.analyze()
    osc_str = tds.oscillator_strength()

    # Convert to eV (1 Hartree = 27.211386245988 eV)
    ev_per_ha = 27.211386245988
    nm_per_ha_inv = 1239.84193  # hc in eV*nm

    excitations = []
    for ie, energy in enumerate(e_a):
        energy_ha = float(energy)
        energy_ev = energy_ha * ev_per_ha
        wavelength_nm = nm_per_ha_inv / energy_ev if energy_ev > 0 else 0.0

        osc_f = osc_str[ie]

        excitations.append({
            "state": ie + 1,
            "energy_ev": round(energy_ev, 6),
            "energy_ha": round(energy_ha, 8),
            "wavelength_nm": round(wavelength_nm, 2),
            "oscillator_strength": round(osc_f, 6),
            "transition": f"S{ie + 1}",
        })

    return {
        "hf_energy": round(ehf, 8),
        "n_states": len(e_a),
        "excitations": excitations,
    }


@tool
def td_dft_excitations_local(
    molecule_coordinate_filename: str,
    functional: str = "b3lyp",
    basis: str = "631g",
    n_states: int = 10,
    chkfile: str = 'pyscf.chk'
) -> Dict[str, Any]:
    """Compute TD-DFT excitation energies and oscillator strengths locally using PySCF.

    This is a wrapper around the internal ``_td_dft_excitations`` function
    that exposes the TD-DFT calculation as a LangChain tool for local execution.

    Parameters
    ----------
    molecule_coordinate_filename : str
        Path to a file containing the molecular geometry in PySCF
        format (e.g. XYZ, Gaussian, or PySCF-native format).
    functional : str, optional
        Exchange-correlation functional to use. Default is "pbe".
        Common options include "pbe", "b3lyp", "wb97x", "lda",
        "pbesol", etc.
    basis : str, optional
        Basis set to use for the calculation. Default is "sto-3g".
        Common options include "sto-3g", "3-21g", "6-31g", "6-31g*",
        "cc-pvdz", "cc-pvtz", etc.
    n_states : int, optional
        Number of low-lying excited states to compute. Default is 10.
    chkfile: str, optional
        Path ot the checkpoint file of the calculation

    Returns
    -------
    Dict[str, Any]
        Dictionary containing ground state energy and a list of excited states
        with excitation energies (eV and Hartree), wavelengths (nm), oscillator
        strengths, and top excitation components.

    Raises
    ------
    FileNotFoundError
        If the specified coordinate file does not exist.
    Exception
        If the TD-DFT calculation fails to converge or encounters
        an error.
    """
    return _td_dft_excitations(molecule_coordinate_filename, functional, basis, n_states, chkfile)


@tool
def td_dft_excitations_hpc(
    molecule_coordinate_filename: str,
    workspace_path: PosixPath,
    functional: str = "b3lyp",
    basis: str = "631g",
    n_states: int = 10,
    chkfile: str = 'pyscf.chk',
    slurm_parameters: dict | None = None
) -> Dict[str, Any]:
    """Compute TD-DFT excitation energies and oscillator strengths on a SLURM cluster.

    This is a wrapper around the internal ``_td_dft_excitations`` function
    that submits the TD-DFT calculation to a SLURM HPC cluster (Snellius)
    via the LangChain HPC tool decorator.

    Parameters
    ----------
    molecule_coordinate_filename : str
        Path to a file containing the molecular geometry in PySCF
        format (e.g. XYZ, Gaussian, or PySCF-native format).
    workspace_path : PosixPath
        Path to the workspace directory used for HPC job execution
        and data storage on the SLURM cluster.
    functional : str, optional
        Exchange-correlation functional to use. Default is "pbe".
        Common options include "pbe", "b3lyp", "wb97x", "lda",
        "pbesol", etc.
    basis : str, optional
        Basis set to use for the calculation. Default is "sto-3g".
        Common options include "sto-3g", "3-21g", "6-31g", "6-31g*",
        "cc-pvdz", "cc-pvtz", etc.
    n_states : int, optional
        Number of low-lying excited states to compute. Default is 10.
    chkfile: str, optional
        Path ot the checkpoint file of the calculation
    slurm_parameters: dict, optional
            dictionary containing the ressources required to perform 
            the calculation. 

    Returns
    -------
    Dict[str, Any]
        Dictionary containing ground state energy and a list of excited states
        with excitation energies (eV and Hartree), wavelengths (nm), oscillator
        strengths, and top excitation components.

    Raises
    ------
    FileNotFoundError
        If the specified coordinate file does not exist.
    Exception
        If the TD-DFT calculation fails to converge or encounters
        an error.
    """
    slurm_data = {
        "url": "https://slurm.snellius.surf.nl",
        "api_ver": "v0.0.43",
        "user_name": os.getenv('SLURM_USER'),
        "slurm_jwt": os.getenv('SLURM_JWT'),
    }

    if slurm_parameters is not None:
        slurm_data.update(slurm_parameters)

    os_data = {
        'bucketname': workspace_path.name
    }

    hpc_func = HPCFunc(_td_dft_excitations,
                  slurm_data=slurm_data,
                  os_data=os_data,
                  root_dir=str(workspace_path)
                  )
    hpc_local_molecule_coordinate_filename = str(PosixPath(molecule_coordinate_filename).relative_to(workspace_path))
    return hpc_func(hpc_local_molecule_coordinate_filename, functional, basis, n_states, chkfile)


def _td_dft_absorption_spectrum(
    excitations_data: Dict[str, Any],
    output_file: str,
    sigma: float = 0.3,
    wavelength_range: tuple = None,
    
) -> Dict[str, Any]:
    """Compute TD-DFT absorption spectrum from precomputed excitation data.

    Parameters
    ----------
    excitations_data : Dict[str, Any]
        Dictionary output from ``_td_dft_excitations`` containing:
        - hf_energy: ground state energy in Hartree
        - n_states: number of excited states
        - excitations: list of dicts with energy_ev, wavelength_nm,
          oscillator_strength, transition, etc.
    output_file : str
            Path to save the absorption spectrum plot as an image (PNG).
    sigma : float, optional
        Gaussian broadening width in eV. Default is 0.3.
    wavelength_range : tuple of float, optional
        Wavelength range (min, max) in nm for the spectrum.
        If None, automatically determined from the excitation data
        with a 20 nm margin on each side.
    Returns
    -------
    Dict[str, Any]
        Dictionary containing:
        - wavelengths: list of wavelength values in nm
        - intensities: list of absorbance intensities
        - excitations: list of computed excited states with details
        - parameters: dict of spectrum parameters used
        - plot_saved: path to the saved plot image, or None
    """
    import numpy as np
    import matplotlib
    import matplotlib.pyplot as plt

    # Extract excitation data
    excitations = excitations_data.get("excitations", [])

    # Auto-determine wavelength range from data if not provided
    if wavelength_range is None:
        valid_wls = [
            exc.get("wavelength_nm", 0.0)
            for exc in excitations
            if exc.get("wavelength_nm", 0.0) > 0
        ]
        if valid_wls:
            wl_min = max(0.0, min(valid_wls) - 20.0)
            wl_max = max(valid_wls) + 20.0
        else:
            wl_min, wl_max = 100.0, 800.0
    else:
        wl_min, wl_max = wavelength_range

    # Build wavelength grid
    wavelengths = np.linspace(wl_min, wl_max, 1000)
    intensities = np.zeros_like(wavelengths)

    # Convolve each excitation with a Gaussian
    for exc in excitations:
        energy_ev = exc.get("energy_ev", 0.0)
        osc_f = exc.get("oscillator_strength", 0.0)
        center_nm = exc.get("wavelength_nm", 0.0)

        if energy_ev <= 0 or osc_f <= 0:
            continue
        if center_nm < wl_min or center_nm > wl_max:
            continue

        # Gaussian broadening in wavelength space
        sigma_nm = sigma * 1239.84193 / (energy_ev ** 2) if energy_ev > 0 else sigma
        sigma_nm = max(sigma_nm, 0.1)  # minimum width
        intensities += osc_f * np.exp(-0.5 * ((wavelengths - center_nm) / sigma_nm) ** 2)

    # Normalize intensities
    max_int = np.max(intensities) if np.max(intensities) > 0 else 1.0
    intensities = intensities / max_int

    # Build excitation list for output
    output_excitations = []
    for exc in excitations:
        output_excitations.append({
            "state": exc.get("state"),
            "energy_ev": exc.get("energy_ev"),
            "wavelength_nm": exc.get("wavelength_nm"),
            "oscillator_strength": exc.get("oscillator_strength"),
            "transition": exc.get("transition"),
        })

    # Plot intensity vs wavelength
    matplotlib.use('agg')
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(wavelengths, intensities, 'b-', linewidth=1.5, label='Absorption spectrum')

    # Mark individual transitions
    for exc in output_excitations:
        if exc['wavelength_nm'] >= wl_min and exc['wavelength_nm'] <= wl_max:
            ax.axvline(x=exc['wavelength_nm'], color='r', linestyle='--', alpha=0.4)

    ax.set_xlabel('Wavelength (nm)', fontsize=12)
    ax.set_ylabel('Normalized Intensity', fontsize=12)
    ax.set_title('TD-DFT Absorption Spectrum', fontsize=14)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(wl_min, wl_max)

    fig.tight_layout()
    fig.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close(fig)

    # show the figure
    subprocess.run(["open", output_file], check=False)

    return {
        "wavelengths": wavelengths.tolist(),
        "intensities": intensities.tolist(),
        "excitations": output_excitations,
        "parameters": {
            "sigma_eV": sigma,
            "wavelength_range_nm": [wl_min, wl_max],
        },
    }


@tool
def td_dft_absorption_spectrum(
    excitations_data: Dict[str, Any],
    output_file: str,
    sigma: float = 0.3,
    wavelength_range: str = None,
    
) -> Dict[str, Any]:
    """Compute TD-DFT absorption spectrum with Gaussian-broadened peaks.

    This tool takes precomputed excitation energies and oscillator strengths
    (e.g. from ``_td_dft_excitations`` or ``td_dft_excitations_local``)
    and generates a continuous absorption spectrum by convoluting the
    discrete transitions with Gaussian functions.

    Parameters
    ----------
    excitations_data : Dict[str, Any]
        Dictionary output from ``_td_dft_excitations`` containing:
        - hf_energy: ground state energy in Hartree
        - n_states: number of excited states
        - excitations: list of dicts with energy_ev, wavelength_nm,
          oscillator_strength, transition, etc.
    output_file : str
        Path to save the absorption spectrum plot as a PNG image.
    sigma : float, optional
        Gaussian broadening width in eV. Default is 0.3.
    wavelength_range : str, optional
        Comma-separated min,max wavelength range in nm (e.g. "200,700").
        If None, automatically determined from the excitation data.
        

    Returns
    -------
    Dict[str, Any]
        Dictionary with wavelength/intensity arrays for the spectrum,
        individual excitation data, calculation parameters, and the
        path to the saved plot image (if output_file was provided).
    """
    if wavelength_range is not None:
        wl_parts = wavelength_range.split(",")
        wl_min, wl_max = float(wl_parts[0]), float(wl_parts[1])
        return _td_dft_absorption_spectrum(
            excitations_data, output_file, sigma, (wl_min, wl_max)
        )
    return _td_dft_absorption_spectrum(
        excitations_data, output_file, sigma, None
    )
