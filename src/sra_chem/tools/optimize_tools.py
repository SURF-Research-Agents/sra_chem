"""PySCF tools for geometry optimization of molecules.

This module provides LangChain-compatible tools for running
PySCF-based geometry optimization computations using DFT.
"""

import os
from pathlib import PosixPath
from typing import Dict, Any
from langchain_core.tools import tool
from langchain_surf.tools.utils.hpc_func import HPCFunc


def _optimize_geometry(
    molecule_coordinate_filename: str,
    basis: str = "631g",
    max_steps: int = 100,
    chkfile: str = 'pyscf_opt.chk',
    output_file: str = 'optimized_molecule.xyz',
) -> Dict[str, Any]:
    """Perform geometry optimization of a molecule using DFT with PySCF.

    Parameters
    ----------
    molecule_coordinate_filename : str
        Path to a file containing the initial molecular geometry in PySCF
        format (e.g. XYZ, Gaussian, or PySCF-native format).
    basis : str, optional
        Basis set to use for the calculation. Default is "631g".
        Common options include "sto-3g", "3-21g", "6-31g", "6-31g*",
        "cc-pvdz", "cc-pvtz", etc.
    max_steps : int, optional
        Maximum number of optimization steps. Default is 300.
    chkfile : str, optional
        Path to the checkpoint file. Default is "pyscf_opt.chk".
    output_file : str, optional
        Path to save the optimized geometry. Default is "optimized_molecule.xyz".

    Returns
    -------
    Dict[str, Any]
        Dictionary containing:
        - initial_energy: initial optimized DFT energy in Hartree and eV
        - final_energy: final optimized DFT energy in Hartree and eV
        - optimized_coordinates: list of [element, x, y, z] for each atom
        - output_file: path to the saved optimized geometry file

    Raises
    ------
    FileNotFoundError
        If the specified coordinate file does not exist.
    Exception
        If the geometry optimization fails to converge or encounters
        an error.
    """
    from pyscf import gto, scf
    from pyscf.geomopt.geometric_solver import optimize

    def _rhf_energy(molecule_coordinate_filename: str, basis: str):
        """Computes the restricted HF energy of a given molecule

        Args:
            molecule_coordinate_filename (str): path to the filename
            basis (str): basis set

        Returns:
            Tuple(Float, Float): Energy in hartrees and eV
        """
        ev_per_ha = 27.211386245988
        mol = gto.M(atom=molecule_coordinate_filename, basis=basis)
        mf = scf.RHF(mol)
        mf.chkfile = chkfile
        initial_energy_ha = mf.kernel()
        initial_energy_ev = initial_energy_ha * ev_per_ha
        return mf, initial_energy_ha, initial_energy_ev

    # compute the initial HF energy    
    mf, initial_energy_ha, initial_energy_ev = _rhf_energy(molecule_coordinate_filename, basis)

    mol_eq = optimize(mf, maxsteps=max_steps)
    
    # Get optimized coordinates
    natoms = mol_eq.natm
    optimized_coords = []
    for i in range(natoms):
        atom_tag = mol_eq.atom_symbol(i)
        coords = mol_eq.atom_coord(i)
        optimized_coords.append([atom_tag, float(coords[0]), float(coords[1]), float(coords[2])])

    # Save optimized geometry to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"{natoms}\n\n")
        for atom_tag, x, y, z in optimized_coords:
            f.write(f"{atom_tag} {x:.8f} {y:.8f} {z:.8f}\n")


    # Re-evaluate energy on optimized geometry
    _, final_energy_ha, final_energy_ev = _rhf_energy(output_file, basis)

    return {
        "initial_energy_ha": round(initial_energy_ha, 8),
        "initial_energy_ev": round(initial_energy_ev, 6),
        "final_energy_ha": round(final_energy_ha, 8),
        "final_energy_ev": round(final_energy_ev, 6),
        "optimized_coordinates": optimized_coords,
        "output_file": os.path.abspath(output_file),
    }


