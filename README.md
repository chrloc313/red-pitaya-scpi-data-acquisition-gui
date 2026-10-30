A Python-based GUI for controlling a Red Pitaya via SCPI, featuring a 2-channel signal generator and oscilloscope, DMA-based data acquisition for high-speed data export and live streaming, data visualization, and CSV/NPZ export.

The application supports deep memory waveform acquisition through the Red Pitaya's built-in AXI DMA-backed storage, enabling captures of up to 412 MB with temporary on-device storage and post acquisition file transfer. 

Binary waveform transfer and NumPy based decoding minimize ASCII parsing overhead, supporting reliable acquisition and live data streaming over the SCPI server at approximately 0.5-0.9 MB/s. 

The GUI interface also provides AWG test pattern validation and acquisition trigger controls to support measurements.