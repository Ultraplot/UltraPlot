#!/usr/bin/env python3
"""
Minimal test to verify kiwi layout basic functionality.
"""

import os
import sys

# Add UltraPlot to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Testing Kiwi Layout Implementation")
print("=" * 60)

# Test 1: Import modules
print("\n[1/6] Testing imports...")
try:
    import numpy as np
    print("  ✓ numpy imported")
except ImportError as e:
    print(f"  ✗ Failed to import numpy: {e}")
    sys.exit(1)

try:
    from ultraplot import kiwi_layout
    print("  ✓ kiwi_layout module imported")
except ImportError as e:
    print(f"  ✗ Failed to import kiwi_layout: {e}")
    sys.exit(1)

try:
    from ultraplot.gridspec import GridSpec
    print("  ✓ GridSpec imported")
except ImportError as e:
    print(f"  ✗ Failed to import GridSpec: {e}")
    sys.exit(1)

# Test 2: Check kiwisolver availability
print("\n[2/6] Checking kiwisolver...")
try:
    import kiwisolver
    print(f"  ✓ kiwisolver available (v{kiwisolver.__version__})")
    KIWI_AVAILABLE = True
except ImportError:
    print("  ⚠ kiwisolver NOT available (this is OK, will fall back)")
    KIWI_AVAILABLE = False

# Test 3: Test layout detection
print("\n[3/6] Testing layout detection...")
test_cases = [
    ([[1, 2], [3, 4]], True, "2x2 grid"),
    ([[1, 1, 2, 2], [0, 3, 3, 0]], False, "Non-orthogonal"),
]

for array, expected, description in test_cases:
    array = np.array(array)
    result = kiwi_layout.is_orthogonal_layout(array)
    if result == expected:
        print(f"  ✓ {description}: correctly detected as {'orthogonal' if result else 'non-orthogonal'}")
    else:
        print(f"  ✗ {description}: detected as {'orthogonal' if result else 'non-orthogonal'}, expected {'orthogonal' if expected else 'non-orthogonal'}")

# Test 4: Test GridSpec with layout array
print("\n[4/6] Testing GridSpec with layout_array...")
try:
    layout = np.array([[1, 1, 2, 2], [0, 3, 3, 0]])
    gs = GridSpec(2, 4, layout_array=layout)
    print(f"  ✓ GridSpec created with layout_array")
    print(f"    - Layout shape: {gs._layout_array.shape}")
    print(f"    - Use kiwi layout: {gs._use_kiwi_layout}")
    print(f"    - Expected: {KIWI_AVAILABLE and not kiwi_layout.is_orthogonal_layout(layout)}")
except Exception as e:
    print(f"  ✗ Failed to create GridSpec: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test kiwi solver (if available)
if KIWI_AVAILABLE:
    print("\n[5/6] Testing kiwi solver...")
    try:
        layout = np.array([[1, 1, 2, 2], [0, 3, 3, 0]])
        positions = kiwi_layout.compute_kiwi_positions(
            layout,
            figwidth=10.0,
            figheight=6.0,
            wspace=[0.2, 0.2, 0.2],
            hspace=[0.2],
            left=0.125,
            right=0.125,
            top=0.125,
            bottom=0.125
        )
        print(f"  ✓ Kiwi solver computed positions for {len(positions)} subplots")
        for num, (left, bottom, width, height) in positions.items():
            print(f"    Subplot {num}: left={left:.3f}, bottom={bottom:.3f}, "
                  f"width={width:.3f}, height={height:.3f}")

        # Check if subplot 3 is centered
        if 3 in positions:
            left3, bottom3, width3, height3 = positions[3]
            center3 = left3 + width3 / 2
            print(f"    Subplot 3 center: {center3:.3f}")
    except Exception as e:
        print(f"  ✗ Kiwi solver failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n[5/6] Skipping kiwi solver test (kiwisolver not available)")

# Test 6: Test with matplotlib if available
print("\n[6/6] Testing with matplotlib (if available)...")
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt

    import ultraplot as uplt

    layout = [[1, 1, 2, 2], [0, 3, 3, 0]]
    fig, axs = uplt.subplots(array=layout, figsize=(10, 6))

    print(f"  ✓ Created figure with {len(axs)} subplots")

    # Get positions
    for i, ax in enumerate(axs, 1):
        pos = ax.get_position()
        print(f"    Subplot {i}: x=[{pos.x0:.3f}, {pos.x1:.3f}], "
              f"y=[{pos.y0:.3f}, {pos.y1:.3f}]")

    plt.close(fig)
    print("  ✓ Test completed successfully")

except ImportError as e:
    print(f"  ⚠ Skipping matplotlib test: {e}")
except Exception as e:
    print(f"  ✗ Matplotlib test failed: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 60)
print("Testing Complete!")
print("=" * 60)
print("\nNext steps:")
print("1. If kiwisolver is not installed: pip install kiwisolver")
print("2. Run the full demo: python test_kiwi_layout_demo.py")
print("3. Run the simple example: python example_kiwi_layout.py")
print("=" * 60)
