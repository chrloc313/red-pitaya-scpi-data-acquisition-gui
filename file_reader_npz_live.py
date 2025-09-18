# -*- coding: utf-8 -*-
"""
Created on Wed Aug 27 14:42:22 2025

@author: User
"""
import numpy as np
import matplotlib.pyplot as plt

def scale_to_volts(raw_data, gain, offset, scale_factor):
    """
    Convert raw ADC counts to volts:
    volts = (raw * gain - offset) * scale_factor
    """
    return (raw_data.astype(np.float32) * gain - offset) * scale_factor

# Load NPZ file
data = np.load("save_data.npz")

# Load raw channels
raw_ch1 = data['raw_ch1']
raw_ch2 = data['raw_ch2']

# Optional averaged channels
avg_ch1 = data['avg_ch1'] if 'avg_ch1' in data else None
avg_ch2 = data['avg_ch2'] if 'avg_ch2' in data else None

# Load calibration constants as scalars directly
gain1 = data['gain1'].item() if 'gain1' in data else 1.0
gain2 = data['gain2'].item() if 'gain2' in data else 1.0
offset1 = data['offset1'].item() if 'offset1' in data else 0.0
offset2 = data['offset2'].item() if 'offset2' in data else 0.0
scale_factor = data['scale_factor'].item() if 'scale_factor' in data else 1.0


# Metadata
decimation = data['decimation'].item() if 'decimation' in data else 1
frame_size = data['frame_size'].item() if 'frame_size' in data else raw_ch1.shape[1]
num_frames = data['num_frames'].item() if 'num_frames' in data else raw_ch1.shape[0]

print(f"Decimation factor: {decimation}")

# Convert raw ADC counts to volts
raw_ch1_volts = scale_to_volts(raw_ch1, gain1, offset1, scale_factor)
raw_ch2_volts = scale_to_volts(raw_ch2, gain2, offset2, scale_factor)

# Flatten for plotting raw data
raw_ch1_flat = raw_ch1_volts.flatten()
raw_ch2_flat = raw_ch2_volts.flatten()

# X axis for raw data
x_raw = np.arange(raw_ch1_flat.shape[0])

# Plot raw data
plt.figure(figsize=(16, 6))
plt.plot(x_raw, raw_ch1_flat, label='Raw Ch1 (Volts)', color='blue')
plt.plot(x_raw, raw_ch2_flat, label='Raw Ch2 (Volts)', color='red')

# Plot avg channels if they exist with their own x axis
if avg_ch1 is not None:
    x_avg_ch1 = np.arange(avg_ch1.size)
    plt.plot(x_avg_ch1, avg_ch1, label='Avg Ch1 (Volts)', color='green', linestyle='--')
if avg_ch2 is not None:
    x_avg_ch2 = np.arange(avg_ch2.size)
    plt.plot(x_avg_ch2, avg_ch2, label='Avg Ch2 (Volts)', color='orange', linestyle='--')


plt.title(f"Signal Plot — {x_raw.shape[0]} samples ({num_frames} frames × {frame_size} samples, Decimation: {decimation})")
plt.xlabel("Sample Index")
plt.ylabel("Voltage (V)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
