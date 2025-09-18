# plot_logic.py
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 25 15:21:51 2025

@author: User
"""

import numpy as np
import time
from save_data import (
    live_save_to_csv, live_save_to_npz, 
    dma_save_to_csv, dma_save_to_npz
)



def update_plot(self):
    
    # Check if acquisition is triggered and ready
    if self.rp.txrx_txt('ACQ:TRIG:STAT?') != 'TD':
        return
    
    # Request binary data from both channels
    self.rp.tx_txt('ACQ:SOUR1:DATA?')
    bin_data_ch1 = self.rp.rx_arb()
    self.rp.tx_txt('ACQ:SOUR2:DATA?')
    bin_data_ch2 = self.rp.rx_arb()
    
    # Start a new acquisition cycle
    start_acq(self)
    
    # Convert binary data to voltage
    volt_data_ch1 = bin_to_volt(bin_data_ch1, self.GAIN_1, self.OFFSET_1, self.SCALE_FACTOR)
    volt_data_ch2 = bin_to_volt(bin_data_ch2, self.GAIN_2, self.OFFSET_2, self.SCALE_FACTOR)

    # Update live plots if channels are enabled
    if self.show_ch1_enabled:
        self.ch1_curve.setData(x=self.x_axis, y=volt_data_ch1)
    if self.show_ch2_enabled:
        self.ch2_curve.setData(x=self.x_axis, y=volt_data_ch2)

    # Handle frame averaging if enabled
    if self.avg_data_enabled:
        self.frame_averager_ch1.add_frame(volt_data_ch1)
        self.frame_averager_ch2.add_frame(volt_data_ch2)

        avg_ch1 = self.frame_averager_ch1.get_average()
        avg_ch2 = self.frame_averager_ch2.get_average()

        self.avg_ch1_curve.setData(x=self.x_axis, y=avg_ch1)
        self.avg_ch2_curve.setData(x=self.x_axis, y=avg_ch2)

    # Save data to buffer if saving is enabled
    if self.save_data_enabled and self.save_countdown > 0:    
        start_idx = self.save_index
        end_idx = self.save_index + self.FRAME_SIZE
    
        if self.file_type == ".csv":
            self.save_buffer_ch1[start_idx:end_idx] = volt_data_ch1
            self.save_buffer_ch2[start_idx:end_idx] = volt_data_ch2
            
        elif self.file_type == ".npz":
            self.save_buffer_ch1[start_idx:end_idx] = np.frombuffer(bin_data_ch1, dtype='>i2')
            self.save_buffer_ch2[start_idx:end_idx] = np.frombuffer(bin_data_ch2, dtype='>i2')
        
        # Save averaged data if both are enabled
        if self.avg_data_enabled:
            self.save_buffer_avg_ch1[start_idx:end_idx] = avg_ch1
            self.save_buffer_avg_ch2[start_idx:end_idx] = avg_ch2
        
        self.save_index += self.FRAME_SIZE
        self.save_countdown -= 1
        
        # If finished saving, write to file
        if self.save_countdown == 0:
            if self.file_type == ".csv":
                live_save_to_csv(self)
            elif self.file_type == ".npz":
                live_save_to_npz(self)
    
    # Update performance counters
    self.frame_count += 1
    self.byte_count += (len(bin_data_ch1) + len(bin_data_ch2))

def start_acq(self):
    self.rp.tx_txt('ACQ:START')
    self.rp.tx_txt(f'ACQ:TRIG {self.trigger_source}')

def update_stats(self):
    self.fps_label.setText(f'FPS: {self.frame_count:.2f}')
    self.mbps_label.setText(f'MB/s: {self.byte_count / (1024 * 1024):.2f}')
    
    # Track total stats
    self.total_frames += self.frame_count
    self.seconds_passed += 1
    
    # Reset counters for next interval
    self.frame_count = 0
    self.byte_count = 0
    
def bin_to_volt(bin_data, gain, offset, scale_factor):
    raw_data = np.frombuffer(bin_data, dtype='>i2').astype(np.float32)
    #volt_data = (raw_data * gain - offset) * scale_factor
    volt_data = (raw_data * gain - offset) * scale_factor
    return volt_data

def dma_function(self): #TODO: ADD CHOICE TO CUSTOMIZE BYTES
    
    # Set total size to acquire
    total_bytes = self.dma_save_size
    bytes_per_ch = total_bytes//2
    total_samples = total_bytes//2
    samples_per_ch = total_samples//2
    
    # Get starting memory address
    start_address = int(self.rp.txrx_txt('ACQ:AXI:START?'))
    start_address2 = start_address + bytes_per_ch
        
    # Configure acquisition settings
    self.rp.tx_txt(f"ACQ:AXI:DEC {self.decimation_factor}")
    self.rp.tx_txt('ACQ:DATA:FORMAT BIN')
    self.rp.tx_txt('ACQ:AXI:DATA:UNITS RAW')
    
    # Configure trigger delay
    self.rp.tx_txt(f"ACQ:AXI:SOUR1:Trig:Dly {total_samples}")
    self.rp.tx_txt(f"ACQ:AXI:SOUR2:Trig:Dly {total_samples}")
    
    # Assign memory buffers to channels in fpga
    self.rp.tx_txt(f"ACQ:AXI:SOUR1:SET:Buffer {start_address},{bytes_per_ch}")
    self.rp.tx_txt(f"ACQ:AXI:SOUR2:SET:Buffer {start_address2},{bytes_per_ch}")
    
    # Enable DMA capture for both channels
    self.rp.tx_txt('ACQ:AXI:SOUR1:ENable ON')
    self.rp.tx_txt('ACQ:AXI:SOUR2:ENable ON')
  
    # Start acquisition    
    start_acq(self) 
    
    
    # Wait for trigger detection
    while 1:
        self.rp.tx_txt("ACQ:TRig:STAT?")
        if self.rp.rx_txt() == 'TD':
            break
    
    start_time = time.time()
    
    # Wait for buffers to fill
    while 1:
        self.rp.tx_txt('ACQ:AXI:SOUR1:TRig:FILL?')
        if self.rp.rx_txt() == '1':
            break
        
    end_time = time.time()
    print(f"DMA: All data captured in {end_time - start_time} seconds")
    
    
    # Stop acquisition
    self.rp.tx_txt('ACQ:STOP')
    
    # Get trigger position
    pointer_Ch1 = int(self.rp.txrx_txt('ACQ:AXI:SOUR1:Trig:Pos?'))
    pointer_Ch2 = int(self.rp.txrx_txt('ACQ:AXI:SOUR2:Trig:Pos?'))
          
    # Initialize save buffers
    samples_to_receive = samples_per_ch
    if self.file_type == ".csv":
        ch1_buffer = np.empty(samples_to_receive, dtype=np.float32)
        ch2_buffer = np.empty(samples_to_receive, dtype=np.float32)
    elif self.file_type == ".npz":
        ch1_buffer = np.empty(samples_to_receive, dtype='>i2')
        ch2_buffer = np.empty(samples_to_receive, dtype='>i2')
    else:
        self.status_label.setText("Unsupported file type.")
        self.save_button.setEnabled(True)
        self.save_data_enabled = False
        return
    
    # Receive data in chunks
    index = 0
    max_block_size = 1024 * 1024
    
    while index < samples_to_receive:
        remaining = samples_to_receive - index
        current_block_size = min(max_block_size, remaining)
    
        # Channel 1
        self.rp.tx_txt(f'ACQ:AXI:SOUR1:DATA:Start:N? {pointer_Ch1},{current_block_size}')
        bin_data_ch1 = self.rp.rx_arb()
    
        if self.file_type == ".csv":
            volt_data_ch1 = bin_to_volt(bin_data_ch1, self.GAIN_1, self.OFFSET_1, self.SCALE_FACTOR)
            ch1_buffer[index: index + current_block_size] = volt_data_ch1
        elif self.file_type == ".npz":
            ch1_buffer[index: index + current_block_size] = np.frombuffer(bin_data_ch1, dtype='>i2')
    
        # Channel 2
        self.rp.tx_txt(f'ACQ:AXI:SOUR2:DATA:Start:N? {pointer_Ch2},{current_block_size}')
        bin_data_ch2 = self.rp.rx_arb()
    
        if self.file_type == ".csv":
            volt_data_ch2 = bin_to_volt(bin_data_ch2, self.GAIN_2, self.OFFSET_2, self.SCALE_FACTOR)
            ch2_buffer[index: index + current_block_size] = volt_data_ch2
        elif self.file_type == ".npz":
            ch2_buffer[index: index + current_block_size] = np.frombuffer(bin_data_ch2, dtype='>i2')
    
        # Update pointers and index
        pointer_Ch1 += current_block_size
        pointer_Ch2 += current_block_size
        index += current_block_size

    # Save acquired data
    if self.file_type == ".csv":
        dma_save_to_csv(self, ch1_buffer, ch2_buffer)
    elif self.file_type == ".npz":
        dma_save_to_npz(self, ch1_buffer, ch2_buffer)