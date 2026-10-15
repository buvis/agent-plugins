# Bugfix Requirements Document

## Introduction

The nightly import drops the last row of a file that has no final newline.

Sources: docs/dev/project-management/intake/processed/00102-last-row

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a source file ends without a newline THEN the system skips its last row

### Expected Behavior (Correct)

2.1 WHEN a source file ends without a newline THEN the system SHALL import its last row

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a source file ends with a newline THEN the system SHALL CONTINUE TO import every row once
