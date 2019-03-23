import numpy as np
import matplotlib.pyplot as plt
import scipy.fftpack

import time
from threading import Thread, Event
import queue

from pynput.keyboard import Key, Listener, KeyCode


class KeyboardBeatDetector:


    def __init__(self, window_size=None, exit_keys=None):

        self.runner = Thread(
            target=self._run,
        )
#        self.runner.daemon = True

        if not exit_keys:
            exit_keys = ['ctrl', 'e']

        keycodes = []
        for key in exit_keys:
            if isinstance(key, str):
                if len(key) > 1:
                    locals = {'key': None}
                    exec('key = Key.{}'.format(key), None, locals)
                    key = locals['key']
                else:
                    key = KeyCode.from_char(key)
            print(type(key), key)
            keycodes.append(key)

        self.window_size = window_size or 2.0
        self.exit_keys = {k: False for k in keycodes}
        self.exit_req = Event()

        self.beat_queue = queue.Queue()

        # local execution variables
        self.window_count = 0
        self.window_start = time.time()

        self.runner.start()

    def _run(self):
        with Listener(
                on_press = self._on_press,
                on_release = self._on_release
        ) as listener:
            # wait until exit requested
            self.exit_req.wait()

    def _on_press(self, key):
        if key in self.exit_keys:
            self.exit_keys[key] = True

        # record the beat
        current_time = time.time()
        delta_time = current_time - self.window_start

        if delta_time < self.window_size:
            self.window_count += 1
        else:
            # send out the beat_values
            self.beat_queue.put((self.window_count, self.window_start))

            self.window_count = 1
            self.window_start = current_time

        # if all the exit keys are pressed
        # exit the listener
        if all(self.exit_keys.values()):
            self.exit_req.set()


    def _on_release(self, key):

        if key in self.exit_keys:
            self.exit_keys[key] = False

print('Starting thread')
a = KeyboardBeatDetector()
a.runner.join()
print('Done thread')
