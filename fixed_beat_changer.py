import random

import numpy as np
from beat_changer import BaseBeatChanger


# Represents the maximum number of beat windows for which the same song can be played
MAX_REPEAT_COUNT = 3
BASE_HIGH = 50
BASE_MID = 40


class FixedBeatChanger(BaseBeatChanger):

    def configure_parameters(self, beat_window_size, window_size):
        self.beat_window_size = beat_window_size
        self.window_size = window_size

    def __init__(self):
        self.low_tracks = []
        self.high_tracks = []
        self.medium_tracks = []

        self.last_choice = None
        self.last_selected = None
        self.last_choice_count = 0

    def play_initial(self):
        value = random.choice(self.low_tracks)
        return value[0]['song'], value[0]['start']

    def change_music(self, times, counts):
        count_mean = np.array(counts).mean()

        choice = None
        low, mid, high = 0, 0, 0

        if count_mean < 2.0:
            choice = 'low'
        else:

            for time, count in zip(times, counts):
                if count > BASE_HIGH:
                    high += 1
                elif count > BASE_MID:
                    mid += 1
                else:
                    low += 1

            if high > mid and high > low:
                choice = 'high'
            elif mid > low:
                choice = 'mid'
            else:
                choice = 'low'

        print(
            'next music choice is {} from {} (high: {}, mid: {}, low: {})'.format(choice, self.last_choice, high, mid, low)
        )
        if choice != self.last_choice and self.last_choice_count > MAX_REPEAT_COUNT:
            self.last_choice = choice
            self.last_choice_count = 0

            values = None
            if choice == 'high':
                values = self.high_tracks
            elif choice == 'mid':
                values = self.medium_tracks
            else:
                values = self.low_tracks

            # OLD SELECTION CODE - unfair allocation
            # total_score = sum(i[1] for i in values)
            # choice = total_score * np.random.uniform(0, 1)

            # index = 0
            # partial_choice = 0
            # while index < len(values) - 1 and partial_choice < choice:
            #     partial_choice += values[index][1]
            #     index += 1
            # index = max(min(0, index), len(values) - 1)


            songs = list(set(song['song'] for (song, pos) in values))
            choice = min(max(int(len(songs) * np.random.uniform(0, 1)), 0), len(songs) - 1)
            song = songs[choice]

            snippets = [snippet for snippet in values if snippet[0]['song'] == song]
            total_score = sum(i[1] for i in snippets)
            choice = total_score * np.random.uniform(0,1)

            index = 0
            partial_choice = 0
            while index < len(snippets) - 1 and partial_choice < choice:
                partial_choice += snippets[index][1]
                index += 1

            index = min(max(0, index), len(snippets) - 1)
            self.last_selected = snippets[index]

            return self.last_selected[0]['song'], self.last_selected[0]['start']
        else:
            self.last_choice_count += 1
            # if the last choice was the same as the current, return nothing
            return None

    def notify_event(self, event):

        if self.last_selected is not None:
            if event == 'good':
                self.last_selected[1] = min(max(0.0, self.last_selected[1] + 0.1), 3.0)
            else:
                self.last_selected[1] = min(max(0.0, self.last_selected[1] - 0.1), 3.0)

    def configure_tracks(self, music_manager):
        self.medium_tracks = [(i, 1.0) for i in music_manager.base_snippets]
        self.low_tracks = [(i, 1.0) for i in music_manager.slow_snippets]
        self.high_tracks = [(i, 1.0) for i in music_manager.fast_snippets]
