# frame_averager.py
# Averages data based on last N acquistions

import numpy as np

class FrameAverager:
    def __init__(self, max_N, frame_size, target_N):
        self.max_N = max_N
        self.frame_size = frame_size
        self.frames = np.zeros((max_N, frame_size), dtype=np.float32)  # initialized with zeros
        self.running_sum = np.zeros(frame_size, dtype=np.float32)      # sum of frames in buffer
        self.next_index = 0
        self.count = 0  # how many real frames added
        self.target_N = target_N

    def add_frame(self, frame):
        frame = frame.astype(np.float32)
        if self.count < self.target_N:
            self.count += 1
            self.running_sum += frame
        elif self.target_N == self.max_N:
            old_frame = self.frames[self.next_index]
            self.running_sum -= old_frame
            self.running_sum += frame
        else:
            # Don't try to maintain a running sum, just rebuild array
            self.frames[self.next_index] = frame
            indices = [(self.next_index - i) % self.max_N for i in range(self.target_N)]
            self.running_sum = np.sum(self.frames[indices], axis=0)
            self.next_index = (self.next_index + 1) % self.max_N
            return
    
        self.frames[self.next_index] = frame
        self.next_index = (self.next_index + 1) % self.max_N

    def update_N(self, new_target_N):
        if new_target_N != self.target_N:
            self.target_N = new_target_N
            # Recalculate running_sum to sum last target_N frames
            indices = [(self.next_index - i - 1) % self.max_N for i in range(self.target_N)]
            self.running_sum = np.sum(self.frames[indices], axis=0)

    def get_average(self):
        #divide by target_N — zeros are part of sum initially
        return self.running_sum / self.target_N

    def clear(self):
        self.frames.fill(0)
        self.running_sum.fill(0)
        self.next_index = 0
        self.count = 0