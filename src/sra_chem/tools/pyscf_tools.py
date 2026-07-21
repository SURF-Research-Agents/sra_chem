"""PySCF tools for quantum chemistry calculations.

This module provides LangChain-compatible tools for running
PySCF-based electronic structure calculations, including
Hartree-Fock ground state energy computations.
"""

import os
from langchain_core.tools import tool
from langchain_surf.tools.hpc_tools import tool as hpc_tools

def _ground_state_energy(
    molecule_coordinate_filename: str,
    basis: str = "sto-3g",
) -> float:
    """Compute the Hartree-Fock ground state energy of a molecule using PySCF.

    Parameters
    ----------
    molecule_coordinate_filename : str
        Path to a file containing the molecular geometry in PySCF
        format (e.g. XYZ, Gaussian, or PySCF-native format).
    basis : str, optional
        Basis set to use for the calculation. Default is "sto-3g".
        Common options include "sto-3g", "3-21g", "6-31g", "6-31g*",
        "cc-pvdz", "cc-pvtz", etc.

    Returns
    -------
    float
        The converged Hartree-Fock ground state energy in eV.

    Raises
    ------
    FileNotFoundError
        If the specified coordinate file does not exist.
    Exception
        If the PySCF calculation fails to converge or encounters
        an error.
    """
    from pyscf import gto
    from pyscf import scf

    mol = gto.M(atom=molecule_coordinate_filename, basis=basis)
    rhf = scf.RHF(mol)
    return rhf.kernel()

@tool
def ground_state_energy_local(
    molecule_coordinate_filename: str,
    basis: str = "sto-3g",
) -> float:
    """Compute the Hartree-Fock ground state energy locally using PySCF.

    This is a wrapper around the internal ``_ground_state_energy`` function
    that exposes the calculation as a LangChain tool for local execution.

    Parameters
    ----------
    molecule_coordinate_filename : str
        Path to a file containing the molecular geometry in PySCF
        format (e.g. XYZ, Gaussian, or PySCF-native format).
    basis : str, optional
        Basis set to use for the calculation. Default is "sto-3g".
        Common options include "sto-3g", "3-21g", "6-31g", "6-31g*",
        "cc-pvdz", "cc-pvtz", etc.

    Returns
    -------
    float
        The converged Hartree-Fock ground state energy in eV.

    Raises
    ------
    FileNotFoundError
        If the specified coordinate file does not exist.
    Exception
        If the PySCF calculation fails to converge or encounters
        an error.
    """
    return _ground_state_energy(molecule_coordinate_filename, basis)


hpc_opt = {
    'slurm_data': {
        "url": "https://slurm.snellius.surf.nl",
        "api_ver": "v0.0.43",
        "user_name": os.getenv('SLURM_USER'),
        "slurm_jwt": os.getenv("SLURM_JWT"),
    },
}

@hpc_tools(hpc=hpc_opt)
def ground_state_energy_hpc(
    molecule_coordinate_filename: str,
    basis: str = "sto-3g",
) -> float:
    """Compute the Hartree-Fock ground state energy on a SLURM cluster.

    This is a wrapper around the internal ``_ground_state_energy`` function
    that submits the calculation to a SLURM HPC cluster (Snellius) via
    the LangChain HPC tool decorator.

    Parameters
    ----------
    molecule_coordinate_filename : str
        Path to a file containing the molecular geometry in PySCF
        format (e.g. XYZ, Gaussian, or PySCF-native format).
    basis : str, optional
        Basis set to use for the calculation. Default is "sto-3g".
        Common options include "sto-3g", "3-21g", "6-31g", "6-31g*",
        "cc-pvdz", "cc-pvtz", etc.

    Returns
    -------
    float
        The converged Hartree-Fock ground state energy in eV.

    Raises
    ------
    FileNotFoundError
        If the specified coordinate file does not exist.
    Exception
        If the PySCF calculation fails to converge or encounters
        an error.
    """
    return _ground_state_energy(molecule_coordinate_filename, basis)