@tool
def optimize_geometry_local(
    molecule_coordinate_filename: str,
    basis: str = "631g",
    max_steps: int = 300,
    chkfile: str = 'pyscf_opt.chk',
    output_file: str = 'optimized_molecule.xyz',
) -> Dict[str, Any]:
    """Perform geometry optimization locally using PySCF.

    This is a wrapper around the internal ``_optimize_geometry`` function
    that exposes the geometry optimization as a LangChain tool for local execution.

    Parameters
    ----------
    molecule_coordinate_filename : str
        Path to a file containing the initial molecular geometry in PySCF
        format (e.g. XYZ, Gaussian, or PySCF-native format).
    basis : str, optional
        Basis set to use for the calculation. Default is "631g".
        Common options include "sto-3g", "3-21g", "6-31g", "6-31g*",
        "cc-pvdz", "cc-pvtz", etc.
    max_steps : int, optional
        Maximum number of optimization steps. Default is 300.
    chkfile : str, optional
        Path to the checkpoint file. Default is "pyscf_opt.chk".
    output_file : str, optional
        Path to save the optimized geometry. Default is "optimized_molecule.xyz".

    Returns
    -------
    Dict[str, Any]
        Dictionary containing initial and final energy (Hartree and eV), 
        optimized coordinates, and path to the saved file.

    Raises
    ------
    FileNotFoundError
        If the specified coordinate file does not exist.
    Exception
        If the geometry optimization fails to converge or encounters
        an error.
    """
    return _optimize_geometry(
        molecule_coordinate_filename, basis, max_steps, chkfile, output_file
    )


@tool
def optimize_geometry_hpc(
    molecule_coordinate_filename: str,
    workspace_path: PosixPath,
    basis: str = "631g",
    max_steps: int = 300,
    chkfile: str = 'pyscf_opt.chk',
    output_file: str = 'optimized_molecule.xyz',
) -> Dict[str, Any]:
    """Perform geometry optimization on a SLURM cluster.

    This is a wrapper around the internal ``_optimize_geometry`` function
    that submits the geometry optimization to a SLURM HPC cluster (Snellius)
    via the LangChain HPC tool decorator.

    Parameters
    ----------
    molecule_coordinate_filename : str
        Path to a file containing the initial molecular geometry in PySCF
        format (e.g. XYZ, Gaussian, or PySCF-native format).
    workspace_path : PosixPath
        Path to the workspace directory used for HPC job execution
        and data storage on the SLURM cluster.
    basis : str, optional
        Basis set to use for the calculation. Default is "631g".
        Common options include "sto-3g", "3-21g", "6-31g", "6-31g*",
        "cc-pvdz", "cc-pvtz", etc.
    max_steps : int, optional
        Maximum number of optimization steps. Default is 300.
    chkfile : str, optional
        Path to the checkpoint file. Default is "pyscf_opt.chk".
    output_file : str, optional
        Path to save the optimized geometry. Default is "optimized_molecule.xyz".

    Returns
    -------
    Dict[str, Any]
        Dictionary containing final energy (Hartree and eV), convergence status,
        number of steps, optimized coordinates, and path to the saved file.

    Raises
    ------
    FileNotFoundError
        If the specified coordinate file does not exist.
    Exception
        If the geometry optimization fails to converge or encounters
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

    hpc_func = HPCFunc(_optimize_geometry,
                  slurm_data=slurm_data,
                  os_data=os_data,
                  root_dir=str(workspace_path)
                  )
    hpc_local_molecule_coordinate_filename = str(PosixPath(molecule_coordinate_filename).relative_to(workspace_path))
    hpc_local_output_file = str(PosixPath(output_file).relative_to(workspace_path))
    return hpc_func(
        hpc_local_molecule_coordinate_filename,
        basis, max_steps, chkfile, hpc_local_output_file
    )
