#!/usr/bin/env python3
"""
Demo script to test the UltraLayout functionality for non-orthogonal subplot arrangements.

This script demonstrates how UltraLayout's constraint-based system handles cases like:
[[1, 1, 2, 2],
 [0, 3, 3, 0]]

where subplot 3 should be nicely centered between subplots 1 and 2.
"""

import matplotlib.pyplot as plt
import numpy as np

try:
    import ultraplot as uplt
    ULTRAPLOT_AVAILABLE = True
except ImportError:
    ULTRAPLOT_AVAILABLE = False
    print("UltraPlot not available. Please install it first.")
    exit(1)


def test_orthogonal_layout():
    """Test with a standard orthogonal (grid-aligned) layout."""
    print("\n=== Testing Orthogonal Layout ===")
    array = [[1, 2], [3, 4]]

    fig, axs = uplt.subplots(array=array, figsize=(8, 6))

    for i, ax in enumerate(axs, 1):
        ax.plot([0, 1], [0, 1])
        ax.set_title(f'Subplot {i}')
        ax.format(xlabel='X', ylabel='Y')

    fig.suptitle('Orthogonal Layout (Standard Grid)')
    plt.savefig('test_orthogonal_layout.png', dpi=150, bbox_inches='tight')
    print("Saved: test_orthogonal_layout.png")
    plt.close()


def test_non_orthogonal_layout():
    """Test with a non-orthogonal layout where subplot 3 should be centered."""
    print("\n=== Testing Non-Orthogonal Layout ===")
    array = [[1, 1, 2, 2],
             [0, 3, 3, 0]]

    fig, axs = uplt.subplots(array=array, figsize=(10, 6))

    # Add content to each subplot
    axs[0].plot([0, 1, 2], [0, 1, 0], 'o-')
    axs[0].set_title('Subplot 1 (Top Left)')
    axs[0].format(xlabel='X', ylabel='Y')

    axs[1].plot([0, 1, 2], [1, 0, 1], 's-')
    axs[1].set_title('Subplot 2 (Top Right)')
    axs[1].format(xlabel='X', ylabel='Y')

    axs[2].plot([0, 1, 2], [0.5, 1, 0.5], '^-')
    axs[2].set_title('Subplot 3 (Bottom Center - should be centered!)')
    axs[2].format(xlabel='X', ylabel='Y')

    fig.suptitle('Non-Orthogonal Layout with UltraLayout')
    plt.savefig('test_non_orthogonal_layout.png', dpi=150, bbox_inches='tight')
    print("Saved: test_non_orthogonal_layout.png")
    plt.close()


def test_complex_layout():
    """Test with a more complex non-orthogonal layout."""
    print("\n=== Testing Complex Layout ===")
    array = [[1, 1, 1, 2],
             [3, 3, 0, 2],
             [4, 5, 5, 5]]

    fig, axs = uplt.subplots(array=array, figsize=(12, 9))

    titles = [
        'Subplot 1 (Top - Wide)',
        'Subplot 2 (Right - Tall)',
        'Subplot 3 (Middle Left)',
        'Subplot 4 (Bottom Left)',
        'Subplot 5 (Bottom - Wide)'
    ]

    for i, (ax, title) in enumerate(zip(axs, titles), 1):
        ax.plot(np.random.randn(20).cumsum())
        ax.set_title(title)
        ax.format(xlabel='X', ylabel='Y')

    fig.suptitle('Complex Non-Orthogonal Layout')
    plt.savefig('test_complex_layout.png', dpi=150, bbox_inches='tight')
    print("Saved: test_complex_layout.png")
    plt.close()


def test_layout_detection():
    """Test the layout detection algorithm."""
    print("\n=== Testing Layout Detection ===")

    from ultraplot.ultralayout import is_orthogonal_layout

    # Test cases
    test_cases = [
        ([[1, 2], [3, 4]], True, "2x2 grid"),
        ([[1, 1, 2, 2], [0, 3, 3, 0]], False, "Centered subplot"),
        ([[1, 1], [1, 2]], True, "L-shape but orthogonal"),
        ([[1, 2, 3], [4, 5, 6]], True, "2x3 grid"),
        ([[1, 1, 1], [2, 0, 3]], False, "Non-orthogonal with gap"),
    ]

    for array, expected, description in test_cases:
        array = np.array(array)
        result = is_orthogonal_layout(array)
        status = "✓" if result == expected else "✗"
        print(f"{status} {description}: orthogonal={result} (expected={expected})")


def test_kiwi_availability():
    """Check if kiwisolver is available."""
    print("\n=== Checking Kiwisolver Availability ===")
    try:
        import kiwisolver
        print(f"✓ kiwisolver is available (version {kiwisolver.__version__})")
        return True
    except ImportError:
        print("✗ kiwisolver is NOT available")
        print("  Install with: pip install kiwisolver")
        return False


def print_position_info(fig, axs, layout_name):
    """Print position information for debugging."""
    print(f"\n--- {layout_name} Position Info ---")
    for i, ax in enumerate(axs, 1):
        pos = ax.get_position()
        print(f"Subplot {i}: x0={pos.x0:.3f}, y0={pos.y0:.3f}, "
              f"width={pos.width:.3f}, height={pos.height:.3f}")


def main():
    """Run all tests."""
    print("="*60)
    print("Testing UltraPlot UltraLayout System")
    print("="*60)

    # Check if kiwisolver is available
    kiwi_available = test_kiwi_availability()

    if not kiwi_available:
        print("\nWARNING: kiwisolver not available.")
        print("Non-orthogonal layouts will fall back to standard grid layout.")

    # Test layout detection
    test_layout_detection()

    # Test orthogonal layout
    test_orthogonal_layout()

    # Test non-orthogonal layout
    test_non_orthogonal_layout()

    # Test complex layout
    test_complex_layout()

    print("\n" + "="*60)
    print("All tests completed!")
    print("Check the generated PNG files to see the results.")
    print("="*60)


if __name__ == '__main__':
    main()
