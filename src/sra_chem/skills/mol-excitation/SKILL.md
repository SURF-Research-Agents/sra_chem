---
name: mol-excitation
description: Compute TD-DFT excitation properties of a molecule using time-dependent density functional theory. Use when the user asks for excitation energies, absorption wavelengths, oscillator strengths, excited states, or TD-DFT calculations for a named molecule.
---
# TD-DFT Excitation Energy Computation

Compute TD-DFT (Time-Dependent Density Functional Theory) excitation energies, oscillator strengths, and absorption spectra of a molecule using PySCF.

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

4. **Compute TD-DFT properties** using the appropriate tool based on user request and molecule size.
   - **Choose the tool based on user request:**
     - If the user wants **excitation energies and oscillator strengths** (individual excited states), use the excitation tools:
       - For **small molecules** (up to ~10-20 atoms), use `td_dft_excitations_local`.
       - For **large molecules** (more than ~10-20 atoms), use `td_dft_excitations_hpc` to submit to a SLURM cluster.
     - If the user wants an **absorption spectrum** (continuous spectrum with broadened peaks), first compute excitations using `td_dft_excitations_local` or `td_dft_excitations_hpc`, then pass the result to `td_dft_absorption_spectrum`.
   - **Choose the method based on user input:**
     - If the user specifies **DFT functional** (e.g., "b3lyp", "pbe", "wb97x"), pass the `functional` parameter.
     - If no functional is specified, default to `"b3lyp"`.
   - Optionally specify a `basis` set (default: `"631g"`).
   - Optionally specify `n_states` to control the number of excited states computed (default: 10).
   - For the spectrum tool, optionally specify `sigma` (Gaussian broadening width in eV, default: 0.3).
   - For excitation tools, pass the coordinate file path from step 3 as `molecule_coordinate_filename`. Use relative path.
   - The excitation tools return excitation energies (eV and Hartree), wavelengths (nm), oscillator strengths, and transition details.
   - Pass the excitation data dict (from step 4 excitation tools) to `td_dft_absorption_spectrum` to generate the continuous spectrum.
   - When generating the absorption spectrum, the `output_file` parameter (containing the plot) **MUST be saved inside the workspace directory** created in step 1.

## Example

**User:** "Compute the TD-DFT excitation energies of water"

**Agent:**
1. Call `create_workspace` with name="water-tddft-excitations" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="water" → SMILES: "O"
3. Call `smiles_to_coordinate_file` with smiles="O", output_file="/path/to/workspace/water.xyz" → path: "/path/to/workspace/water.xyz"
4. Call `td_dft_excitations_local` with molecule_coordinate_filename="/path/to/workspace/water.xyz" → excitations: [...]
5. Return the computed excitation energies and oscillator strengths to the user.

**User:** "Compute the TD-DFT absorption spectrum of water using b3lyp"

**Agent:**
1. Call `create_workspace` with name="water-tddft-spectrum" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="water" → SMILES: "O"
3. Call `smiles_to_coordinate_file` with smiles="O", output_file="/path/to/workspace/water.xyz" → path: "/path/to/workspace/water.xyz"
4. Call `td_dft_excitations_local` with molecule_coordinate_filename="/path/to/workspace/water.xyz", functional="b3lyp" → excitations: [...]
5. Call `td_dft_absorption_spectrum` with excitations_data=<result from step 4>, output_file="/path/to/workspace/absorption_spectrum.png" → spectrum data: {...}
6. Return the absorption spectrum data (wavelengths, intensities, and excitation details) to the user.

**User:** "Compute excited states of a large molecule with wb97x"

**Agent:**
1. Call `create_workspace` with name="molecule-tddft-excitations" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="molecule" → SMILES: "..."
3. Call `smiles_to_coordinate_file` with smiles="...", output_file="/path/to/workspace/molecule.xyz" → path: "/path/to/workspace/molecule.xyz"
4. Call `td_dft_excitations_hpc` with molecule_coordinate_filename="/path/to/workspace/molecule.xyz", functional="wb97x" → excitations: [...]
5. Return the computed excitation energies and oscillator strengths to the user.

## Notes

- **CRITICAL:** Step 1 (create workspace) is **MANDATORY and NON-NEGOTIABLE**. Never skip it under any circumstances.
- **All files** generated during the workflow (coordinate files, etc.) **MUST be written inside the workspace directory** created in step 1. Never use the current working directory or any other path.
- If `molecule_name_to_smiles` fails to find the molecule, inform the user that the molecule name could not be recognized.
- Always verify each step succeeds before proceeding to the next.
- Excitation energies are returned in both eV and Hartree units. Wavelengths are in nm.
- **TD-DFT excitation calculation** uses Unrestricted Kohn-Sham (UKS) reference with TD-DFT on top (UKS/TD-DFT).
- Common DFT functionals: `"pbe"`, `"b3lyp"`, `"wb97x"`, `"lda"`, `"pbesol"`.
- **Excitation tools** (`td_dft_excitations_local`, `td_dft_excitations_hpc`) return discrete excited states with energies, wavelengths, oscillator strengths, and top excitation components (orbital transitions).
- **Absorption spectrum tool** (`td_dft_absorption_spectrum`) takes excitation data as input and returns a continuous spectrum with Gaussian-broadened peaks, plus the discrete excitation data.
- Use local tools (`td_dft_excitations_local`) for small molecules that can be computed on the local machine.
- Use HPC tool (`td_dft_excitations_hpc`) for large molecules that require SLURM cluster resources (Snellius).
- The absorption spectrum tool is local-only (no HPC variant available).
- Both excitation tools accept optional `basis` (e.g. `"6-31g"`, `"cc-pvdz"`) and `n_states` parameters.
- The absorption spectrum tool takes excitation data (from excitation tools) and accepts `sigma` (Gaussian broadening width in eV) and `wavelength_range` (comma-separated min,max in nm).
- The excitation output includes `hf_energy` (ground state energy), `n_states`, and a list of `excitations` each containing `state`, `energy_ev`, `energy_ha`, `wavelength_nm`, `oscillator_strength` and `transition` (e.g. "S1")
