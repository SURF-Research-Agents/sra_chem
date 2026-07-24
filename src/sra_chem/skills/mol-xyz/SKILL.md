---
name: mol-xyz
description: Transform a molecule name into a 3D coordinate file (PDB or XYZ format) by converting the name to SMILES and then generating the structure. Use when the user requests a coordinate file, 3D structure, or molecular geometry for a named molecule.
---
# Molecule Coordinate File Generation

Transform a molecule name into a coordinate file (PDB or XYZ format) by converting the name to SMILES and then generating the 3D structure.

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
   - Specify the desired output format (PDB or XYZ).
   - Specify an output file path **inside the workspace directory created in step 1**.

## Example

**User:** "Generate a coordinate file for aspirin"

**Agent:**
1. Call `create_workspace` with name="aspirin-xyz" → workspace: "/path/to/workspace"
2. Call `molecule_name_to_smiles` with name="aspirin" → SMILES: "CC(=O)OC1=CC=CC=C1C(=O)O"
3. Call `smiles_to_coordinate_file` with smiles="CC(=O)OC1=CC=CC=C1C(=O)O", output_file="/path/to/workspace/aspirin.xyz"
4. Return the generated coordinate file to the user.

## Notes

- **CRITICAL:** Step 1 (create workspace) is **MANDATORY and NON-NEGOTIABLE**. Never skip it under any circumstances.
- **All files** generated during the workflow (coordinate files, etc.) **MUST be written inside the workspace directory** created in step 1. Never use the current working directory or any other path.
- If `molecule_name_to_smiles` fails to find the molecule, inform the user that the molecule name could not be recognized.
- Always verify the SMILES conversion succeeded before proceeding to coordinate generation.
- Use appropriate file extensions (.pdb or .xyz) for the output format.
