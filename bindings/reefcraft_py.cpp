// -----------------------------------------------------------------------------
// Copyright (c) 2025
//
// Licensed under the MIT License. See the LICENSE file for details.
// -----------------------------------------------------------------------------
#include "reefcraft/reefcraft.hpp"

#include <nanobind/nanobind.h>

namespace nb = nanobind;

NB_MODULE(reefcraft, inExt) {
    inExt.doc() = "Reefcraft: deterministic sim_value sampler";

    // Local static sampler instance
    static reefcraft::Sampler theSampler{12345u};

    // Expose seed(inSeed) to Python
    inExt.def("seed",
              [](uint32_t inSeed) { theSampler.Seed(inSeed); },
              "Reseed the sim_value sampler RNG",
              nb::arg("seed"));

    // Expose sim_value(inTime) to Python
    inExt.def("sim_value",
              [](float inTime) { return theSampler.SimValue(inTime); },
              "Generate a randomly varying sine at time t",
              nb::arg("t"));
}
