// -----------------------------------------------------------------------------
// Copyright (c) 2025
//
// Licensed under the MIT License. See the LICENSE file for details.
// -----------------------------------------------------------------------------
#include "reefcraft/reefcraft.hpp"

/*
Currently Defining M_PI in reefcraft.hpp

This library is not accessible for GitHub testing:

#include <corecrt_math_defines.h>  // For M_PI
*/

namespace reefcraft {

Sampler::Sampler(uint32_t inSeed)
    : m_CycleStart(0.0f),
      m_PeriodDist(0.5f, 1.5f),
      m_AmpDist(0.1f, 1.0f),
      m_Rng(inSeed)
{
    // Initialize the first cycle
    m_Period    = m_PeriodDist(m_Rng);
    m_Amplitude = m_AmpDist(m_Rng);
}

void Sampler::Seed(uint32_t inSeed) {
    m_Rng.seed(inSeed);
    m_CycleStart = 0.0f;
    m_Period     = m_PeriodDist(m_Rng);
    m_Amplitude  = m_AmpDist(m_Rng);
}

float Sampler::SimValue(float inTime) {
    // Advance through any completed cycles
    while (inTime >= m_CycleStart + m_Period) {
        m_CycleStart += m_Period;
        m_Period      = m_PeriodDist(m_Rng);
        m_Amplitude   = m_AmpDist(m_Rng);
    }

    // Compute normalized phase angle in [0, 2π)
    float theta = 2.0f * static_cast<float>(M_PI) *
                  (inTime - m_CycleStart) / m_Period;

    return m_Amplitude * std::sin(theta);
}

} // namespace reefcraft
