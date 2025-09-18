# -*- coding: utf-8 -*-
"""
Created on Mon Sep  8 10:33:04 2025

@author: User
"""

import re
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QFileDialog


def convert_to_printf_format(fmt_str):
    """
    Convert format strings like '1.6f' to printf-style like '%.6f'.
    If parsing fails, default to '%.6f'.
    """
    if not fmt_str:
        return "%.6f"
    match = re.match(r"(\d+)\.(\d+)f", fmt_str)
    if match:
        width, precision = match.groups()
        return f"%.{precision}f"
    else:
        # fallback default
        return "%.6f"


def select_save_file(self, dialog_title, default_name, file_filter):
    options = QFileDialog.Options()
    filename, _ = QFileDialog.getSaveFileName(
        self,
        dialog_title,
        default_name,
        file_filter,
        options=options
    )
    if not filename:
        print("No filename selected — save canceled")
        self.status_label.setText("Save canceled.")
        self.save_button.setEnabled(True)
        return None
    self.filename = filename
    return filename


def validate_buffers(self, *buffers):
    # Check if any buffer is None
    if any(buf is None for buf in buffers):
        self.status_label.setText("Save failed: no data.")
        print("Save failed: some buffers are None")
        return False
    
    # Check if all shapes match
    shapes = [buf.shape for buf in buffers]
    if len(set(shapes)) != 1:
        self.status_label.setText("Save failed: buffer size mismatch.")
        print("Error: Buffers must be the same shape:", shapes)
        return False
    return True


def save_dataframe_to_csv(self, df):
    try:
        float_fmt = convert_to_printf_format(getattr(self, "save_format", None))
        df.to_csv(self.filename, index=False, float_format=float_fmt)
        self.status_label.setText(f"Saved {len(df)} rows to {self.filename}")
        print(f"Saved CSV to {self.filename}")
    except Exception as e:
        print(f"CSV save failed: {e}")
        self.status_label.setText("Save failed.")

def reset_save_state(self):
    # Reset save state
    self.save_buffer_ch1 = None
    self.save_buffer_ch2 = None
    self.save_buffer_avg_ch1 = None
    self.save_buffer_avg_ch2 = None
    self.save_index = 0
    self.save_data_enabled = False
    self.save_button.setEnabled(True)

def save_data_to_npz(self, data_dict):
    try:
        np.savez_compressed(self.filename, **data_dict)
        self.status_label.setText(f"Saved data to {self.filename}")
        print(f"Saved .npz with keys: {list(data_dict.keys())}")
    except Exception as e:
        print(f"NPZ save failed: {e}")
        self.status_label.setText("Save failed.")


def live_save_to_csv(self):
    filename = select_save_file(
        self,
        "Save CSV",
        self.filename,
        "CSV Files (*.csv);;All Files (*)"
    )
    if not filename:
        return
    
    #num_samples_total, num_columns = self.save_buffer.shape
    frame_size = self.FRAME_SIZE
    num_frames = self.current_save_limit

    # Construct CSV columns
    frame_numbers = np.repeat(np.arange(1, num_frames + 1), frame_size)
    sample_indices = np.tile(np.arange(frame_size), num_frames)
    
    data = {
        "Frame": frame_numbers,
        "Sample": sample_indices,
        "Ch1": self.save_buffer_ch1,
        "Ch2": self.save_buffer_ch2
    }
    
    if self.avg_data_enabled:
        data["Avg1"] = self.save_buffer_avg_ch1
        data["Avg2"] = self.save_buffer_avg_ch2
    df = pd.DataFrame(data)

    save_dataframe_to_csv(self, df)

    # Reset states after save
    self.save_index = 0
    self.save_data_enabled = False
    self.save_button.setEnabled(True)


def dma_save_to_csv(self, ch1_buffer, ch2_buffer):
    filename = select_save_file(
        self,
        "Save DMA CSV",
        self.filename,
        "CSV Files (*.csv);;All Files (*)"
    )
    if not filename:
        return

    if not validate_buffers(self, ch1_buffer, ch2_buffer):
        return

    num_samples = len(ch1_buffer)
    indices = np.arange(num_samples)

    data = {
        "Index": indices,
        "Ch1": ch1_buffer,
        "Ch2": ch2_buffer
    }

    df = pd.DataFrame(data)

    save_dataframe_to_csv(self, df)
    

def live_save_to_npz(self):
    filename = select_save_file(
        self,
        "Save Data",
        self.filename.replace(".csv", ".npz"),
        "NumPy Compressed (*.npz);;All Files (*)"
    )
    if not filename:
        return
    
    data_to_save = {
        'raw_ch1': self.save_buffer_ch1.astype(np.int16),
        'raw_ch2': self.save_buffer_ch2.astype(np.int16),
        # Optional averaged channels
        'avg_ch1': self.save_buffer_avg_ch1.astype(np.float32) if self.avg_data_enabled else None,
        'avg_ch2': self.save_buffer_avg_ch2.astype(np.float32) if self.avg_data_enabled else None,
        # Calibration constants
        'gain1': self.GAIN_1,
        'gain2': self.GAIN_2,
        'offset1': self.OFFSET_1,
        'offset2': self.OFFSET_2,
        'scale_factor': self.SCALE_FACTOR,
        # Metadata
        'decimation': int(self.decimation_factor),
        'frame_size': self.FRAME_SIZE,
        'num_frames': self.current_save_limit,
    }

    # Remove None values (e.g., avg_ch1 if not enabled)
    data_to_save = {k: v for k, v in data_to_save.items() if v is not None}
    save_data_to_npz(self, data_to_save)
    reset_save_state(self)


def dma_save_to_npz(self, ch1_buffer, ch2_buffer):
    filename = select_save_file(
        self,
        "Save DMA Data",
        self.filename.replace(".csv", ".npz"),
        "NumPy Compressed (*.npz);;All Files (*)"
    )
    if not filename:
        return

    if not validate_buffers(self, ch1_buffer, ch2_buffer):
        return

    data_to_save = {
        "raw_ch1": ch1_buffer,
        "raw_ch2": ch2_buffer,
        "gain1": self.GAIN_1,
        "gain2": self.GAIN_2,
        "offset1": self.OFFSET_1,
        "offset2": self.OFFSET_2,
        "scale_factor": self.SCALE_FACTOR,
        "decimation": int(self.decimation_factor),
        "frame_size": self.FRAME_SIZE,
        "num_frames": self.current_save_limit,
    }

    save_data_to_npz(self, data_to_save)
