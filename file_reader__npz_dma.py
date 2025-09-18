# -*- coding: utf-8 -*-
"""
Created on Mon Sep  8 18:16:13 2025

@author: User
"""

"""
NPZ Signal Viewer with Calibration
Created on Sep 8, 2025
"""

import numpy as np
import matplotlib.pyplot as plt

def scale_to_volts(raw_data, gain=1.0, offset=0.0, scale_factor=1.0):
    """
    Convert raw ADC counts to calibrated voltage:
    V = ((raw * gain) - offset) * scale_factor
    """
    return (raw_data.astype(np.float32) * gain - offset) * scale_factor

# === Load NPZ File ===
data = np.load("save_data.npz")

# === Required raw data ===
raw_ch1 = data['raw_ch1']
raw_ch2 = data['raw_ch2']

# === Calibration Constants ===
gain1 = data['gain1'].item() if 'gain1' in data else 1.0
gain2 = data['gain2'].item() if 'gain2' in data else 1.0
offset1 = data['offset1'].item() if 'offset1' in data else 0.0
offset2 = data['offset2'].item() if 'offset2' in data else 0.0
scale_factor = data['scale_factor'].item() if 'scale_factor' in data else 1.0

# === Flatten for plotting ===
ch1_volts = scale_to_volts(raw_ch1.flatten(), gain1, offset1, scale_factor)
ch2_volts = scale_to_volts(raw_ch2.flatten(), gain2, offset2, scale_factor)
x = np.arange(ch1_volts.size)

# === Plot ===
plt.figure(figsize=(14, 6))
plt.plot(x, ch1_volts, label='Channel 1 (V)', color='blue')
plt.plot(x, ch2_volts, label='Channel 2 (V)', color='red')

decimation = data['decimation'].item() if 'decimation' in data else 1
frame_size = data['frame_size'].item() if 'frame_size' in data else 16384
num_frames = data['num_frames'].item() if 'num_frames' in data else raw_ch1.size/16384
print(f"Decimation factor: {decimation}")

plt.title("Signal Plot with Calibration")
plt.xlabel("Sample Index")
plt.ylabel("Voltage (V)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
