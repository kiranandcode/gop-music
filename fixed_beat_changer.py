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

    def change_music(self, times, counts, repeated=False):
        count_mean = np.array(counts).mean()

        choice = None
        low, mid, high = 0, 0, 0

        if count_mean < 2.0:
            choice = 'low'
        else:

            multiplier = 1
            for time, count in zip(times, counts):
                if count > BASE_HIGH:
                    high +=  multiplier
                elif count > BASE_MID:
                    mid += multiplier
                else:
                    low += multiplier
                multiplier *= 1.1

            if high > mid and high > low:
                choice = 'high'
            elif mid > low:
                choice = 'mid'
            else:
                choice = 'low'

        print(
            'next music choice is {} from {} (high: {}, mid: {}, low: {})'.format(choice, self.last_choice, high, mid, low)
        )

        if repeated:
            print('INFO: Song was repeated')
        print('choice{} != self.last_choice{} or self.last_choice_count{} >= MAX_REPEAT_COUNT{} or repeated{}  == {}'.format(choice, self.last_choice, self.last_choice_count, MAX_REPEAT_COUNT, repeated, choice != self.last_choice or self.last_choice_count >= MAX_REPEAT_COUNT or repeated))
        if choice != self.last_choice or self.last_choice_count >= MAX_REPEAT_COUNT or repeated:
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
            song_sums = [sum(snippet[1][0] for snippet in values if snippet[0]['song'] == song)/len([snippet[1][0] for snippet in values if snippet[0]['song'] == song]) for song in songs]

            choice = sum(song_sums) * np.random.uniform(0,1)

            index = 0
            partial_choice = 0
            for i, value in enumerate(song_sums):
                partial_choice += value
                if partial_choice >= choice:
                    index = i
                    break

            # choice = min(max(int(len(songs) * np.random.uniform(0, 1)), 0), len(songs) - 1)
            choice = min(max(int(index), 0), len(songs) - 1)
            song = songs[choice]
            print('song priority sum: ', song_sums, song)

            snippets = [snippet for snippet in values if snippet[0]['song'] == song]
            total_score = sum(i[1][0] for i in snippets)
            choice = total_score * np.random.uniform(0,1)

            index = 0
            partial_choice = 0
            while index < len(snippets) - 1 and partial_choice < choice:
                partial_choice += snippets[index][1][0]
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
                self.last_selected[1][0] = min(max(0.0, self.last_selected[1][0] + 1.0), 40.0)
            else:
                self.last_selected[1][0] = min(max(0.0, self.last_selected[1][0] - 1.0), 40.0)

    def configure_tracks(self, music_manager):
        self.medium_tracks = [(i, [1.0]) for i in music_manager.base_snippets]
        self.low_tracks = [(i, [1.0]) for i in music_manager.slow_snippets]
        self.high_tracks = [(i, [1.0]) for i in music_manager.fast_snippets]
