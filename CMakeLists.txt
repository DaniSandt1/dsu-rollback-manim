cmake_minimum_required(VERSION 3.16)
project(dsu_rollback LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(MSVC)
    add_compile_options(/W4 /utf-8 /EHsc)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# La estructura es header-only.
add_library(dsu INTERFACE)
target_include_directories(dsu INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/cpp/include)

# Genera las trazas JSON que consume la animación.
add_executable(escenarios cpp/src/escenarios.cpp)
target_link_libraries(escenarios PRIVATE dsu)

add_executable(dsu_tests cpp/tests/tests.cpp)
target_link_libraries(dsu_tests PRIVATE dsu)

enable_testing()
add_test(NAME dsu_tests COMMAND dsu_tests)
