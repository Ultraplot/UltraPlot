#!/usr/bin/env python3
"""
Thread-Safe Configuration
==========================

This example demonstrates the thread-safe behavior of UltraPlot's
configuration system, showing how settings can be isolated per-thread
using context managers.
"""

import threading
import time

import ultraplot as uplt

# %%
# Global vs Thread-Local Changes
# -------------------------------
# Changes outside a context manager are global and persistent.
# Changes inside a context manager are thread-local and temporary.

# Store original font size
original_size = uplt.rc["font.size"]
print(f"Original font size: {original_size}")

# Global change (persistent)
uplt.rc["font.size"] = 12
print(f"After global change: {uplt.rc['font.size']}")

# Thread-local change (temporary)
with uplt.rc_matplotlib:
    uplt.rc_matplotlib["font.size"] = 20
    print(f"Inside context: {uplt.rc_matplotlib['font.size']}")

# After context, reverts to previous value
print(f"After context: {uplt.rc_matplotlib['font.size']}")

# Restore original
uplt.rc["font.size"] = original_size

# %%
# Parallel Thread Testing
# ------------------------
# Each thread can have its own isolated settings when using context managers.


def create_plot_in_thread(thread_id, results):
    """Create a plot with thread-specific settings."""
    with uplt.rc_matplotlib:
        # Each thread uses different settings
        thread_font_size = 8 + thread_id * 2
        uplt.rc_matplotlib["font.size"] = thread_font_size
        uplt.rc["axes.grid"] = thread_id % 2 == 0  # Grid on/off alternating

        # Verify settings are isolated
        actual_size = uplt.rc_matplotlib["font.size"]
        results[thread_id] = {
            "expected": thread_font_size,
            "actual": actual_size,
            "isolated": (actual_size == thread_font_size),
        }

        # Small delay to increase chance of interference if not thread-safe
        time.sleep(0.1)

        # Create a simple plot
        fig, ax = uplt.subplots(figsize=(3, 2))
        ax.plot([1, 2, 3], [1, 2, 3])
        ax.format(
            title=f"Thread {thread_id}",
            xlabel="x",
            ylabel="y",
        )
        uplt.close(fig)  # Clean up

    # After context, settings are restored
    print(f"Thread {thread_id}: Settings isolated = {results[thread_id]['isolated']}")


# Run threads in parallel
results = {}
threads = [
    threading.Thread(target=create_plot_in_thread, args=(i, results)) for i in range(5)
]

print("\nRunning parallel threads with isolated settings...")
for t in threads:
    t.start()
for t in threads:
    t.join()

# Verify all threads had isolated settings
all_isolated = all(r["isolated"] for r in results.values())
print(f"\nAll threads had isolated settings: {all_isolated}")

# %%
# Use Case: Parallel Testing
# ---------------------------
# This is particularly useful for running tests in parallel where each
# test needs different matplotlib/ultraplot settings.


def run_test_with_settings(test_id, settings):
    """Run a test with specific settings."""
    with uplt.rc_matplotlib:
        # Apply test-specific settings
        uplt.rc.update(settings)

        # Run test code
        fig, axs = uplt.subplots(ncols=2, figsize=(6, 2))
        axs[0].plot([1, 2, 3], [1, 4, 2])
        axs[1].scatter([1, 2, 3], [2, 1, 3])
        axs.format(suptitle=f"Test {test_id}")

        # Verify settings
        print(f"Test {test_id}: font.size = {uplt.rc['font.size']}")

        uplt.close(fig)  # Clean up


# Different tests with different settings
test_settings = [
    {"font.size": 10, "axes.grid": True},
    {"font.size": 14, "axes.grid": False},
    {"font.size": 12, "axes.titleweight": "bold"},
]

print("\nRunning parallel tests with different settings...")
test_threads = [
    threading.Thread(target=run_test_with_settings, args=(i, settings))
    for i, settings in enumerate(test_settings)
]

for t in test_threads:
    t.start()
for t in test_threads:
    t.join()

print("\nAll tests completed without interference!")

# %%
# Important Notes
# ---------------
# 1. Changes outside context managers are global and affect all threads
# 2. Changes inside context managers are thread-local and temporary
# 3. Context managers automatically clean up when exiting
# 4. This works for rc, rc_matplotlib, and rc_ultraplot
# 5. Perfect for parallel test execution and multi-threaded applications
