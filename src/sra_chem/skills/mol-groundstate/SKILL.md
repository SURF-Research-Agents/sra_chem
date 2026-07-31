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

4. **Optimize geometry (optional).** Before computing the ground state energy, ask the user if they would like to optimize the geometry of the molecule first.
   - If the user confirms, perform geometry optimization using the appropriate tool based on molecule size:
     - For **small molecules** (up to ~10-20 atoms), use `optimize_geometry_local`.
     - For **large molecules** (more than ~10-20 atoms), use `optimize_geometry_hpc` to submit to a SLURM cluster.
   - Specify the output file path **inside the workspace directory** (e.g., `optimized_molecule.xyz`).
   - Use the optimized coordinate file as input for the ground state energy calculation instead of the initial coordinate file from step 3.
   - If the user declines, skip this step and proceed directly to step 5 using the coordinate file from step 3.

5. **Compute ground state energy** using the appropriate tool based on user request and molecule size.
   - **Choose the method based on user input:**
     - If the user specifies **DFT** (or mentions functional like "b3lyp", "pbe"), use the DFT tools:
       - For **small molecules** (up to ~10-20 atoms), use `dft_energy_local`.
       - For **large molecules** (more than ~10-20 atoms), use `dft_energy_hpc` to submit to a SLURM cluster.
       - Pass the `functional` parameter (e.g., `"b3lyp"`, `"pbe"`) and optionally `basis`.
     - If the user specifies **HF** or does not specify a method, use the HF tools:
       - For **small molecules** (up to ~10-20 atoms), use `hf_energy_local`.
       - For **large molecules** (more than ~10-20 atoms), use `hf_energy_hpc` to submit to a SLURM cluster.
   - Pass the coordinate file path from step 3 (or step 4 if geometry optimization was performed) as `molecule_coordinate_filename`. Use relative path.
   - Optionally specify a `basis` set (default: `"sto-3g"`).
   - The tool returns the convergence value (ground state energy in Hartree).

## Example

**User:** "Compute the ground state energy of water"

**Agent:**
1. Call `create_workspace` with name="water-ground-state" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="water" → SMILES: "O"
3. Call `smiles_to_coordinate_file` with smiles="O", output_file="/path/to/workspace/water.xyz" → path: "/path/to/workspace/water.xyz"
4. Ask the user: "Would you like to optimize the geometry of the molecule before computing the ground state energy?"
   - User: "No" → Skip optimization.
5. Call `hf_energy_local` with molecule_coordinate_filename="/path/to/workspace/water.xyz" → energy: -75.0673... (Hartree)
6. Return the computed ground state energy to the user.

**User:** "Compute the ground state energy of water" (with optimization)

**Agent:**
1. Call `create_workspace` with name="water-ground-state" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="water" → SMILES: "O"
3. Call `smiles_to_coordinate_file` with smiles="O", output_file="/path/to/workspace/water.xyz" → path: "/path/to/workspace/water.xyz"
4. Ask the user: "Would you like to optimize the geometry of the molecule before computing the ground state energy?"
   - User: "Yes" → proceed with optimization.
5. Call `optimize_geometry_local` with molecule_coordinate_filename="/path/to/workspace/water.xyz", output_file="/path/to/workspace/optimized_water.xyz" → optimized: {...}
6. Call `hf_energy_local` with molecule_coordinate_filename="/path/to/workspace/optimized_water.xyz" → energy: -75.0673... (Hartree)
7. Return the computed ground state energy to the user.

**User:** "Compute the DFT energy of water using b3lyp"

**Agent:**
1. Call `create_workspace` with name="water-dft-ground-state" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="water" → SMILES: "O"
3. Call `smiles_to_coordinate_file` with smiles="O", output_file="/path/to/workspace/water.xyz" → path: "/path/to/workspace/water.xyz"
4. Ask the user: "Would you like to optimize the geometry of the molecule before computing the DFT energy?"
   - User: "No" → Skip optimization.
5. Call `dft_energy_local` with molecule_coordinate_filename="/path/to/workspace/water.xyz", functional="b3lyp" → energy: ... (Hartree)
6. Return the computed ground state energy to the user.

**User:** "Compute the ground state energy of a large protein"

**Agent:**
1. Call `create_workspace` with name="protein-ground-state" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="protein" → SMILES: "..."
3. Call `smiles_to_coordinate_file` with smiles="...", output_file="/path/to/workspace/protein.xyz" → path: "/path/to/workspace/protein.xyz"
4. Ask the user: "Would you like to optimize the geometry of the molecule before computing the ground state energy?"
   - User: "No" → Skip optimization.
5. Call `hf_energy_hpc` with molecule_coordinate_filename="/path/to/workspace/protein.xyz" → energy: ... (Hartree)
6. Return the computed ground state energy to the user.

## Notes

- **CRITICAL:** Step 1 (create workspace) is **MANDATORY and NON-NEGOTIABLE**. Never skip it under any circumstances.
- **All files** generated during the workflow (coordinate files, etc.) **MUST be written inside the workspace directory** created in step 1. Never use the current working directory or any other path.
- If `molecule_name_to_smiles` fails to find the molecule, inform the user that the molecule name could not be recognized.
- Always verify each step succeeds before proceeding to the next.
- The ground state energy is returned in Hartree units by PySCF.
- Geometry optimization is **optional but recommended** before ground state energy calculations. Always ask the user if they want to optimize the geometry first.
- Use `optimize_geometry_local` for small molecules and `optimize_geometry_hpc` for large molecules requiring SLURM cluster resources.
- The optimized coordinate file (e.g., `optimized_molecule.xyz`) **MUST be saved inside the workspace directory** created in step 1.
- **HF calculation** uses Restricted Hartree-Fock (RHF) with the default PySCF basis set ("sto-3g").
- **DFT calculation** uses Unrestricted Kohn-Sham (UKS) with the specified exchange-correlation functional.
- Common DFT functionals: `"pbe"`, `"b3lyp"`, `"wb97x"`, `"lda"`, `"pbesol"`.
- Use local tools (`hf_energy_local`, `dft_energy_local`) for small molecules that can be computed on the local machine.
- Use HPC tools (`hf_energy_hpc`, `dft_energy_hpc`) for large molecules that require SLURM cluster resources.
- Both HF and DFT tools accept an optional `basis` parameter (e.g. `"6-31g"`, `"cc-pvdz"`) for higher accuracy.
