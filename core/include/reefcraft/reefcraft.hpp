// -----------------------------------------------------------------------------
// Copyright (c) 2025
//
// Licensed under the MIT License. See the LICENSE file for details.
// -----------------------------------------------------------------------------
#pragma once

#include <random>
#include <cmath>

namespace reefcraft {

class Sampler {
public:
    /// Construct with an explicit RNG seed (default 12345 for deterministic runs)
    explicit Sampler(uint32_t inSeed = 12345u);

    /// Reseed the sampler and reset the cycle
    void Seed(uint32_t inSeed);

    /// Sample the value at a given time
    float SimValue(float inTime);

private:
    float m_CycleStart;   ///< Start time of the current cycle
    float m_Period;       ///< Duration of the current cycle in seconds
    float m_Amplitude;    ///< Amplitude of the current cycle

    std::mt19937 m_Rng;   ///< Random-number engine
    std::uniform_real_distribution<float> m_PeriodDist;  ///< Range: [0.5, 1.5] seconds
    std::uniform_real_distribution<float> m_AmpDist;     ///< Range: [0.1, 1.0]
};

} // namespace reefcraft
