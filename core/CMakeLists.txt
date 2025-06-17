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