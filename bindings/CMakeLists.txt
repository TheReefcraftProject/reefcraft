find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(nanobind CONFIG REQUIRED)

nanobind_add_module(reefcraft
  reefcraft_py.cpp
)

target_link_libraries(reefcraft PRIVATE reefcraft_core)

install(TARGETS reefcraft
  RUNTIME DESTINATION .    # .pyd on Windows → <venv>/Lib/site-packages/
  LIBRARY DESTINATION .    # .so/.dylib on Unix → <venv>/lib/pythonX.Y/site-packages/
)