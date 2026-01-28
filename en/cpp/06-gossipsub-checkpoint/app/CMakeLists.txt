cmake_minimum_required(VERSION 3.16)

if(POLICY CMP0135)
  cmake_policy(SET CMP0135 NEW)
endif()

project(lesson06_gossipsub_checkpoint LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Hunter cmake modules
file(GLOB HUNTER_MODULE_PATHS "$ENV{HOME}/.hunter/_Base/Download/Hunter/*/*/Unpacked/cmake/modules")
if(HUNTER_MODULE_PATHS)
    list(GET HUNTER_MODULE_PATHS 0 HUNTER_MODULE_PATH)
    list(APPEND CMAKE_MODULE_PATH "${HUNTER_MODULE_PATH}")
    if(NOT COMMAND hunter_check_toolchain_definition)
        macro(hunter_check_toolchain_definition)
        endmacro()
    endif()
endif()

find_package(ZLIB CONFIG QUIET)
find_package(libsecp256k1 CONFIG QUIET)
find_package(Boost CONFIG REQUIRED COMPONENTS filesystem program_options)
find_package(soralog CONFIG REQUIRED)
find_package(libp2p CONFIG REQUIRED)

add_executable(lesson main.cpp)

target_link_libraries(lesson PRIVATE
    p2p::p2p
    p2p::p2p_ping
    p2p::p2p_quic
    p2p::p2p_identify
    p2p::p2p_gossip
    Boost::filesystem
    Boost::program_options
    soralog::soralog
)

set_target_properties(lesson PROPERTIES
    OUTPUT_NAME "lesson"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
)
