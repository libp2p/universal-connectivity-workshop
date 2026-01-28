cmake_minimum_required(VERSION 3.16)

# Set policies for better compatibility
if(POLICY CMP0135)
  cmake_policy(SET CMP0135 NEW)
endif()

project(lesson01_identity LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Export compile commands for IDE support
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Hunter cmake modules are needed for Hunter-installed packages
# Find and include Hunter cmake modules if available
file(GLOB HUNTER_MODULE_PATHS "$ENV{HOME}/.hunter/_Base/Download/Hunter/*/*/Unpacked/cmake/modules")
if(HUNTER_MODULE_PATHS)
    list(GET HUNTER_MODULE_PATHS 0 HUNTER_MODULE_PATH)
    list(APPEND CMAKE_MODULE_PATH "${HUNTER_MODULE_PATH}")
    # Define the required Hunter function as a no-op since we're not using Hunter directly
    if(NOT COMMAND hunter_check_toolchain_definition)
        macro(hunter_check_toolchain_definition)
        endmacro()
    endif()
endif()

# Find dependencies (order matters - find deps before libp2p)
find_package(ZLIB CONFIG QUIET)
find_package(libsecp256k1 CONFIG QUIET)
find_package(Boost CONFIG REQUIRED COMPONENTS filesystem program_options)
find_package(soralog CONFIG REQUIRED)
find_package(libp2p CONFIG REQUIRED)

# Create executable
add_executable(lesson main.cpp)

# Link libraries (cpp-libp2p uses p2p:: namespace)
target_link_libraries(lesson PRIVATE
    p2p::p2p
    Boost::filesystem
    Boost::program_options
    soralog::soralog
)

# Set output properties
set_target_properties(lesson PROPERTIES
    OUTPUT_NAME "lesson"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
)
