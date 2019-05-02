from abc import ABC, abstractmethod

class BaseBeatChanger(ABC):

    @abstractmethod
    def configure_parameters(self, beat_window_size, window_size):
        """
        Configures the beat changer with the number of samples used to
        form the beat window, and the number of beats in a given window
        """
        pass

    @abstractmethod
    def configure_tracks(self, music_manager):
        """
        Initialises the beat changer's internal song list with the songs from a
        given music manager
        """
        pass

    @abstractmethod
    def change_music(self, times, counts, repeated=False):
        """
        Given a list of times and corresponding beat counts, determines
        whether a new song should be scheduled.

        Returns None if no new song to schedule, else returns a tuple
        with the song filename and offset in seconds into the song to
        start playback
        """
        pass

    @abstractmethod
    def notify_event(self, event):
        """
        Notify beat changer of other miscellaneous events such as the user's
        approval of the song choice.
        """
        pass

    @abstractmethod
    def play_initial(self):
        """
        Play an initial song to kick things off.

        Returns a song filename and offset in seconds to start.
        """
        pass


