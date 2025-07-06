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
1) **Python 3.11+**
2) **[UV](https://docs.astral.sh/uv/getting-started/installation/)** for Python package management
3) **[Dear PyGui](https://github.com/hoffstadt/DearPyGui)** (installed with `uv sync`)
4) **Visual Studio Code** *(optional)*

Steps:

4) `git clone https://github.com/TheReefcraftProject/reefcraft`
5) `cd reefcraft` and run `uv sync`
6) Execute the Python tests:
   ```bash
   pytest
   ```
7) Launch the example app:
   ```bash
   python app/main.py
   ```
