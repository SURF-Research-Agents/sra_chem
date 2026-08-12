---
name: mol-geoopt
description: Optimize the geometry of a molecule at the DFT level using PySCF. Use when the user asks for geometry optimization, molecular structure optimization, equilibrium geometry, or optimized molecular coordinates for a named molecule.
---
# Geometry Optimization

Optimize the molecular geometry using PySCF's DFT-based geometry optimization by converting the molecule name to a coordinate file and running either a local or HPC geometry optimization.

## Mandatory Steps

**These steps MUST be performed in order. Do NOT skip or combine them.**

1. **Create a workspace directory** using the `create_workspace` tool.
   - **MANDATORY:** You MUST create a workspace directory before any other step. Never use the current working directory.
   - Provide a descriptive name for the workspace (e.g., based on the molecule name).
   - Use the returned workspace directory path as the base for **all** subsequent file paths.
   - **All files created during this workflow** (coordinate files, temporary files, optimized geometry files, etc.) **MUST be written inside this workspace directory**. Never write files to the current working directory or any other location.

2. **Convert molecule name to SMILES** using the `molecule_name_to_smiles` tool.
   - Provide the molecule name as input.
   - Capture the resulting SMILES string.

3. **Generate coordinate file** using the `smiles_to_coordinate_file` tool.
   - Pass the SMILES string obtained from step 2.
   - Specify an output file path (e.g., `molecule.xyz`) **inside the workspace directory created in step 1**.
   - Capture the returned file path.

4. **Estimate compute resources** using the `resource_estimation_agent`.
   - **MANDATORY:** You MUST estimate resources before running any geometry optimization. Never skip this step.
   - Delegate to the `resource_estimation_agent` with the following parameters:
     - `method`: `"dft"` (geometry optimization uses DFT internally)
     - `molecule_size`: the number of atoms in the molecule
     - `basis`: the basis set (if specified by the user, otherwise `"6-31g"`)
     - `use_hpc`: `True` if the molecule has more than ~15 atoms or a large basis set (cc-pvtz, def2-qzvpp), otherwise `False`
   - The resource estimation agent will return estimated walltime, memory requirements, and SLURM parameters.
   - **If `use_hpc_recommended` is `True`** or the estimated walltime exceeds 1 hour:
     - Use the HPC tool (`optimize_geometry_hpc`) for the optimization, passing the `slurm_parameters` field from the resource estimation tool.
     - Present the SLURM parameters from the estimation to inform the user about the HPC job configuration.
   - **If `use_hpc_recommended` is `False`** and estimated walltime is under 1 hour:
     - Use the local tool (`optimize_geometry_local`) for the optimization.
   - If the user asks about resource requirements without requesting the optimization, respond using only the resource estimation agent output and do not proceed to steps 5.

5. **Perform geometry optimization** using the appropriate tool based on the resource estimation from step 4.
   - **Choose the tool based on resource estimation:**
     - If HPC is recommended (from step 4), use `optimize_geometry_hpc`.
     - If local execution is sufficient (from step 4), use `optimize_geometry_local`.
   - Pass the coordinate file path from step 3 as `molecule_coordinate_filename`. Use absolute path.
   - Optionally specify a `basis` set (default: `"6-31g"`).
   - Optionally specify `max_steps` to control the maximum number of optimization steps (default: 300).
   - Optionally specify `chkfile` for the checkpoint file path (default: `"pyscf_opt.chk"`).
   - Specify an `output_file` path **inside the workspace directory** (e.g., `"optimized_molecule.xyz"`) where the optimized geometry will be saved.

## Example

**User:** "Optimize the geometry of water"

**Agent:**
1. Call `create_workspace` with name="water-geometry-optimization" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="water" → SMILES: "O"
3. Call `smiles_to_coordinate_file` with smiles="O", output_file="/path/to/workspace/water.xyz" → path: "/path/to/workspace/water.xyz"
4. Delegate to `resource_estimation_agent` with method="dft", molecule_size=3, basis="6-31g", use_hpc=False → resource estimate: {estimated_time: "60 seconds", use_hpc_recommended: false}
5. Since HPC is not recommended, call `optimize_geometry_local` with molecule_coordinate_filename="/path/to/workspace/water.xyz", output_file="/path/to/workspace/optimized_water.xyz" → {final_energy_ha: -76.xxx, final_energy_ev: -2075.xxx, optimized_coordinates: [...], output_file: "/path/to/workspace/optimized_water.xyz"}
6. Return the optimized geometry and energies to the user.


