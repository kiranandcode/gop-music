import numpy as np
import matplotlib.pyplot as plt
import scipy.fftpack
from pathlib import Path
from math import ceil

import time
from threading import Thread, Event
import queue

from music_manager import MusicManager
from keyboard_handler import KeyboardBeatDetector
import vlc




def play_song(filename, position=None, fadein=3, fadeout=3, callback=None, volume=60, interval_res=1):
    stop_event = Event()

    def play():
        nonlocal position
        nonlocal fadein
        nonlocal fadeout
        nonlocal callback
        nonlocal volume

        sound_a = vlc.MediaPlayer(filename)

        sound_a.play()
        if interval_res != 1:
            fadein = fadein / interval_res
            fadeout = fadeout / interval_res

        # get the length of the sound (in seconds)
        sound_length = sound_a.get_length() // 1000

        while sound_length == 0:
            sound_length = sound_a.get_length()
        print(sound_length)

        if position is not None:
            # convert position to percentage
            position = position / sound_length
            sound_a.set_position(position)

        # fade in the song
        if fadein is not None:
            current_volume = 0
            increment = volume / fadein

            while current_volume < volume:
                sound_a.audio_set_volume(int(current_volume))
                current_volume += increment
                time.sleep(interval_res)

        sound_a.audio_set_volume(int(volume))

        # wait for a stop message or for song to end
        stop_event.wait(sound_length)

        # fade out the song
        if sound_a.get_position() < 1.0 and fadeout is not None:
            current_volume = volume
            increment = volume / fadeout

            while sound_a.get_position() < 1.0 and current_volume > 0:
                sound_a.audio_set_volume(int(current_volume))
                current_volume -= increment
                time.sleep(interval_res)

        sound_a.stop()

        # if we stopped due to the song ending, call the callback
        if callback and not stop_event.is_set():
            callback(filename)

    t = Thread(target=play)
    t.daemon = True
    t.start()

    return stop_event




class MusicPlayer:
    """
    Plots beats from a queue
    """

    def __init__(self, min_change_time=60, window_size=3.0, **kwargs):
        # create a keyboard detector
        self.detector = KeyboardBeatDetector(**kwargs)
        self.beat_queue = detector.beat_queue

        self.last_song_stop = None
        self.min_change_time = min_change_time
        self.window_size = int(ceil(min_change_time / window_size) + 1)

        self.internal_counts = []
        self.internal_times = []

    def play_song(self, song_name, position=None):
        if self.last_song_stop is not None:
            self.last_song_stop.set()

        self.last_song_stop = play_song(
            song,
            position=position,
            fadein=self.fade_in,
            fadeout=self.fade_out,
            interval_res=self.interval_res,
            callback=self.play_song
        )

    def run(self):

        while True:

            # retrieve the next entry
            (count, time) = self.beat_queue.get()

            self.internal_times.append(time)
            self.internal_counts.append(count)

            if len(self.internal_times) > window_size:
                del self.internal_times[0]
                del self.internal_counts[0]


                # once the window has filled up, we are safe to
                # try changing the music

                next_music = self.beat_changer.change_music(
                    self.internal_times,
                    self.internal_counts
                )

                # if the beat changer requests a music change
                if next_music:
                    song, position = next_music
                    self.play_song(song, position)

# song_a = './music/sample.wav'
# song_b = './music/sample_2.wav'

# stop_song_a = play_song(song_a, 30, interval_res=0.2)
# time.sleep(10)
# print('starting next song')
# stop_song_b = play_song(song_b)
# time.sleep(10)
# print('stopping first song')
# stop_song_a.set()
# time.sleep(10)
# print('stopping second song')
# stop_song_b.set()
