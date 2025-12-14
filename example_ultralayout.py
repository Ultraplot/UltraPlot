#!/usr/bin/env python3
"""
Simple example demonstrating UltraLayout for non-orthogonal subplot arrangements.

This example shows how subplot 3 gets centered between subplots 1 and 2 when
using UltraLayout with the layout: [[1, 1, 2, 2], [0, 3, 3, 0]]
"""

import matplotlib.pyplot as plt
import numpy as np

try:
    import ultraplot as uplt
except ImportError:
    print("ERROR: UltraPlot not installed or not in PYTHONPATH")
    print("Try: export PYTHONPATH=/Users/vanelter@qut.edu.au/Documents/UltraPlot:$PYTHONPATH")
    exit(1)

# Check if kiwisolver is available
try:
    import kiwisolver
    print(f"✓ kiwisolver available (v{kiwisolver.__version__})")
except ImportError:
    print("⚠ WARNING: kiwisolver not installed")
    print("  Install with: pip install kiwisolver")
    print("  Layouts will fall back to standard grid positioning\n")

# Create a non-orthogonal layout
# Subplot 1 spans columns 0-1 in row 0
# Subplot 2 spans columns 2-3 in row 0
# Subplot 3 spans columns 1-2 in row 1 (centered between 1 and 2)
# Cells at (1,0) and (1,3) are empty (0)
layout = [[1, 1, 2, 2],
          [0, 3, 3, 0]]

print("Creating figure with layout:")
print(np.array(layout))

# Create the subplots
fig, axs = uplt.subplots(array=layout, figsize=(10, 6), wspace=0.5, hspace=0.5)

# Style subplot 1
axs[0].plot([0, 1, 2, 3], [0, 2, 1, 3], 'o-', linewidth=2, markersize=8)
axs[0].set_title('Subplot 1\n(Top Left)', fontsize=14, fontweight='bold')
axs[0].format(xlabel='X axis', ylabel='Y axis')
axs[0].set_facecolor('#f0f0f0')

# Style subplot 2
axs[1].plot([0, 1, 2, 3], [3, 1, 2, 0], 's-', linewidth=2, markersize=8)
axs[1].set_title('Subplot 2\n(Top Right)', fontsize=14, fontweight='bold')
axs[1].format(xlabel='X axis', ylabel='Y axis')
axs[1].set_facecolor('#f0f0f0')

# Style subplot 3 - this should be centered!
axs[2].plot([0, 1, 2, 3], [1.5, 2.5, 2, 1], '^-', linewidth=2, markersize=8, color='red')
axs[2].set_title('Subplot 3\n(Bottom Center - Should be centered!)',
                 fontsize=14, fontweight='bold', color='red')
axs[2].format(xlabel='X axis', ylabel='Y axis')
axs[2].set_facecolor('#fff0f0')

# Add overall title
fig.suptitle('Non-Orthogonal Layout with UltraLayout\nSubplot 3 is centered between 1 and 2',
             fontsize=16, fontweight='bold')

# Print position information
print("\nSubplot positions (in figure coordinates):")
for i, ax in enumerate(axs, 1):
    pos = ax.get_position()
    print(f"  Subplot {i}: x=[{pos.x0:.3f}, {pos.x1:.3f}], "
          f"y=[{pos.y0:.3f}, {pos.y1:.3f}], "
          f"center_x={pos.x0 + pos.width/2:.3f}")

# Check if subplot 3 is centered
if len(axs) >= 3:
    pos1 = axs[0].get_position()
    pos2 = axs[1].get_position()
    pos3 = axs[2].get_position()

    # Calculate expected center (midpoint between subplot 1 and 2)
    expected_center = (pos1.x0 + pos2.x1) / 2
    actual_center = pos3.x0 + pos3.width / 2

    print(f"\nCentering check:")
    print(f"  Expected center of subplot 3: {expected_center:.3f}")
    print(f"  Actual center of subplot 3: {actual_center:.3f}")
    print(f"  Difference: {abs(actual_center - expected_center):.3f}")

    if abs(actual_center - expected_center) < 0.01:
        print("  ✓ Subplot 3 is nicely centered!")
    else:
        print("  ⚠ Subplot 3 might not be perfectly centered")
        print("  (This is expected if kiwisolver is not installed)")

# Save the figure
output_file = 'ultralayout_example.png'
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"\n✓ Saved figure to: {output_file}")

# Show the plot
plt.show()

print("\nDone!")