**User:** "Optimize the geometry of benzene using cc-pvdz"

**Agent:**
1. Call `create_workspace` with name="benzene-geometry-optimization" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="benzene" → SMILES: "c1ccccc1"
3. Call `smiles_to_coordinate_file` with smiles="c1ccccc1", output_file="/path/to/workspace/benzene.xyz" → path: "/path/to/workspace/benzene.xyz"
4. Delegate to `resource_estimation_agent` with method="dft", molecule_size=12, basis="cc-pvdz", use_hpc=False → resource estimate: {estimated_time: "5 minutes", use_hpc_recommended: false}
5. Since HPC is not recommended, call `optimize_geometry_local` with molecule_coordinate_filename="/path/to/workspace/benzene.xyz", basis="cc-pvdz", output_file="/path/to/workspace/optimized_benzene.xyz" → {final_energy_ha: -230.xxx, final_energy_ev: -6265.xxx, optimized_coordinates: [...], output_file: "/path/to/workspace/optimized_benzene.xyz"}
6. Return the optimized geometry and energies to the user.

**User:** "Optimize the geometry of a large protein"

**Agent:**
1. Call `create_workspace` with name="protein-geometry-optimization" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="protein" → SMILES: "..."
3. Call `smiles_to_coordinate_file` with smiles="...", output_file="/path/to/workspace/protein.xyz" → path: "/path/to/workspace/protein.xyz"
4. Delegate to `resource_estimation_agent` with method="dft", molecule_size=500, basis="6-31g", use_hpc=True → resource estimate: {estimated_time: "3 hours", use_hpc_recommended: true, slurm_parameters: {...}}
5. Since HPC is recommended, call `optimize_geometry_hpc` with molecule_coordinate_filename="/path/to/workspace/protein.xyz", slurm_parameters={"partition": "general", "time": "72:00:00", "ntasks": 16, ...}, output_file="/path/to/workspace/optimized_protein.xyz" → {final_energy_ha: -xxxxx.xxx, final_energy_ev: -xxxxxx.xxx, optimized_coordinates: [...], output_file: "/path/to/workspace/optimized_protein.xyz"}
6. Return the optimized geometry and energies to the user.

## Notes

- **CRITICAL:** Step 1 (create workspace) is **MANDATORY and NON-NEGOTIABLE**. Never skip it under any circumstances.
- **MANDATORY:** Step 4 (resource estimation via `resource_estimation_agent`) is **MANDATORY and NON-NEGOTIABLE**. Always estimate resources before running geometry optimizations.
- **All files** generated during the workflow (coordinate files, optimized geometry files, etc.) **MUST be written inside the workspace directory** created in step 1. Never write files to the current working directory or any other path.
- **SLURM parameters from resource estimation** (partition, walltime, CPUs, memory) should be passed to `optimize_geometry_hpc` via the `slurm_parameters` argument if available.
- **Note on HPC tools:** `optimize_geometry_hpc` uses the `HPCFunc` class internally which submits jobs to the Snellius SLURM cluster.
- If `molecule_name_to_smiles` fails to find the molecule, inform the user that the molecule name could not be recognized.
- Always verify each step succeeds before proceeding to the next.
- **Geometry optimization uses DFT internally** with the restricted Hartree-Fock (RHF) reference for the optimization step, then re-evaluates the RHF energy on the optimized geometry.
- The optimization result includes:
  - `initial_energy_ha` / `initial_energy_ev`: Energy of the starting geometry
  - `final_energy_ha` / `final_energy_ev`: Energy of the optimized geometry
  - `optimized_coordinates`: List of `[element, x, y, z]` for each atom in the optimized structure
  - `output_file`: Path to the saved optimized geometry file (XYZ format)
- Energies are returned in both Hartree and eV units.
- **Basis set options:** `"6-31g"` (default), `"sto-3g"` (minimal), `"6-31g*"`, `"cc-pvdz"`, `"cc-pvtz"`, `"def2-svp"`, `"def2-tzvp"`.
- **Max steps:** Control the maximum number of optimization steps with `max_steps` (default: 300). Increase for difficult optimizations, decrease to save time for simple molecules.
- Use local tools (`optimize_geometry_local`) for small molecules that can be optimized on the local machine.
- Use HPC tools (`optimize_geometry_hpc`) for large molecules that require SLURM cluster resources.
- Geometry optimization finds the local minimum on the potential energy surface. The result depends on the starting geometry — if the initial structure is far from the minimum, optimization may fail or converge to an unexpected minimum.