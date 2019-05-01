import random

import numpy as np
from beat_changer import BaseBeatChanger



BASE_HIGH_RATIO = 1.56
BASE_MID_RATIO = 0.96


class RatioBeatChanger(BaseBeatChanger):

    def configure_parameters(self, beat_window_size, window_size):
        self.beat_window_size = beat_window_size
        self.window_size = window_size

    def __init__(self):
        self.low_tracks = []
        self.high_tracks = []
        self.medium_tracks = []

        self.last_choice = None
        self.last_selected = None

    def play_initial(self):
        value = random.choice(self.low_tracks)
        return value[0]['song'], value[0]['start']

    def change_music(self, times, counts):
        count_mean = np.array(counts).mean()

        choice = None

        if count_mean < 2.0:
            choice = 'low'
        else:
            low, mid, high = 0, 0, 0

            for time, count in zip(times, counts):
                if count > count_mean * BASE_HIGH_RATIO:
                    high += 1
                elif count > count_mean * BASE_MID_RATIO:
                    mid += 1
                else:
                    low += 1

            if high > mid and high > low:
                choice = 'high'
            elif mid > low:
                choice = 'mid'
            else:
                choice = 'low'

        print('next music choice is {} from {}'.format(choice, self.last_choice))
        if choice != self.last_choice:
            self.last_choice = choice

            list = None
            if choice == 'high':
                list = self.high_tracks
            elif choice == 'mid':
                list = self.medium_tracks
            else:
                list = self.low_tracks

            counter = {}
            for (song, score) in list:
                counter.setdefault(song, 0)
                counter[song] += 1

            total_score = sum(i[1]/counter[i[0]] for i in list)
            choice = total_score * np.random.uniform(0, 1)

            index = 0
            partial_choice = 0
            while index < len(list) - 1 and partial_choice < choice:
                partial_choice += list[index][1] / counter[list[index][0]]
                index += 1
            index = min(max(0, index), len(list) - 1)

            self.last_selected = list[index]

            return self.last_selected[0]['song'], self.last_selected[0]['start']
        else:
            # if the last choice was the same as the current, return nothing
            return None

    def notify_event(self, event):

        if self.last_selected is not None:
            if event == 'good':
                self.last_selected[1] = max(min(0.0, self.last_selected[1] + 0.1), 3.0)
            else:
                self.last_selected[1] = max(min(0.0, self.last_selected[1] - 0.1), 3.0)

    def configure_tracks(self, music_manager):
        self.medium_tracks = [(i, 1.0) for i in music_manager.base_snippets]
        self.low_tracks = [(i, 1.0) for i in music_manager.slow_snippets]
        self.high_tracks = [(i, 1.0) for i in music_manager.fast_snippets]
