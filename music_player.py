import time
from math import ceil
from subprocess import call
from threading import Event, Thread

import vlc

from keyboard_handler import KeyboardBeatDetector
from music_manager import open_saved_mm


def send_notification(msg):
    """
    Sends the provided message as a notification
    :param msg: message to print in notification
    """
    call(['notify-send', msg])


def play_song(filename, position=None, fadein=3, fadeout=3, callback=None, volume=60, interval_res=1.0):
    """
    Custom function supporting playing songs with fadein and fadeout using VLC media player.

    :param filename: file to be played
    :param position: position (in seconds) to play
    :param fadein: number of seconds to use for fading in the song
    :param fadeout: number of seconds to use for fading out the sonc
    :param callback: callback to be called when music finishes
    :param volume: the volume at which the song should be played
    :param interval_res: the number of seconds between updates when fading in the song

    :return: a condition object that can be set to stop the playback
    """
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
        stop_event.wait(max(sound_length - fadeout, 0))

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


class BeatChangerWrapperPlayer:
    """
    Given a beat changer object, implements a media player which will play the
    audio suggested by the beat changer and feed in keyboard presses to the
    beat changer.
    """

    def __init__(
            self, beat_changer, music_manager=None,
            beat_window_size=3.0, interval_res=0.2, fade_in=3, fade_out=3,
            min_change_time=60,
            exit_keys=None, keys_events=None, send_notifications=False
    ):
        if music_manager is None:
            music_manager = open_saved_mm('default')

        # create a keyboard detector
        self.keyboard_detector = KeyboardBeatDetector(
            window_size=beat_window_size,
            exit_keys=exit_keys,
            keys_events=keys_events,
        )

        # retrieve a beat queue
        self.beat_queue = self.keyboard_detector.beat_queue
        self.last_song_stop = None

        # calculate the number of beat_windows to include in an analysis time
        self.window_size = int(ceil(min_change_time / beat_window_size) + 1)

        # two variables to keep track of recieved data
        self.internal_counts = []
        self.internal_times = []

        # parameters used to play songs
        self.fade_in = fade_in
        self.fade_out = fade_out
        self.interval_res = interval_res

        self.send_notifications = send_notifications

        # load the beat-changer
        beat_changer.configure_tracks(music_manager)
        self.beat_changer = beat_changer
        self.music_manager = music_manager

    def play_song(self, song, position=None):
        """
        Given a song and position, begins playback of the song,
        fading out the last played song if necassary

        :param song: filename of the song to be played
        :param position: position (in seconds) of the song at which to play
        """
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

    def change_music(self):
        # look at beats queue and return a song or none
        return self.beat_changer.change_music(self.internal_times, self.internal_counts)

    def notify_event(self, event):
        # passed an event to indicate quality of last choice
        self.beat_changer.notify_event(event)

    def run(self):

        while True:

            # retrieve the next entry
            next_item = self.beat_queue.get()

            # we'll expect 3 types of things from the beat queue
            # events if the user presses a keybinding
            # or a result
            if not isinstance(next_item, tuple):
                self.notify_event(next_item)
            else:
                (count, time) = next_item

                self.internal_times.append(time)
                self.internal_counts.append(count)

                if len(self.internal_times) > self.window_size:
                    del self.internal_times[0]
                    del self.internal_counts[0]

                    # once the window has filled up, we are safe to
                    # try changing the music
                    next_music = self.change_music()

                    # if the beat changer requests a music change
                    if next_music:
                        song, position = next_music
                        self.play_song(song, position)

                        if self.send_notifications:
                            send_notification('Playing {}'.format(song))

                        # reset the window
                        self.internal_times = []
                        self.internal_counts = []
                    elif self.send_notifications:
                        send_notification('Continuing Playback of Last Song')
