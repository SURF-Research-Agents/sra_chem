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

4. **Estimate compute resources** using the `resource_estimation_agent`.
   - **MANDATORY:** You MUST estimate resources before running any TD-DFT excitation calculation. Never skip this step.
   - Delegate to the `resource_estimation_agent` with the following parameters:
     - `method`: `"td-dft"`
     - `molecule_size`: the number of atoms in the molecule
     - `basis`: the basis set (if specified by the user, otherwise `"631g"`)
     - `n_states`: the number of excited states (if specified by the user, otherwise `10`)
     - `functional`: the DFT functional (if specified by the user, otherwise `"b3lyp"`)
     - `use_hpc`: `True` if the molecule has more than ~15 atoms or a large basis set (cc-pvtz, def2-qzvpp), otherwise `False`
   - The resource estimation agent will return estimated walltime, memory requirements, and SLURM parameters.
   - **If `use_hpc_recommended` is `True`** or the estimated walltime exceeds 1 hour:
     - Use the `td_dft_excitations_hpc` tool for the calculation, passing the `slurm_parameters` field from the resource estimation tool (e.g., `slurm_parameters=resource_result["slurm_parameters"]`).
     - Present the SLURM parameters (partition, walltime, CPUs, memory) from the estimation to inform the user about the HPC job configuration.
   - **If `use_hpc_recommended` is `False`** and estimated walltime is under 1 hour:
     - Use the `td_dft_excitations_local` tool for the calculation.
   - If the user asks about resource requirements without requesting the calculation, respond using only the resource estimation agent output and do not proceed to steps 5.

5. **Compute TD-DFT properties** using the appropriate tool based on the resource estimation from step 4.
   - **Choose the tool based on resource estimation:**
     - If HPC is recommended (from step 4), use `td_dft_excitations_hpc` to submit to a SLURM cluster.
     - If local execution is sufficient (from step 4), use `td_dft_excitations_local`.
   - If the user wants an **absorption spectrum** (continuous spectrum with broadened peaks), first compute excitations using `td_dft_excitations_local` or `td_dft_excitations_hpc`, then pass the result to `td_dft_absorption_spectrum`.
   - **Choose the method based on user input:**
     - If the user specifies **DFT functional** (e.g., "b3lyp", "pbe", "wb97x"), pass the `functional` parameter.
     - If no functional is specified, default to `"b3lyp"`.
   - Optionally specify a `basis` set (default: `"631g"`).
   - Optionally specify `n_states` to control the number of excited states computed (default: 10).
   - For the spectrum tool, optionally specify `sigma` (Gaussian broadening width in eV, default: 0.3).
   - For excitation tools, pass the coordinate file path from step 3 as `molecule_coordinate_filename`. Use relative path.
   - The excitation tools return excitation energies (eV and Hartree), wavelengths (nm), oscillator strengths, and transition details.
   - Pass the excitation data dict (from step 5 excitation tools) to `td_dft_absorption_spectrum` to generate the continuous spectrum.
   - When generating the absorption spectrum, the `output_file` parameter (containing the plot) **MUST be saved inside the workspace directory** created in step 1.

## Example

**User:** "Compute the TD-DFT excitation energies of water"

**Agent:**
1. Call `create_workspace` with name="water-tddft-excitations" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="water" → SMILES: "O"
3. Call `smiles_to_coordinate_file` with smiles="O", output_file="/path/to/workspace/water.xyz" → path: "/path/to/workspace/water.xyz"
4. Delegate to `resource_estimation_agent` with method="td-dft", molecule_size=3, basis="631g", functional="b3lyp", use_hpc=False → resource estimate: {estimated_time: "14 seconds", use_hpc_recommended: false}
5. Since HPC is not recommended, call `td_dft_excitations_local` with molecule_coordinate_filename="/path/to/workspace/water.xyz" → excitations: [...]
6. Return the computed excitation energies and oscillator strengths to the user.

**User:** "Compute the TD-DFT absorption spectrum of water using b3lyp"

**Agent:**
1. Call `create_workspace` with name="water-tddft-spectrum" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="water" → SMILES: "O"
3. Call `smiles_to_coordinate_file` with smiles="O", output_file="/path/to/workspace/water.xyz" → path: "/path/to/workspace/water.xyz"
4. Delegate to `resource_estimation_agent` with method="td-dft", molecule_size=3, basis="631g", functional="b3lyp", use_hpc=False → resource estimate: {estimated_time: "14 seconds", use_hpc_recommended: false}
5. Since HPC is not recommended, call `td_dft_excitations_local` with molecule_coordinate_filename="/path/to/workspace/water.xyz", functional="b3lyp" → excitations: [...]
6. Call `td_dft_absorption_spectrum` with excitations_data=<result from step 5>, output_file="/path/to/workspace/absorption_spectrum.png" → spectrum data: {...}
7. Return the absorption spectrum data (wavelengths, intensities, and excitation details) to the user.

**User:** "Compute excited states of a large molecule with wb97x"

**Agent:**
1. Call `create_workspace` with name="molecule-tddft-excitations" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="molecule" → SMILES: "..."
3. Call `smiles_to_coordinate_file` with smiles="...", output_file="/path/to/workspace/molecule.xyz" → path: "/path/to/workspace/molecule.xyz"
4. Delegate to `resource_estimation_agent` with method="td-dft", molecule_size=50, basis="6-31g", functional="wb97x", use_hpc=True → resource estimate: {estimated_time: "5.2 hours", use_hpc_recommended: true, slurm_parameters: {...}}
5. Since HPC is recommended, call `td_dft_excitations_hpc` with molecule_coordinate_filename="/path/to/workspace/molecule.xyz", functional="wb97x", slurm_parameters={"partition": "general", "time": "24:00:00", "ntasks": 16, ...} → excitations: [...]
6. Return the computed excitation energies and oscillator strengths to the user.

## Notes

- **CRITICAL:** Step 1 (create workspace) is **MANDATORY and NON-NEGOTIABLE**. Never skip it under any circumstances.
- **MANDATORY:** Step 4 (resource estimation via `resource_estimation_agent`) is **MANDATORY and NON-NEGOTIABLE**. Always estimate resources before running TD-DFT calculations.
- **All files** generated during the workflow (coordinate files, etc.) **MUST be written inside the workspace directory** created in step 1. Never use files to the current working directory or any other path.
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
- **SLURM parameters from resource estimation** (partition, walltime, CPUs, memory) must be passed as the `slurm_parameters` argument to `td_dft_excitations_hpc`. These parameters configure the SLURM job submission.
- **Note on HPC tools:** `td_dft_excitations_hpc` uses the `HPCFunc` class internally which submits jobs to the Snellius SLURM cluster. The `slurm_parameters` dict is merged into the SLURM job configuration before submission.
