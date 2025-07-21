cmake_minimum_required(VERSION 3.5)
project(gtplanner)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  dynamic_reconfigure
)

generate_dynamic_reconfigure_options(cfg/CostWeights.cfg)

include_directories(
  include
  ${catkin_INCLUDE_DIRS}
)

add_executable(gtplanner_node src/costmap2d.cpp)
add_dependencies(gtplanner_node ${PROJECT_NAME}_gencfg)
target_link_libraries(gtplanner_node ${catkin_LIBRARIES})

catkin_add_gtest(test_dynamic_weights test/test_dynamic_weights.cpp)
target_link_libraries(test_dynamic_weights ${catkin_LIBRARIES})
