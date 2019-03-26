import numpy as np
import matplotlib.pyplot as plt
import scipy.fftpack
from pathlib import Path

import pygame
from pygame.mixer import Sound

import time
from threading import Thread, Event
import queue

from pynput.keyboard import Key, Listener
from music_manager import MusicManager
from keyboard_handler import KeyboardBeatDetector

pygame.mixer.init()
pygame.init()



def play_song(filename, fadein=1000, fadeout=1000, callback=None):
    stop_event = Event()
    def play():
        sound_a = Sound(filename)
        sound_length = sound_a.get_length()

        sound_a.play(fade_ms=fadein)
        # wait for a stop message or for song to end
        stop_event.wait(sound_length)

        sound_a.fadeout(fadeout)

        if callback:
            callback(filename)

    t = Thread(target=play)
    t.daemon = True
    t.start()

    return stop_event




class MusicPlayer:
    """
    Plots beats from a queue
    """

    def __init__(self, beat_queue):
        self.beat_queue = beat_queue

        self.internal_counts = []
        self.internal_times = []

    def run(self):

        while True:

            # retrieve the next entry
            (count, time) = self.beat_queue.get()

            self.internal_times.append(time)
            self.internal_counts.append(count)

stop_song_a = play_song(song_a)
time.sleep(10)
print('starting next song')
stop_song_b = play_song(song_b)
time.sleep(10)
print('stopping first song')
stop_song_a.set()

time.sleep(2)
time.sleep(100)
