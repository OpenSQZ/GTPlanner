#pragma once
#include <ros/ros.h>
#include <mutex>
#include <vector>

#ifdef GTPLANNER_HAS_DYNAMIC_RECONFIGURE
#include <dynamic_reconfigure/server.h>
#include <gtplanner/CostWeightsConfig.h>
#endif

class Costmap2D {
public:
  Costmap2D();
  void updateWeights(const std::vector<double>& weights);
private:
#ifdef GTPLANNER_HAS_DYNAMIC_RECONFIGURE
  void reconfigCB(gtplanner::CostWeightsConfig& cfg, uint32_t level);
  dynamic_reconfigure::Server<gtplanner::CostWeightsConfig> reconfig_srv_;
#endif
  std::mutex mtx_;
  std::vector<double> current_weights_;
};
