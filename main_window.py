# main_window.py

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
)
from frame_averager import FrameAverager
from ui_components import (
    create_label, create_checkbox, create_spinbox, create_pushbutton,
    create_combobox, create_lineedit, set_label_color
)
from acq_plot import (
    update_plot, update_stats, start_acq, dma_function
)

class MainWindow(QMainWindow):

    MAX_AVG_FRAMES = 100
    MAX_SAVE_FRAMES = 100
    FRAME_SIZE = 16384
    
    OFFSET_1 = -142
    GAIN_1 = 1.17099
    OFFSET_2 = -166
    GAIN_2 = 1.16671
    
    SCALE_FACTOR = 20.0 / 8192
    
    def __init__(self, rp):
        super().__init__()
        self.rp = rp
        self.setup_main_window()
        self.setup_layout()
        self.setup_plot_curves()
        self.setup_stats()
        self.setup_controls()
        self.setup_timers()

        start_acq(self)  # Start acquisition after setup

    def setup_main_window(self):
        self.setObjectName("MainWindow")
        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.setCentralWidget(self.centralwidget)

    def setup_layout(self):
        self.main_layout = QVBoxLayout(self.centralwidget)
        self.graph = pg.PlotWidget()
        self.main_layout.addWidget(self.graph)

        # Create multiple horizontal layouts for controls
        self.row1 = QHBoxLayout()
        self.row2 = QHBoxLayout()
        self.row3 = QHBoxLayout()
        self.row4 = QHBoxLayout()
        self.row5 = QHBoxLayout()
        self.row6 = QHBoxLayout()
        self.row7 = QHBoxLayout()
        self.row8 = QHBoxLayout()

        for layout in (self.row1, self.row2, self.row3, 
                       self.row4, self.row5, self.row6,
                       self.row7, self.row8):
            layout.setSpacing(10)
            self.main_layout.addLayout(layout)
            
    def setup_controls(self):
        # Initialize control states and create widgets
        
        self.show_ch1_enabled = True
        self.show_ch2_enabled = True
        self.avg_data_enabled = False
        self.save_data_enabled = False
        
        # Checkboxes for showing channels
        self.show_ch1_checkbox = create_checkbox("Show Ch 1", self.on_show_ch1_clicked, self.show_ch1_enabled)
        self.show_ch2_checkbox = create_checkbox("Show Ch 2", self.on_show_ch2_clicked, self.show_ch2_enabled)
        
        avg_data_label = create_label("Frames to Average:")
        self.avg_data_checkbox = create_checkbox("Average Data", self.on_avg_data_clicked, self.avg_data_enabled)
        self.avg_spinbox = self.setup_averaging()
        
        self.phase_align_button = create_pushbutton("Phase Align", self.on_phase_align_clicked)

        
        # Add widgets to row 1 layout
        for widget in (self.show_ch1_checkbox, self.show_ch2_checkbox, avg_data_label, 
                       self.avg_spinbox, self.avg_data_checkbox, self.phase_align_button):
            self.row1.addWidget(widget)
        
        # Channel labels and output enable checkboxes
        ch1_label = create_label("Ch_1")
        ch2_label = create_label("Ch_2")
        
        self.ch1_output_checkbox = create_checkbox("ON", lambda: self.on_output_changed(1), True)
        self.ch2_output_checkbox = create_checkbox("ON", lambda: self.on_output_changed(2), True)

        # Waveform controls for each channel
        ch1_waveform_label = create_label("Waveform:")
        ch2_waveform_label = create_label("Waveform:")

        waveforms = ["SINE", "SQUARE", "TRIANGLE", "SAWU", "SAWD", 
                     "PWM", "ARBITRARY", "DC", "DC_NEG"]
        self.ch1_waveform_combobox = create_combobox(lambda: self.on_waveform_changed(1), waveforms)
        self.ch2_waveform_combobox = create_combobox(lambda: self.on_waveform_changed(2), waveforms)
        self.ch2_waveform_combobox.setCurrentText("SQUARE")  

        # Frequency spinboxes
        ch1_freq_label = create_label("Frequency (Hz):")        
        ch2_freq_label = create_label("Frequency (Hz):")        
        min_freq, max_freq, initial_freq = 0, 62_500_000, 1000
        self.ch1_freq_spinbox = create_spinbox(min_freq, max_freq, initial_freq, lambda: self.on_freq_changed(1))
        self.ch2_freq_spinbox = create_spinbox(min_freq, max_freq, initial_freq, lambda: self.on_freq_changed(2))
       
        # Amplitude spinboxes
        ch1_amp_label = create_label("Amplitude (V):")
        ch2_amp_label = create_label("Amplitude (V):")

        min_amp, max_amp, initial_amp = -1, 1, 1
        self.ch1_amp_spinbox = create_spinbox(min_amp, max_amp, initial_amp, lambda: self.on_amp_changed(1),
                                              double=True, decimals=2, step=0.01)
        self.ch2_amp_spinbox = create_spinbox(min_amp, max_amp, initial_amp, lambda: self.on_freq_changed(2),
                                              double=True, decimals=2, step=0.01)
        
        # Add channel 1 controls to row 2 layout
        for widget in (ch1_label, self.ch1_output_checkbox, ch1_waveform_label, self.ch1_waveform_combobox,
                       ch1_freq_label, self.ch1_freq_spinbox, ch1_amp_label, self.ch1_amp_spinbox):
            self.row2.addWidget(widget)
        # Add channel 2 controls to row 3 layout
        for widget in (ch2_label, self.ch2_output_checkbox, ch2_waveform_label, self.ch2_waveform_combobox, 
                       ch2_freq_label, self.ch2_freq_spinbox, ch2_amp_label, self.ch2_amp_spinbox):
            self.row3.addWidget(widget)
        
        # Trigger source and related controls
        self.trigger_source = "CH1_PE"
        self.trigger_source_combo = create_combobox(self.on_trigger_source_changed,
            ["CH1_PE", "CH1_NE", "CH2_PE", "CH2_NE", "EXT_PE", "EXT_NE"])
        
        trigger_source_label = create_label("Trigger Source:")
        trigger_level_label = create_label("Trigger Level:")        
        self.trigger_level_spinbox = create_spinbox(-20.0, 20.0, 0.0, self.on_trigger_level_changed, 
                                                    double=True, decimals=3, step=0.01)
        decimation_factor_label = create_label("Decimation Factor:")
         
        self.decimation_factor = "128"
        self.decimation_factor_combo = create_combobox(self.on_decimation_factor_changed,
            [str(i) for i in [1,2,4,8,16,32,64,128,256,512,1024,2048,4096,8192,16384,32768,65536]]
        )
        self.decimation_factor_combo.setCurrentText(self.decimation_factor)
        
        
        # Add trigger and decimation controls to row 4
        for widget in (trigger_source_label, self.trigger_source_combo,
                       trigger_level_label, self.trigger_level_spinbox,
                       decimation_factor_label, self.decimation_factor_combo):
            self.row4.addWidget(widget)
        
        # Save format and file type controls
        save_format_label = create_label("Save Data String Format:")
        self.save_format = "1.6f"
        self.save_format_input = create_lineedit(self.save_format, self.on_save_format_changed)
        self.save_format_input.setFixedWidth(400)
        
        file_type_label = create_label("Save File as:")
        files  = [".csv", ".npz"]
        self.file_type_combobox = create_combobox(self.on_file_type_changed, files)
        self.file_type = ".csv"
        
        # Add save format and file type controls to row 5
        for widget in (save_format_label, self.save_format_input,
                       file_type_label, self.file_type_combobox):
            self.row5.addWidget(widget)
        
        # Number of frames to save and save button
        save_frames_label = create_label("Number of Frames to Save:")
        self.save_spinbox = self.setup_saving()
        self.save_button = create_pushbutton("Save Live Data", self.on_live_save_clicked)
        
        # Add save frame controls to row 6
        for widget in (save_frames_label, self.save_spinbox, self.save_button):
            self.row6.addWidget(widget)
            
        # DMA controls 
        self.dma_button = create_pushbutton("Deep Memory Acquisition", self.on_dma_clicked)        
        save_size_label = create_label("Number of Bytes to Save:")
        min_save_size = 8192
        max_save_size = int(self.rp.txrx_txt('ACQ:AXI:SIZE?')) 
        self.dma_save_size = min_save_size
        self.dma_save_size_spinbox = create_spinbox(min_save_size, max_save_size, self.dma_save_size,
                                                    self.on_dma_save_size_changed, step=min_save_size)
        
        # Add DMA controls to row 7
        for widget in (save_size_label, self.dma_save_size_spinbox, self.dma_button):
            self.row7.addWidget(widget)

        # Status labels: FPS, MB/s, and status message
        self.fps_label = create_label("FPS: 0.0")
        self.mbps_label = create_label("MB/s: 0.00")
        self.status_label = create_label("")
        set_label_color(self.status_label, "green")
        
        # Add status labels to row 8
        for label in (self.fps_label, self.mbps_label, self.status_label):
            self.row8.addWidget(label)

    def setup_plot_curves(self):
        self.x_axis = np.arange(self.FRAME_SIZE, dtype=np.float32)  # X axis data
        # Create plot curves for each channel and averages
        self.ch1_curve = self.graph.plot(pen='blue')
        self.ch2_curve = self.graph.plot(pen='red')
        self.avg_ch1_curve = self.graph.plot(pen='green')
        self.avg_ch2_curve = self.graph.plot(pen='yellow')
        # Optimize curve rendering
        for curve in [self.ch1_curve, self.ch2_curve, 
                      self.avg_ch1_curve, self.avg_ch2_curve]:
            curve.setSkipFiniteCheck(True)
            curve.setClipToView(True)        

    def setup_stats(self):
        # Initialize statistics counters
        self.byte_count = 0
        self.frame_count = 0
        self.total_frames = 0
        self.seconds_passed = 0

    def setup_timers(self):
        # Timer for updating plots (every 10 ms)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(10)
        
        # Timer for updating stats (every 1 second)
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(1000)

    def setup_averaging(self):
        # Setup frame averaging spinbox and FrameAverager instances
        min_avg_frames = 1
        initial_avg_frames = 10
        self.frame_averager_ch1 = FrameAverager(
            self.MAX_AVG_FRAMES, self.FRAME_SIZE, initial_avg_frames)
        self.frame_averager_ch2 = FrameAverager(
            self.MAX_AVG_FRAMES, self.FRAME_SIZE, initial_avg_frames)
        return create_spinbox(min_avg_frames, self.MAX_AVG_FRAMES, 
                              initial_avg_frames, self.on_avg_N_changed)

    def setup_saving(self):
        # Setup saving spinbox and initialize saving parameters
        min_save_frames = 1
        self.current_save_limit = 10
        self.save_countdown = 0
        self.save_index = 0
        
        self.filename = "save_data.csv"
        return create_spinbox(min_save_frames, self.MAX_SAVE_FRAMES, 
                          self.current_save_limit, self.on_save_limit_changed)

    def update_plot(self):
        update_plot(self)  # Delegate plot update to external function

    def update_stats(self):
        update_stats(self)  # Delegate stats update to external function
    
    def on_show_ch1_clicked(self, state):
        self.show_ch1_enabled = (state == Qt.Checked)
        self.ch1_curve.clear()  # Clear curve when toggled

    def on_show_ch2_clicked(self, state):
        self.show_ch2_enabled = (state == Qt.Checked)
        self.ch2_curve.clear()  # Clear curve when toggled
    
    def on_avg_data_clicked(self, state):
        self.avg_data_enabled = (state == Qt.Checked)
        # Clear average curves and data when toggled
        self.avg_ch1_curve.clear()
        self.avg_ch2_curve.clear()
        self.frame_averager_ch1.clear()
        self.frame_averager_ch2.clear()

    def on_avg_N_changed(self, value):
        # Update number of frames to average and clear buffer
        self.frame_averager_ch1.update_N(value)
        self.frame_averager_ch2.update_N(value)
        self.frame_averager_ch1.clear()
        self.frame_averager_ch2.clear()

    def on_trigger_source_changed(self):
        self.trigger_source = self.trigger_source_combo.currentText()
        start_acq(self)  # Restart acquisition with new trigger source

    def on_trigger_level_changed(self, value):
        self.rp.tx_txt(f'ACQ:TRIG:LEV {value/20}')  # Send trigger level command
        
    def on_decimation_factor_changed(self, index):
        self.decimation_factor = self.decimation_factor_combo.currentText()
        self.rp.tx_txt(f'ACQ:DEC {self.decimation_factor}')  # Send decimation factor command
        start_acq(self)  # Restart acquisition with new decimation factor

    def on_phase_align_clicked(self):
        self.rp.tx_txt('PHAS:ALIGN')  # Send phase alignment command

    def on_file_type_changed(self):
        self.file_type = self.file_type_combobox.currentText()  # Update save file type

    def on_live_save_clicked(self): 
        # Start live data saving
        self.save_index = 0
        self.save_countdown = self.current_save_limit
        self.status_label.setText("Saving...")
        self.save_data_enabled = True
        self.save_button.setEnabled(False)
        
        num_rows = self.current_save_limit * self.FRAME_SIZE
        
        if self.file_type == ".csv":
            data_type = np.float32
        elif self.file_type == ".npz":
            data_type = '>i2'
        else:
            self.status_label.setText("Unsupported file type.")
            self.save_button.setEnabled(True)
            self.save_data_enabled = False
            return
        
        # Allocate buffers for saving data
        self.save_buffer_ch1 = np.empty(num_rows, dtype=data_type)
        self.save_buffer_ch2 = np.empty(num_rows, dtype=data_type)
        
        if self.avg_data_enabled:
            self.save_buffer_avg_ch1 = np.empty(num_rows, dtype=np.float32)
            self.save_buffer_avg_ch2 = np.empty(num_rows, dtype=np.float32)

    def on_save_limit_changed(self, limit):
        self.current_save_limit = limit  # Update save frames limit        

    def on_save_format_changed(self, text):
        try:
            test_value = 1.234567
            formatted = format(test_value, text)  # Test format string validity
            self.save_format = text
            set_label_color(self.save_format_input, "black")  # Valid format
        except (ValueError, TypeError):
            set_label_color(self.save_format_input, "red")    # Invalid format

    def on_dma_clicked(self):
        dma_function(self)  # Call DMA acquisition function
        
    def on_dma_save_size_changed(self, value): 
        # Ensure DMA save size is multiple of 8192 bytes
        if value % 8192 == 0: 
            self.dma_save_size = value 
        self.dma_save_size_spinbox.setValue(self.dma_save_size)
        
    def on_output_changed(self, ch_num):
        # Toggle output state for channel
        checkbox_map = {
            1: self.ch1_output_checkbox,
            2: self.ch2_output_checkbox,
        }
        checkbox = checkbox_map.get(ch_num)
        
        if checkbox.isChecked():
            self.rp.tx_txt(f'OUTPUT{ch_num}:STATE ON')
        else:
            self.rp.tx_txt(f'OUTPUT{ch_num}:STATE OFF')
        
        # Stop acquisition if both outputs off, else start acquisition
        if not (self.ch1_output_checkbox.isChecked() or 
                self.ch2_output_checkbox.isChecked()):
            self.rp.tx_txt('ACQ:STOP')
        else:
            self.rp.tx_txt('ACQ:START')

            
    def on_waveform_changed(self, ch_num):
        # Map channel number to corresponding waveform combobox
        waveform_map = {
            1: self.ch1_waveform_combobox,
            2: self.ch2_waveform_combobox,
        }
        combo = waveform_map.get(ch_num)
        if not combo:
            return
        waveform = combo.currentText()  # Get selected waveform
        self.rp.tx_txt(f'SOUR{ch_num}:FUNC {waveform}')  # Send waveform setting command to device
    
    def on_freq_changed(self, ch_num):
        # Map channel number to corresponding frequency spinbox
        freq_map = {
            1: self.ch1_freq_spinbox,
            2: self.ch2_freq_spinbox,
        }
        spinbox = freq_map.get(ch_num)
        if not spinbox:
            return
        frequency = spinbox.value()  # Get frequency value from spinbox
        self.rp.tx_txt(f'SOUR{ch_num}:FREQ:FIX {frequency}')  # Send frequency setting command to device
    
    def on_amp_changed(self, ch_num):
        # Map channel number to corresponding amplitude spinbox
        amp_map = {
            1: self.ch1_amp_spinbox,
            2: self.ch2_amp_spinbox,
        }
        spinbox = amp_map.get(ch_num)
        if not spinbox:
            return  # Exit if channel number is invalid
        amplitude = spinbox.value()  # Get amplitude value from spinbox
        self.rp.tx_txt(f'SOUR{ch_num}:VOLT {amplitude}')  # Send amplitude setting command to device
    
    
    def closeEvent(self, event):
        # Stop timers on window close
        self.timer.stop()
        self.stats_timer.stop()
        # Turn off output and close device connection
        self.rp.tx_txt('OUTPUT:STATE OFF')
        self.rp.close()
        # Calculate and print average frames per second if possible
        if self.seconds_passed > 0:
            avg_fps = self.total_frames / self.seconds_passed
        else:
            avg_fps = 0.0
        print(f"avg fps: {avg_fps:.2f}, seconds passed: {self.seconds_passed}")
        event.accept()  # Accept the close event to close the window
