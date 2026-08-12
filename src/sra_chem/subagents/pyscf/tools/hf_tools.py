"""PySCF tools for Hartree-Fock quantum chemistry calculations.

This module provides LangChain-compatible tools for running
PySCF-based Hartree-Fock ground state energy computations.
"""

import os
from pathlib import PosixPath
from langchain_core.tools import tool
from langchain_surf.tools.utils.hpc_func import HPCFunc


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
def hf_energy_local(
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


@tool
def hf_energy_hpc(
    molecule_coordinate_filename: str,
    workspace_path: PosixPath,
    basis: str = "sto-3g",
    slurm_parameters: dict | None = None
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
    workspace_path : PosixPath
        Path to the workspace directory used for HPC job execution
        and data storage on the SLURM cluster.
    basis : str, optional
        Basis set to use for the calculation. Default is "sto-3g".
        Common options include "sto-3g", "3-21g", "6-31g", "6-31g*",
        "cc-pvdz", "cc-pvtz", etc.
    slurm_parameters: dict, optional
        dictionary containing the ressources required to perform 
        the calculation. 

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

    hpc_func = HPCFunc(_ground_state_energy,
                  slurm_data=slurm_data,
                  os_data=os_data,
                  root_dir=str(workspace_path)
                  )
    hpc_local_molecule_coordinate_filename = str(PosixPath(molecule_coordinate_filename).relative_to(workspace_path))
    return hpc_func(hpc_local_molecule_coordinate_filename, basis)
