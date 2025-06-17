# Reefcraft
**Photorealistic Coral Simulations with Physically Based Accuracy**

Reefcraft is an open-source software platform designed to simulate **physically based coral growth** with scientifically accurate **micro and macro morphology**. Built with a focus on realism and flexibility, Reefcraft is a volumetric simulation engine that integrates computational fluid dynamics, chemical reactions, and fine-grain morphological modeling.

This repository contains the source code, documentation, and examples for the Reefcraft software.

---

## Features
- **Physically Based Coral Growth**: Simulates coral growth processes grounded in biological and physical principles.
- **Volumetric Simulation**: Models coral structures in three-dimensional space, capturing intricate morphology and micromorphology.
- **Scientific Accuracy**:
  - Computational Fluid Dynamics (CFD) for realistic water flow simulations.
  - Chemical reaction modeling for nutrient and environmental interactions.
- **Photorealistic Visualizations**: Generate detailed renderings of coral structures for scientific and artistic use.
- **Extensibility**: Designed for easy customization and integration with other projects or tools.

---

## Getting Started
Follow these steps to install and start using Reefcraft:

Requirements:
1) Visual Studio Community Edition (or better) INCLUDING vcpkg  
https://visualstudio.microsoft.com/vs/community/  
Be sure to check the box to install vcpkg for C++ package management  
Ideally set the environment var to reach vcpkg but it will fallback to the default vs community location  
   - ```bash
     setx VCPKG_ROOT "<path_to_your_vcpkg_installation>"  
   - ```bash
     setx VCPKG_ROOT "C:/Program Files/Microsoft Visual Studio/2022/Community/VC/vcpkg"

2) UV  Python Package Manager  
https://docs.astral.sh/uv/getting-started/installation/  
3) Visual Code  

Currently the workflow is through a wheel so this takes much longer
than desired.  Need to implement an in-situ dev cycle for the extension.

Steps:  
1) git clone https://github.com/TheReefcraftProject/reefcraft
2) uv sync from terminal in the cloned directory
3) open the workspace in Visual Code
4) Build desired target  

Build the full wheel in powershell terminal with active venv:
> pip install -e .

The execute python tests with:
> pytest

Run the app from the reefcraft.py  
