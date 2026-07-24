---
name: mol-groundstate
description: Compute the ground state energy of a molecule from its name using PySCF. Use when the user asks for ground state energy, electronic energy, or quantum chemical energy calculation for a named molecule.
---
# Ground State Energy Computation

Compute the ground state energy of a molecule using PySCF RHF by converting the molecule name to a coordinate file and running a Hartree-Fock calculation.

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

4. **Compute ground state energy** using the appropriate tool based on molecule size.
   - For **small molecules** (up to ~10-20 atoms), use `ground_state_energy_local`.
   - For **large molecules** (more than ~10-20 atoms), use `ground_state_energy_hpc` to submit to a SLURM cluster.
   - Pass the coordinate file path from step 3 as `molecule_coordinate_filename`. Use relative path
   - Optionally specify a `basis` set (default: `"sto-3g"`).
   - The tool returns the RHF convergence value (ground state energy in Hartree).

## Example

**User:** "Compute the ground state energy of water"

**Agent:**
1. Call `create_workspace` with name="water-ground-state" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="water" → SMILES: "O"
3. Call `smiles_to_coordinate_file` with smiles="O", output_file="/path/to/workspace/water.xyz" → path: "/path/to/workspace/water.xyz"
4. Call `ground_state_energy_local` with molecule_coordinate_filename="/path/to/workspace/water.xyz" → energy: -75.0673... (Hartree)
5. Return the computed ground state energy to the user.

**User:** "Compute the ground state energy of a large protein"

**Agent:**
1. Call `create_workspace` with name="protein-ground-state" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="protein" → SMILES: "..."
3. Call `smiles_to_coordinate_file` with smiles="...", output_file="/path/to/workspace/protein.xyz" → path: "/path/to/workspace/protein.xyz"
4. Call `ground_state_energy_hpc` with molecule_coordinate_filename="/path/to/workspace/protein.xyz" → energy: ... (Hartree)
5. Return the computed ground state energy to the user.

## Notes

- **CRITICAL:** Step 1 (create workspace) is **MANDATORY and NON-NEGOTIABLE**. Never skip it under any circumstances.
- **All files** generated during the workflow (coordinate files, etc.) **MUST be written inside the workspace directory** created in step 1. Never use the current working directory or any other path.
- If `molecule_name_to_smiles` fails to find the molecule, inform the user that the molecule name could not be recognized.
- Always verify each step succeeds before proceeding to the next.
- The ground state energy is returned in Hartree units by PySCF RHF.
- The calculation uses Restricted Hartree-Fock (RHF) with the default PySCF basis set ("sto-3g").
- Use `ground_state_energy_local` for small molecules that can be computed on the local machine.
- Use `ground_state_energy_hpc` for large molecules that require SLURM cluster resources.
- Both tools accept an optional `basis` parameter (e.g. `"6-31g"`, `"cc-pvdz"`) for higher accuracy.
