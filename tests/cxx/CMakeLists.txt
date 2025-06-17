# Create an executable from the test source
add_executable(test_core
    test_core.cpp
)

# Link it against your core library
target_link_libraries(test_core PRIVATE reefcraft_core)

# Register it with CTest
add_test(NAME core-cxx COMMAND test_core)
