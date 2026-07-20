---
name: mol-xyz
description: Transform a molecule name into a 3D coordinate file (PDB or XYZ format) by converting the name to SMILES and then generating the structure. Use when the user requests a coordinate file, 3D structure, or molecular geometry for a named molecule.
---
# Molecule Coordinate File Generation

Transform a molecule name into a coordinate file (PDB or XYZ format) by converting the name to SMILES and then generating the 3D structure.

## Workflow

1. **Convert molecule name to SMILES** using the `molecule_name_to_smiles` tool.
   - Provide the molecule name as input.
   - Capture the resulting SMILES string.

2. **Generate coordinate file** using the `smiles_to_coordinate_file` tool.
   - Pass the SMILES string obtained from step 1.
   - Specify the desired output format (PDB or XYZ).

## Example

**User:** "Generate a coordinate file for aspirin"

**Agent:**
1. Call `molecule_name_to_smiles` with name="aspirin" → SMILES: "CC(=O)OC1=CC=CC=C1C(=O)O"
2. Call `smiles_to_coordinate_file` with smiles="CC(=O)OC1=CC=CC=C1C(=O)O", format="pdb"
3. Return the generated coordinate file to the user.

## Notes

- If `molecule_name_to_smiles` fails to find the molecule, inform the user that the molecule name could not be recognized.
- Always verify the SMILES conversion succeeded before proceeding to coordinate generation.
- Use appropriate file extensions (.pdb or .xyz) for the output format.
