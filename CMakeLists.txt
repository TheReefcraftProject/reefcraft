cmake_minimum_required(VERSION 3.18)

# On Windows, if the environment variable VCPKG_ROOT is not set, fall back to the default VS‑Community install path:
if(WIN32 AND NOT DEFINED ENV{VCPKG_ROOT})
    set(ENV{VCPKG_ROOT}
        "C:/Program Files/Microsoft Visual Studio/2022/Community/VC/vcpkg")
    message(STATUS "VCPKG_ROOT not defined; falling back to $ENV{VCPKG_ROOT}")
endif()

project(reefcraft LANGUAGES CXX)

# Enable testing
include(CTest)
enable_testing()

# Build core lib and Python extension
add_subdirectory(core)
add_subdirectory(bindings)
add_subdirectory(tests/cxx)