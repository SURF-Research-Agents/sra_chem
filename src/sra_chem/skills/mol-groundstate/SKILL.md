---
name: mol-groundstate
description: Compute the ground state energy of a molecule from its name using PySCF. Use when the user asks for ground state energy, electronic energy, or quantum chemical energy calculation for a named molecule.
---
# Ground State Energy Computation

Compute the ground state energy of a molecule using PySCF by converting the molecule name to a coordinate file and running either a Hartree-Fock (HF) or Density Functional Theory (DFT) calculation.

## Mandatory Steps

**These steps MUST be performed in order. Do NOT skip or combine them.**

1. **Create a workspace directory** using the `create_workspace` tool.
   - **MANDATORY:** You MUST create a workspace directory before any other step. Never use the current working directory.
   - Provide a descriptive name for the workspace (e.g., based on the molecule name).
   - Use the returned workspace directory path as the base for **all** subsequent file paths.
   - **All files created during this workflow** (coordinate files, temporary files, etc.) **MUST be written inside this workspace directory**. Never write files to the current working directory or any other location.

2. **Convert molecule name to SMILES** using the `molecule_name_to_smiles` tool.
   - Provide the molecule name as input.
   - Capture the resulting SMILES string.

3. **Generate coordinate file** using the `smiles_to_coordinate_file` tool.
   - Pass the SMILES string obtained from step 2.
   - Specify an output file path (e.g., `molecule.xyz`) **inside the workspace directory created in step 1**.
   - Capture the returned file path.

4. **Estimate compute resources** using the `resource_estimation_agent`.
   - **MANDATORY:** You MUST estimate resources before running any ground state energy calculation. Never skip this step.
   - Delegate to the `resource_estimation_agent` with the following parameters:
     - `method`: `"hf"` if no method was specified by the user, `"dft"` if DFT was requested
     - `molecule_size`: the number of atoms in the molecule
     - `basis`: the basis set (if specified by the user, otherwise `"sto-3g"`)
     - `functional`: the DFT functional (if DFT is requested and specified by the user, otherwise `"pbe"`)
     - `use_hpc`: `True` if the molecule has more than ~15 atoms or a large basis set (cc-pvtz, def2-qzvpp), otherwise `False`
   - The resource estimation agent will return estimated walltime, memory requirements, and SLURM parameters.
   - **If `use_hpc_recommended` is `True`** or the estimated walltime exceeds 1 hour:
     - Use the HPC tool (`hf_energy_hpc` or `dft_energy_hpc`) for the calculation, passing the `slurm_parameters` field from the resource estimation tool.
     - Present the SLURM parameters from the estimation to inform the user about the HPC job configuration.
   - **If `use_hpc_recommended` is `False`** and estimated walltime is under 1 hour:
     - Use the local tool (`hf_energy_local` or `dft_energy_local`) for the calculation.
   - If the user asks about resource requirements without requesting the calculation, respond using only the resource estimation agent output and do not proceed to steps 5.

5. **Compute ground state energy** using the appropriate tool based on the resource estimation from step 4.
   - **Choose the tool based on resource estimation:**
     - If HPC is recommended (from step 4), use the HPC tool:
       - For DFT calculations (from user request), use `dft_energy_hpc`.
       - For HF calculations, use `hf_energy_hpc`.
     - If local execution is sufficient (from step 4), use the local tool:
       - For DFT calculations, use `dft_energy_local`.
       - For HF calculations, use `hf_energy_local`.
   - Pass the coordinate file path from step 3 as `molecule_coordinate_filename`. Use relative path.
   - Pass the `functional` parameter (e.g., `"b3lyp"`, `"pbe"`) if DFT is being used.
   - Optionally specify a `basis` set (default: `"sto-3g"`).
   - The tool returns the convergence value (ground state energy in Hartree).

## Example

**User:** "Compute the ground state energy of water"

