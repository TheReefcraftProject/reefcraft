// -----------------------------------------------------------------------------
// Copyright (c) 2025
//
// Licensed under the MIT License. See the LICENSE file for details.
// -----------------------------------------------------------------------------
#include "reefcraft/reefcraft.hpp"

#include <iostream>
#include <algorithm>
#include <cmath>
#include <limits>

int main() {
    bool success = true;

    // -------------------------------------------------------------------------
    // Test 1: Finite output and amplitude bounds over [0, 10] seconds
    // -------------------------------------------------------------------------

    reefcraft::Sampler theSampler;

    float maxValue = -std::numeric_limits<float>::infinity();
    float minValue =  std::numeric_limits<float>::infinity();

    for (int i = 0; i <= 1000; ++i) {
        float inTime = i * 0.01f;
        float value = theSampler.SimValue(inTime);

        if (!std::isfinite(value)) {
            std::cerr << "✘ Non‑finite value at t=" << inTime << ": " << value << "\n";
            success = false;
            break;
        }

        maxValue = std::max(maxValue, value);
        minValue = std::min(minValue, value);
    }

    constexpr float kTolerance = 0.05f;
    if (maxValue > 1.0f + kTolerance || minValue < -1.0f - kTolerance) {
        std::cerr << "✘ Values out of expected bounds: ["
                  << minValue << ", " << maxValue << "]\n";
        success = false;
    } else {
        std::cout << "✔ sim_value() within ±1.05 and finite over [0,10]s\n";
    }

    // -------------------------------------------------------------------------
    // Test 2: Reseeding produces repeatable values
    // -------------------------------------------------------------------------

    theSampler.Seed(123);
    float valueA = theSampler.SimValue(0.5f);

    theSampler.Seed(123);
    float valueB = theSampler.SimValue(0.5f);

    if (valueA != valueB) {
        std::cerr << "✘ Reseed with same value does not reproduce result\n";
        success = false;
    } else {
        std::cout << "✔ Reseed with same value produces consistent output\n";
    }

    // -------------------------------------------------------------------------
    // Test 3: Changing the seed alters the output
    // -------------------------------------------------------------------------

    theSampler.Seed(123);
    float valueC = theSampler.SimValue(1.0f);

    theSampler.Seed(456);
    float valueD = theSampler.SimValue(1.0f);

    if (valueC == valueD) {
        std::cerr << "✘ Different seeds produced same result at t=1.0\n";
        success = false;
    } else {
        std::cout << "✔ Different seeds produce different results\n";
    }

    // -------------------------------------------------------------------------
    // Test 4: Continuity across time — no large jumps
    // -------------------------------------------------------------------------

    theSampler.Seed(999);
    float valueBefore = theSampler.SimValue(4.999f);
    float valueAfter  = theSampler.SimValue(5.001f);

    if (std::fabs(valueBefore - valueAfter) > 1.0f) {
        std::cerr << "✘ Discontinuity detected across t=5.0\n";
        success = false;
    } else {
        std::cout << "✔ Output is continuous across cycle boundaries\n";
    }

    // -------------------------------------------------------------------------
    // Test 5: Long duration stability
    // -------------------------------------------------------------------------

    theSampler.Seed(2025);
    for (int i = 0; i < 10000; ++i) {
        float inTime = i * 0.01f;
        float value = theSampler.SimValue(inTime);
        if (!std::isfinite(value)) {
            std::cerr << "✘ Non-finite value at t=" << inTime << "\n";
            success = false;
            break;
        }
    }

    if (success) {
        std::cout << "✔ Passed all tests\n";
        return 0;
    } else {
        std::cerr << "✘ One or more tests failed\n";
        return 1;
    }
}
