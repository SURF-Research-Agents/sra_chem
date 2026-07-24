## How to use sra_chem

SURF Chemistry Agents — A multi-agent system for computational chemistry.

The project setup is documented in [project_setup.md](project_setup.md).

### Agent Architecture

This project provides a multi-agent system for computational chemistry workflows:

| Agent | Description | Key Tools |
|-------|-------------|-----------|
| **Chemoinformatics Agent** | Molecular representation & structure generation | SMILES conversion, 3D structure generation, coordinate file creation |
| **Quantum Chemistry Agent** | Electronic structure calculations | Hartree-Fock energies (local & HPC), basis set selection |
| **Multi-Agent Orchestrator** | Coordinates both agents for end-to-end workflows | All tools from both agents |

## Installation

To install sra_chem from GitHub repository, do:

```console
git clone git@github.com:surf-research-agents/sra_chem.git
cd sra_chem
python -m pip install .
```

## Documentation

Include a link to your project's full documentation here.



## Credits

This package was created with [Copier](https://github.com/copier-org/copier) and the [NLeSC/python-template](https://github.com/NLeSC/python-template).
