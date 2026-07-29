"""PySCF tools for DFT quantum chemistry calculations.

This module provides LangChain-compatible tools for running
PySCF-based Density Functional Theory (DFT) ground state energy computations.
"""

import os
from pathlib import PosixPath
from langchain_core.tools import tool
from langchain_surf.tools.utils.hpc_func import HPCFunc


def _dft_energy(
    molecule_coordinate_filename: str,
    functional: str = "pbe",
    basis: str = "sto-3g",
) -> float:
    """Compute the DFT ground state energy of a molecule using PySCF.

    Parameters
    ----------
    molecule_coordinate_filename : str
        Path to a file containing the molecular geometry in PySCF
        format (e.g. XYZ, Gaussian, or PySCF-native format).
    functional : str, optional
        Exchange-correlation functional to use. Default is "pbe".
        Common options include "pbe", "b3lyp", "wb97x", "lda",
        "pbesol", "hf", etc.
    basis : str, optional
        Basis set to use for the calculation. Default is "sto-3g".
        Common options include "sto-3g", "3-21g", "6-31g", "6-31g*",
        "cc-pvdz", "cc-pvtz", etc.

    Returns
    -------
    float
        The converged DFT ground state energy in eV.

    Raises
    ------
    FileNotFoundError
        If the specified coordinate file does not exist.
    Exception
        If the PySCF calculation fails to converge or encounters
        an error.
    """
    from pyscf import gto
    from pyscf import dft

    mol = gto.M(atom=molecule_coordinate_filename, basis=basis)
    uhf = dft.UKS(mol, xc=functional)
    return uhf.kernel()


@tool
def dft_energy_local(
    molecule_coordinate_filename: str,
    functional: str = "pbe",
    basis: str = "sto-3g",
) -> float:
    """Compute the DFT ground state energy locally using PySCF.

    This is a wrapper around the internal ``_dft_energy`` function
    that exposes the DFT calculation as a LangChain tool for local execution.

    Parameters
    ----------
    molecule_coordinate_filename : str
        Path to a file containing the molecular geometry in PySCF
        format (e.g. XYZ, Gaussian, or PySCF-native format).
    functional : str, optional
        Exchange-correlation functional to use. Default is "pbe".
        Common options include "pbe", "b3lyp", "wb97x", "lda",
        "pbesol", "hf", etc.
    basis : str, optional
        Basis set to use for the calculation. Default is "sto-3g".
        Common options include "sto-3g", "3-21g", "6-31g", "6-31g*",
        "cc-pvdz", "cc-pvtz", etc.

    Returns
    -------
    float
        The converged DFT ground state energy in eV.

    Raises
    ------
    FileNotFoundError
        If the specified coordinate file does not exist.
    Exception
        If the PySCF calculation fails to converge or encounters
        an error.
    """
    return _dft_energy(molecule_coordinate_filename, functional, basis)


@tool
def dft_energy_hpc(
    molecule_coordinate_filename: str,
    workspace_path: PosixPath,
    functional: str = "pbe",
    basis: str = "sto-3g",
) -> float:
    """Compute the DFT ground state energy on a SLURM cluster.

    This is a wrapper around the internal ``_dft_energy`` function
    that submits the DFT calculation to a SLURM HPC cluster (Snellius)
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
        "pbesol", "hf", etc.
    basis : str, optional
        Basis set to use for the calculation. Default is "sto-3g".
        Common options include "sto-3g", "3-21g", "6-31g", "6-31g*",
        "cc-pvdz", "cc-pvtz", etc.

    Returns
    -------
    float
        The converged DFT ground state energy in eV.

    Raises
    ------
    FileNotFoundError
        If the specified coordinate file does not exist.
    Exception
        If the PySCF calculation fails to converge or encounters
        an error.
    """
    slurm_data = {
        "url": "https://slurm.snellius.surf.nl",
        "api_ver": "v0.0.43",
        "user_name": os.getenv('SLURM_USER'),
        "slurm_jwt": os.getenv('SLURM_JWT'),
    }

    os_data = {
        'bucketname': workspace_path.name
    }

    hpc_func = HPCFunc(_dft_energy,
                  slurm_data=slurm_data,
                  os_data=os_data,
                  root_dir=str(workspace_path)
                  )
    hpc_local_molecule_coordinate_filename = str(PosixPath(molecule_coordinate_filename).relative_to(workspace_path))
    return hpc_func(hpc_local_molecule_coordinate_filename, functional, basis)
