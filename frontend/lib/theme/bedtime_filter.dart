import 'package:flutter/material.dart';

/// Equivalent of the design's `filter: grayscale(1) brightness(0.78)`
/// applied to the whole app when bedtime mode is on.
const bedtimeColorFilter = ColorFilter.matrix(<double>[
  0.165828, 0.557856, 0.056316, 0, 0,
  0.165828, 0.557856, 0.056316, 0, 0,
  0.165828, 0.557856, 0.056316, 0, 0,
  0, 0, 0, 1, 0,
]);
