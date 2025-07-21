#include <gtest/gtest.h>
#include "gtplanner/costmap2d.h"

TEST(CostmapFixture, DynamicWeightUpdate) {
  Costmap2D cm;
  cm.updateWeights({2.0, 1.0});
  EXPECT_EQ(cm.current_weights_[0], 2.0);
}

int main(int argc, char **argv) {
  testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
