import numpy as np
import matplotlib.pyplot as plt
import scipy.fftpack
from scipy import interpolate

import time
from threading import Thread, Event, RLock
import queue

from pynput.keyboard import Key, Listener, KeyCode


class BeatVisualizer:
    """
    Plots beats from a queue
    """

    def __init__(self, beat_queue, update_interval=None, window_width=None):
        self.beat_queue = beat_queue
        self.update_interval = update_interval
        self.window_width = window_width

        self.internal_counts = []
        self.internal_times = []

    def run(self):
        figure = plt.figure(figsize=(10, 10))
        ax = figure.add_subplot(1, 1, 1)
        plt.ion()

        line, = ax.plot(self.internal_times, self.internal_counts)

        mean_low, = ax.plot([], [], label='low thresh')
        mean_high, = ax.plot([], [], label='high thresh')
        mean_line, = ax.plot([], [], label='mean thresh')
        smooth_line, = ax.plot([], [], label='smooth line')

        low_values = []
        high_values = []
        mean_values = []

        ax.legend()

        figure.show()

        while True:
            if self.update_interval:
                time.sleep(self.update_interval)

            # retrieve the next entry
            (count, time) = self.beat_queue.get()

            self.internal_times.append(time)
            self.internal_counts.append(count)

            internal_times = np.array(self.internal_times)
            internal_counts = np.array(self.internal_counts)



            if self.window_width and len(self.internal_times) > self.window_width:
                del self.internal_times[0]
                del self.internal_counts[0]
                del low_values[0]
                del high_values[0]
                del mean_values[0]

            # update the line
            line.set_xdata(self.internal_times)
            line.set_ydata(self.internal_counts)

            # add mean values
            count_mean = np.array(self.internal_counts).mean()

            low_values.append(count_mean * 0.96)
            high_values.append(count_mean * 1.54) # 1.96
            mean_values.append(count_mean)

            mean_low.set_xdata(self.internal_times)
            mean_low.set_ydata(low_values)

            mean_high.set_xdata(self.internal_times)
            mean_high.set_ydata(high_values)

            mean_line.set_xdata(self.internal_times)
            mean_line.set_ydata(mean_values)

            if len(self.internal_counts) > 3:
                flin = interpolate.interp1d(internal_times, internal_counts, kind='cubic')
                time_resample = np.linspace(internal_times.min(), internal_times.max(), 100)
                counts_resample = flin(time_resample)

                smooth_line.set_xdata(time_resample)
                smooth_line.set_ydata(counts_resample)



            ax.relim()
            ax.autoscale_view()

            figure.canvas.draw()
            figure.canvas.flush_events()

            self.beat_queue.task_done()


def sanitize_keys(keys):
    keycodes = []
    for key in keys:
        if isinstance(key, str):
            if len(key) > 1:
                locals = {'key': None}
                exec('key = Key.{}'.format(key), None, locals)
                key = locals['key']
            else:
                key = KeyCode.from_char(key)
        print(type(key), key)
        keycodes.append(key)
    return keycodes


class KeyboardBeatDetector:

    def __init__(self, window_size=None, exit_keys=None, keys_events=None, event_queue=None):

        self.runner = Thread(
            target=self._run,
        )
        self.runner.daemon = True

        if not exit_keys:
            exit_keys = ['ctrl', 'e']

        if not keys_events:
            keys_events = []

        # hook up all key-events
        self.event_map = []
        for (evnt, keys) in keys_events:
            keycodes = sanitize_keys(keys)
            self.event_map.append(
                (evnt, {k: False for k in keycodes})
            )

        # hook up exit keys
        keycodes = sanitize_keys(exit_keys)
        self.exit_keys = {k: False for k in keycodes}

        self.window_size = window_size or 2.0
        self.exit_req = Event()

        self.beat_queue = queue.Queue()
        if event_queue is None:
            event_queue = self.beat_queue

        self.event_queue = event_queue

        # local execution variables
        self.window_count = 0
        self.window_start = time.time()
        self.data_lock = RLock()

        self.runner.start()

    def _run(self):
        with Listener(
                on_press=self._on_press,
                on_release=self._on_release
        ) as listener:
            # wait until exit requested
            while not self.exit_req.is_set():
                self.exit_req.wait(self.window_size)

                # if wait time exceeds without getting
                # a beat, manually send zero beats
                with self.data_lock:

                    current_time = time.time()
                    delta_time = current_time - self.window_start
                    while delta_time > self.window_size:
                        self.beat_queue.put((self.window_count, self.window_start))
                        self.window_count = 0
                        self.window_start += self.window_size
                        delta_time = current_time - self.window_start

    def _on_press(self, key):
        if key in self.exit_keys:
            self.exit_keys[key] = True

        # if all the exit keys are pressed
        # exit the listener
        if all(self.exit_keys.values()):
            self.exit_req.set()

        for (event, keymap) in self.event_map:
            if key in keymap:
                keymap[key] = True
            if all(keymap.values()):
                self.event_queue.put(event)

        # record the beat
        current_time = time.time()
        with self.data_lock:
            delta_time = current_time - self.window_start

            if delta_time < self.window_size:
                self.window_count += 1
            else:
                # send out the beat_values
                while delta_time > self.window_size:
                    self.beat_queue.put((self.window_count, self.window_start))
                    self.window_count = 0
                    self.window_start += self.window_size
                    delta_time = current_time - self.window_start

                self.window_count = 1
                self.window_start = current_time

    def _on_release(self, key):

        if key in self.exit_keys:
            self.exit_keys[key] = False

        for (event, keymap) in self.event_map:
            if key in keymap:
                keymap[key] = False



if __name__ == '__main__':
    a = KeyboardBeatDetector(window_size=5.0)
    bv = BeatVisualizer(a.beat_queue, window_width=10)
    bv.run()
    a.runner.join()
