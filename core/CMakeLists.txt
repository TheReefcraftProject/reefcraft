add_library(reefcraft_core
  src/reefcraft.cpp
)

target_include_directories(reefcraft_core PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

set_target_properties(reefcraft_core PROPERTIES
  PUBLIC_HEADER include/reefcraft/reefcraft.hpp
)

# Platform-specific handling
if(WIN32)
  # Windows-specific settings
  message(STATUS "Building for Windows")
  
  # Include Windows-specific headers (if needed)
  target_include_directories(reefcraft_core PRIVATE 
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include/windows>
  )

  # Windows-specific math defines (corecrt_math_defines.h for M_PI)
  add_definitions(-D_USE_MATH_DEFINES)

elseif(UNIX)
  # Linux/macOS-specific settings
  message(STATUS "Building for Linux/macOS")
  
  # Include standard math headers (for Linux/macOS)
  target_include_directories(reefcraft_core PRIVATE 
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include/linux>
  )

  # Define M_PI if not already defined (since it's not guaranteed in all compilers)
  add_definitions(-DM_PI=3.14159265358979323846)
endif()