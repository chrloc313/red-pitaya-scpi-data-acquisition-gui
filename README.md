# Red Pitaya SCPI Data Acquisition GUI

A Python-based GUI for controlling a Red Pitaya through SCPI. The application provides a two-channel signal generator and oscilloscope, along with high-speed data acquisition, live streaming, and waveform visualization.

The application supports deep-memory waveform acquisition using the Red Pitaya's built-in AXI DMA storage, allowing captures of up to 412 MB. Acquired data is temporarily stored on the device before being transferred to the host computer.

To improve transfer efficiency, waveform data is transmitted in binary format and decoded using NumPy, reducing the overhead associated with ASCII-based communication. This supports waveform acquisition and live data streaming over the SCPI server at approximately 0.5–0.9 MB/s.

Additional GUI features include AWG test-pattern validation, configurable acquisition triggers, and waveform visualization for signal monitoring and measurement.