**Agent:**
1. Call `create_workspace` with name="water-ground-state" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="water" → SMILES: "O"
3. Call `smiles_to_coordinate_file` with smiles="O", output_file="/path/to/workspace/water.xyz" → path: "/path/to/workspace/water.xyz"
4. Delegate to `resource_estimation_agent` with method="hf", molecule_size=3, basis="sto-3g", use_hpc=False → resource estimate: {estimated_time: "30 seconds", use_hpc_recommended: false}
5. Since HPC is not recommended, call `hf_energy_local` with molecule_coordinate_filename="/path/to/workspace/water.xyz" → energy: -75.0673... (Hartree)
6. Return the computed ground state energy to the user.


**User:** "Compute the DFT energy of water using b3lyp"

**Agent:**
1. Call `create_workspace` with name="water-dft-ground-state" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="water" → SMILES: "O"
3. Call `smiles_to_coordinate_file` with smiles="O", output_file="/path/to/workspace/water.xyz" → path: "/path/to/workspace/water.xyz"
4. Delegate to `resource_estimation_agent` with method="dft", molecule_size=3, basis="sto-3g", functional="b3lyp", use_hpc=False → resource estimate: {estimated_time: "60 seconds", use_hpc_recommended: false}
5. Since HPC is not recommended, call `dft_energy_local` with molecule_coordinate_filename="/path/to/workspace/water.xyz", functional="b3lyp" → energy: ... (Hartree)
6. Return the computed ground state energy to the user.

**User:** "Compute the ground state energy of a large protein"

**Agent:**
1. Call `create_workspace` with name="protein-ground-state" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="protein" → SMILES: "..."
3. Call `smiles_to_coordinate_file` with smiles="...", output_file="/path/to/workspace/protein.xyz" → path: "/path/to/workspace/protein.xyz"
4. Delegate to `resource_estimation_agent` with method="hf", molecule_size=500, basis="sto-3g", use_hpc=True → resource estimate: {estimated_time: "2.5 hours", use_hpc_recommended: true, slurm_parameters: {...}}
5. Since HPC is recommended, call `hf_energy_hpc` with molecule_coordinate_filename="/path/to/workspace/protein.xyz", slurm_parameters={"partition": "general", "time": "72:00:00", "ntasks": 16, ...} → energy: ... (Hartree)
6. Return the computed ground state energy to the user.

## Notes

- **CRITICAL:** Step 1 (create workspace) is **MANDATORY and NON-NEGOTIABLE**. Never skip it under any circumstances.
- **MANDATORY:** Step 4 (resource estimation via `resource_estimation_agent`) is **MANDATORY and NON-NEGOTIABLE**. Always estimate resources before running ground state energy calculations.
- **All files** generated during the workflow (coordinate files, etc.) **MUST be written inside the workspace directory** created in step 1. Never use files to the current working directory or any other path.
- **SLURM parameters from resource estimation** (partition, walltime, CPUs, memory) must be passed as the `slurm_parameters` argument to `hf_energy_hpc` or `dft_energy_hpc`. These parameters configure the SLURM job submission.
- **Note on HPC tools:** `hf_energy_hpc` and `dft_energy_hpc` use the `HPCFunc` class internally which submits jobs to the Snellius SLURM cluster. The `slurm_parameters` dict is merged into the SLURM job configuration before submission.
- If `molecule_name_to_smiles` fails to find the molecule, inform the user that the molecule name could not be recognized.
- Always verify each step succeeds before proceeding to the next.
- The ground state energy is returned in Hartree units by PySCF.
- **HF calculation** uses Restricted Hartree-Fock (RHF) with the default PySCF basis set ("sto-3g").
- **DFT calculation** uses Unrestricted Kohn-Sham (UKS) with the specified exchange-correlation functional.
- Common DFT functionals: `"pbe"`, `"b3lyp"`, `"wb97x"`, `"lda"`, `"pbesol"`.
- Use local tools (`hf_energy_local`, `dft_energy_local`) for small molecules that can be computed on the local machine.
- Use HPC tools (`hf_energy_hpc`, `dft_energy_hpc`) for large molecules that require SLURM cluster resources.
- Both HF and DFT tools accept an optional `basis` parameter (e.g. `"6-31g"`, `"cc-pvdz"`) for higher accuracy.
