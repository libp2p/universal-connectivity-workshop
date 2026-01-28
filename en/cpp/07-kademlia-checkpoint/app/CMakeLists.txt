cmake_minimum_required(VERSION 3.14)
project(lesson07_kademlia_checkpoint)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add stub modules for Hunter (not using Hunter for this build)
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

# Pre-find dependencies with correct target names for Hunter packages
find_package(ZLIB REQUIRED CONFIG)
find_package(libsecp256k1 REQUIRED CONFIG)

find_package(libp2p REQUIRED)
find_package(soralog REQUIRED)
find_package(Boost REQUIRED COMPONENTS filesystem program_options)
find_package(OpenSSL REQUIRED)

add_executable(lesson main.cpp)

target_link_libraries(lesson PRIVATE
    p2p::p2p
    p2p::p2p_ping
    p2p::p2p_quic
    p2p::p2p_identify
    p2p::p2p_gossip
    p2p::p2p_kademlia
    Boost::filesystem
    Boost::program_options
    soralog::soralog
)
