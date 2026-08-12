"""Tools for estimating compute resources for quantum chemistry simulations.

This module provides a LangChain tool that estimates compute time, memory,
and HPC job parameters for Hartree-Fock, DFT, and TD-DFT calculations
based on simulation parameters.
"""

from langchain_core.tools import tool

NCPUS_PER_PART = {
    "rome": 128,
    "genoa": 192,
    "fat_rome": 128,
    "fat_genoa": 192,
    "himem_4tb": 128,
    "himem_8tb": 128
}

# Complexity constants: basis set multiplier relative to STO-3G
BASIS_COMPLEXITY = {
    "sto-3g": 1.0,
    "3-21g": 1.5,
    "6-31g": 2.0,
    "6-31g*": 2.5,
    "6-311g": 3.0,
    "6-311g*": 3.5,
    "cc-pvdz": 3.0,
    "cc-pvtz": 5.0,
    "def2-svp": 2.0,
    "def2-tzvp": 3.5,
    "def2-qzvpp": 6.0,
}

# Method base time (seconds) for a reference molecule (~10 atoms, STO-3G)
METHOD_BASE_TIME = {
    "hf": 30,
    "dft": 60,
    "td-dft": 300,
}

# Memory per basis function (MB)
MEMORY_PER_BASIS_FUNC = {
    "hf": 50,
    "dft": 80,
    "td-dft": 200,
}

# TD-DFT time multiplier per excited state
TD_DFT_STATE_MULTIPLIER = 1.5

# Default SLURM partition and account for Snellius
SLURM_DEFAULT_PARTITION = "rome"
SLURM_WALLTIME_DEFAULT = "24:00:00"


