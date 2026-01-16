"""
Ridge Plot
==========

"""

import numpy as np

import ultraplot as uplt

# Generate sample data
np.random.seed(19680801)
n_datasets = 10
n_points = 50
data = [np.random.randn(n_points) + i for i in range(n_datasets)]
labels = [f"Dataset {i+1}" for i in range(n_datasets)]

# Create a figure and axes
fig, ax = uplt.subplots(figsize=(8, 6))

# Create the ridgeline plot
ax.ridgeline(data, labels=labels, overlap=0.1, cmap="managua")
ax.format(title="Example Ridge Plot", xlabel="Value", ylabel="Dataset")
fig.show()
