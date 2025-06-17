# python-extension-project
Clean c++ and nanobind python project base using VSCode, vcpkg, pyproject.toml, uv, ruff

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
1) git clone [python-extension-project  ](https://github.com/JustinEbert/python-extension-project)
2) uv sync from terminal in the cloned directory
3) open the workspace in Visual Code
4) Build desired target  

Build the full wheel in powershell terminal with active venv:
> pip install -e .

The execute python tests with:
> pytest

Run the app from the reefcraft.py  
