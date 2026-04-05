"""Application-wide constants for PPTX Agent.

This module defines magic numbers as named constants to improve
code readability and maintainability.
"""

# =============================================================================
# EMU (English Metric Units) Conversion Constants
# =============================================================================

# PowerPoint uses EMU (English Metric Units) for internal measurements
# 914400 EMU = 1 inch
EMU_PER_INCH = 914400

# Average character width in EMU (approximately 7 points)
EMU_PER_CHAR_WIDTH = 70000

# Average line height in EMU (approximately 12 points)
EMU_PER_LINE_HEIGHT = 120000


# =============================================================================
# Text Capacity Estimation Constants
# =============================================================================

# Average character width in inches at 12pt font
CHAR_WIDTH_INCHES = 0.1

# Average line height in inches at 12pt font
LINE_HEIGHT_INCHES = 0.2

# Minimum character capacity for any placeholder
MIN_PLACEHOLDER_CHARS = 50

# Default character capacity when dimensions are unavailable
DEFAULT_PLACEHOLDER_CHARS = 100


# =============================================================================
# Default Shape Positioning (in Inches)
# =============================================================================

# Default X position for shapes when placeholder not found
DEFAULT_SHAPE_LEFT_INCHES = 1

# Default Y position for shapes when placeholder not found
DEFAULT_SHAPE_TOP_INCHES = 2

# Default width for shapes when placeholder not found
DEFAULT_SHAPE_WIDTH_INCHES = 6

# Default height for shapes when placeholder not found
DEFAULT_SHAPE_HEIGHT_INCHES = 4


# =============================================================================
# Presentation Constraints
# =============================================================================

# Minimum number of slides per FR-019 requirement
MIN_SLIDES = 3

# Maximum number of slides per FR-019 requirement
MAX_SLIDES = 30


# =============================================================================
# Percentage Calculation Constants
# =============================================================================

# Multiplier for converting decimal to percentage
PERCENTAGE_MULTIPLIER = 100.0
