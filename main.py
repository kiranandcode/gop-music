from abc import ABC, abstractmethod


class BaseBeatChanger(ABC):

    @abstractmethod
    def configure_tracks(self, music_manager):
        pass

    @abstractmethod
    def change_music(self, times, counts):
        pass

    @abstractmethod
    def notify_event(self, event):
        pass

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
