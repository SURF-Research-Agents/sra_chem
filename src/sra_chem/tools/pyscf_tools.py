"""PySCF tools for quantum chemistry calculations.

This module is kept for backward compatibility. New code should import
directly from sra_chem.tools.hf_tools or sra_chem.tools.dft_tools.
"""

# Backward compatibility re-exports
from sra_chem.tools.hf_tools import (  # noqa: F401
    hf_energy_local,
    hf_energy_hpc,
)

from sra_chem.tools.dft_tools import (  # noqa: F401
    dft_energy_local,
    dft_energy_hpc,
)

from sra_chem.tools.tddft_tools import (
    td_dft_excitations_local,
    td_dft_excitations_hpc,
    td_dft_absorption_spectrum

)

from sra_chem.tools.optimize_tools import (
    optimize_geometry_local,
    optimize_geometry_hpc,
)
