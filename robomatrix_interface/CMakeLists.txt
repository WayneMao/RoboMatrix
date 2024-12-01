cmake_minimum_required(VERSION 3.8)
project(robomatrix_interface)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# cmake_policy(SET CMP0148 NEW)

# find dependencies
find_package(ament_cmake REQUIRED)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

find_package(rosidl_default_generators REQUIRED)

################################### rm_srv

set(MODULE_NAME robomatrix_srv)

file(GLOB ${MODULE_NAME}_FILES "${CMAKE_CURRENT_SOURCE_DIR}/srv/*.srv")

set(${MODULE_NAME}_FILE_NAMES)

foreach(file ${${MODULE_NAME}_FILES})
    get_filename_component(file_name ${file} NAME)
    list(APPEND ${MODULE_NAME}_FILE_NAMES "srv/${file_name}")
endforeach()

################################ generate the interface
ament_export_dependencies(std_msgs)
ament_export_dependencies(rosidl_default_generators)
rosidl_generate_interfaces(${PROJECT_NAME}
      ${robomatrix_srv_FILE_NAMES}
    #   DEPENDENCIES geometry_msgs 
    #   DEPENDENCIES std_msgs
    )
ament_package()
