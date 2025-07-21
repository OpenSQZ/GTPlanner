#include "gtplanner/costmap2d.h"

Costmap2D::Costmap2D() {
#ifdef GTPLANNER_HAS_DYNAMIC_RECONFIGURE
  reconfig_srv_.setCallback(boost::bind(&Costmap2D::reconfigCB, this, _1, _2));
#endif
}

void Costmap2D::updateWeights(const std::vector<double>& w) {
  std::lock_guard<std::mutex> lock(mtx_);
  current_weights_ = w;
}

#ifdef GTPLANNER_HAS_DYNAMIC_RECONFIGURE
void Costmap2D::reconfigCB(gtplanner::CostWeightsConfig& cfg, uint32_t) {
  updateWeights({cfg.obstacle_weight, cfg.inflation_weight});
}
#endif