@tool
def estimate_simulation_resources(
    method: str,
    molecule_size: int,
    basis: str = "sto-3g",
    n_states: int | None = None,
    use_hpc: bool = False,
    functional: str = "pbe",
) -> dict:
    """Estimate compute resources (time, memory, HPC parameters) for a quantum chemistry simulation.

    Analyzes simulation parameters and provides resource estimates including
    walltime, memory requirements, and SLURM job submission parameters.

    Parameters
    ----------
    method : str
        Quantum chemistry method: "hf", "dft", or "td-dft".
    molecule_size : int
        Number of atoms in the molecule.
    basis : str, optional
        Basis set name. Default is "sto-3g".
        Common values: "sto-3g", "3-21g", "6-31g", "6-31g*",
        "cc-pvdz", "cc-pvtz", "def2-svp", "def2-tzvp".
    n_states : int, optional
        Number of excited states for TD-DFT calculations.
        Required when method="td-dft". Default is 10.
    use_hpc : bool, optional
        Whether to use HPC resources (SLURM cluster). Default is False.
        HPC is recommended for molecules with >15 atoms or large basis sets.
    functional : str, optional
        DFT exchange-correlation functional (for DFT and TD-DFT only).
        Default is "pbe". Common values: "pbe", "b3lyp", "wb97x", "lda".

    Returns
    -------
    dict
        Resource estimation including:
        - method: the calculation method
        - molecule_size: number of atoms
        - basis: basis set used
        - estimated_time_seconds: approximate walltime in seconds
        - estimated_time_formatted: human-readable time (hours:minutes)
        - estimated_memory_mb: approximate peak memory in MB
        - estimated_memory_gb: approximate peak memory in GB
        - number_of_basis_functions: estimated number of basis functions
        - scaling: computational scaling class (e.g. "O(N^3)")
        - slurm_parameters: dict with SLURM job parameters (if use_hpc=True)
        - recommendation: recommendation on local vs HPC execution
        - risk_level: "low", "medium", or "high" for convergence/timeout risk

    Notes
    -----
    Estimates are based on typical PySCF performance on standard hardware.
    Actual performance may vary depending on system architecture, basis set,
    and convergence behavior. TD-DFT times include the underlying DFT reference.
    """
    method = method.lower().strip()
    basis = basis.lower().strip()

    # Validate method
    if method not in ("hf", "dft", "td-dft"):
        return {
            "error": f"Unknown method '{method}'. Use 'hf', 'dft', or 'td-dft'."
        }

    # Handle n_states for TD-DFT
    if method == "td-dft":
        if n_states is None:
            n_states = 10
    else:
        n_states = None

    # Estimate number of basis functions from molecule size and basis complexity
    basis_multiplier = BASIS_COMPLEXITY.get(basis, 4.0)
    atoms_per_basis_func = 2.5  # average atoms per basis function
    num_basis_funcs = max(1, int(molecule_size / atoms_per_basis_func) * basis_multiplier)

    # Get basis complexity multiplier
    complexity = BASIS_COMPLEXITY.get(basis, 4.0)

    # Get method base time
    base_time = METHOD_BASE_TIME[method]

    # Calculate estimated time based on complexity and molecule size
    # O(N^3) to O(N^4) scaling with number of basis functions
    # Use a moderate scaling power and basis set sensitivity
    time_estimate = base_time * complexity ** 1.5 * (molecule_size / 10) ** 1.5

    # Add TD-DFT state cost (reference is 10 states)
    if n_states:
        time_estimate *= 1 + (n_states - 10) * TD_DFT_STATE_MULTIPLIER

    # Memory estimation
    memory_per_basis = MEMORY_PER_BASIS_FUNC.get(method, 100)
    memory_estimate_mb = memory_per_basis * num_basis_funcs * (1 + complexity / 5)

    # Memory scaling: O(N^2) for storage
    memory_estimate_mb = memory_estimate_mb * (molecule_size / 10) ** 1.5

    # Format time
    if time_estimate >= 3600:
        time_formatted = f"{time_estimate / 3600:.1f} hours"
    elif time_estimate >= 60:
        time_formatted = f"{time_estimate / 60:.1f} minutes"
    else:
        time_formatted = f"{time_estimate:.0f} seconds"

    # Memory formatting
    memory_gb = memory_estimate_mb / 1024
    if memory_gb >= 1:
        memory_formatted = f"{memory_gb:.1f} GB"
    else:
        memory_formatted = f"{memory_estimate_mb:.0f} MB"

    # Determine scaling class
    if method == "hf":
        scaling = "O(N^3)"
    elif method == "dft":
        scaling = "O(N^3) to O(N^4)"
    else:
        scaling = "O(N^4) + O(N^3 * n_states)"

    # HPC decision
    use_hpc_recommended = use_hpc or molecule_size > 15 or complexity > 6 or n_states and n_states > 20

    # Build SLURM parameters
    slurm_params = {}
    if use_hpc or use_hpc_recommended:
        if memory_estimate_mb > 8192:
            partition = "fat_rome"
            mem_per_cpu = f"{min(int(memory_gb * 2), 128)}G"
        else:
            partition = SLURM_DEFAULT_PARTITION
            mem_per_cpu = "4G"

        # Walltime estimation with safety margin
        time_seconds = int(time_estimate * 2)  # 2x safety margin
        if time_seconds >= 86400:
            walltime = "72:00:00"
        elif time_seconds >= 36000:
            walltime = f"{time_seconds // 3600 + 1}:00:00"
        elif time_seconds >= 3600:
            hours = time_seconds // 3600
            mins = (time_seconds % 3600) // 60
            walltime = f"{hours}:{mins:02d}:00"
        else:
            walltime = "00:30:00"

        # CPU estimation
        if molecule_size > 50 or complexity > 10:
            ncpus = NCPUS_PER_PART[partition]
        elif molecule_size > 20:
            ncpus = NCPUS_PER_PART[partition]//2
        else:
            ncpus = NCPUS_PER_PART[partition]//4

        slurm_params = {
            "partition": partition,
            "ntasks": 1,
            "cpus-per-task": ncpus,
            "mem-per-cpu": mem_per_cpu,
            "time": walltime,
            "nodes": 1,
        }

    # Risk assessment
    risk_level = "low"
    if complexity > 10 or molecule_size > 100 or (n_states and n_states > 50):
        risk_level = "high"
    elif complexity > 5 or molecule_size > 30 or (n_states and n_states > 20):
        risk_level = "medium"

    # Convergence recommendations
    recommendations = []
    if complexity > 6:
        recommendations.append("Use a larger checkpoint file (chkfile) for better convergence")
    if method == "td-dft" and n_states and n_states > 20:
        recommendations.append("Consider increasing max_cycles in DFT convergence settings")
    if molecule_size > 50:
        recommendations.append("Consider using a smaller basis set for initial geometry optimization")
    if not recommendations:
        recommendations.append("Standard settings should work well for this system")

    return {
        "method": method,
        "molecule_size": molecule_size,
        "basis": basis,
        "functional": functional if method in ("dft", "td-dft") else None,
        "n_states": n_states,
        "estimated_time_seconds": round(time_estimate, 0),
        "estimated_time_formatted": time_formatted,
        "estimated_memory_mb": round(memory_estimate_mb, 0),
        "estimated_memory_gb": round(memory_gb, 2),
        "memory_formatted": memory_formatted,
        "number_of_basis_functions": num_basis_funcs,
        "complexity_multiplier": complexity,
        "scaling": scaling,
        "use_hpc_recommended": use_hpc_recommended,
        "recommendation": (
            "HPC recommended" if use_hpc_recommended else
            "Local execution should be sufficient"
        ),
        "risk_level": risk_level,
        "slurm_parameters": slurm_params if slurm_params else None,
        "recommendations": recommendations,
    }
