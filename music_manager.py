# base library imports
from argparse import ArgumentParser
from pathlib import Path
import __main__ as main
import json
import os
import sys

# core-numerical/standard imports
import pandas as pd
import soundfile

# cosmetic imports
from tqdm import tqdm

# library imports
from beat_detection import *

SCRIPT_NAME = __file__
DEBUG = bool(os.environ.get('TYPE_MUSIC_DEBUG', False))

if not __file__:
    SCRIPT_NAME = str(Path(main.__file__).resolve())
else:
    SCRIPT_NAME = str(Path(__file__).resolve())

def custom_error_handler(type, value, traceback):
    # get the name of the script the exception originated from
    file_name = traceback.tb_frame.f_code.co_filename

    # if from this script, then quit
    if SCRIPT_NAME == file_name or not DEBUG:
        print(
            'INFO: Script aborted unexpectedly, encountered exception: {}'.format(value),
            file=sys.stderr,
        )
        return
    else:
        # otherwise, handle as normal (i.e print stacktrace)
        sys.__excepthook__(type, value, traceback)
        return

sys.excepthook = custom_error_handler


VERSION = 1
FROM_UNKNOWN = 'unk'  # 0
FROM_LOW = 'low'  # 1
FROM_MED = 'med'  # 2
FROM_HIGH = 'high'  # 3
# OS environment variables
BLOCK_SIZE = int(os.environ.get('TYPE_MUSIC_BLOCK_SIZE', 1000))
BEAT_INTERVAL_SIZE = int(os.environ.get('TYPE_MUSIC_BEAT_INTERVAL_SIZE', 2))
LOW_BASE_BEAT_THRESHOLD = int(os.environ.get('TYPE_MUSIC_LOW_BASE_BEAT_THRESHOLD', 10))
BASE_HIGH_BEAT_THRESHOLD = int(os.environ.get('TYPE_MUSIC_BASE_HIGH_BEAT_THRESHOLD', 20))
SAVE_DIR = Path(os.environ.get('TYPE_MUSIC_SAVE_DIR', '~/.typemusic/'))

# make sure the directory exists
SAVE_DIR.mkdir(parents=True,exist_ok=True)


def open_saved_mm(filename):
    file_path = SAVE_DIR / (filename + ".json")

    mm = MusicManager()

    if file_path.exists():
        mm.load_from_disk(str(file_path))

    return mm

def save_new_mm(filename, mm):
    file_path = SAVE_DIR / (filename + ".json")


    mm.save_to_disk(str(file_path))




class MusicManager:

    def __init__(self,path=None):
        if path:
            self.load_from_disk(path)
        else:
            self.version = VERSION

            self.block_size = BLOCK_SIZE
            self.beat_interval_size = BEAT_INTERVAL_SIZE
            self.low_base_beat_threshold = LOW_BASE_BEAT_THRESHOLD
            self.base_high_beat_threshold = BASE_HIGH_BEAT_THRESHOLD

            self.songs = []
            self.slow_snippets = []
            self.fast_snippets = []
            self.base_snippets = []

    def resample_songs(self, verbose=False):
        # take a copy of the songs list
        songs = self.songs

        # clear all the variables
        self.songs = []
        self.slow_snippets = []
        self.fast_snippets = []
        self.base_snippets = []


        slist = songs
        if verbose:
            slist = tqdm(songs)

        # re add the songs
        for song in slist:
            self.add_song(song)


    def remove_song(self, song):
        self.songs.remove(song)

        self.slow_snippets = [
            entry for entry in self.slow_snippets if entry['song'] != song
        ]

        self.base_snippets = [
            entry for entry in self.base_snippets if entry['song'] != song
        ]

        self.fast_snippets = [
            entry for entry in self.fast_snippets if entry['song'] != song
        ]


    def get_snippets(self, song, count=False):
        snippets, fast, base, slow = [], [], [], []
        if count:
            snippets, fast, base, slow = 0, 0, 0, 0

        for entry in self.slow_snippets:
            if entry['song'] == song:
                if count:
                    snippets += 1
                    slow += 1
                else:
                    snippets.append(entry)
                    slow.append(entry)

        for entry in self.base_snippets:
            if entry['song'] == song:
                if count:
                    snippets += 1
                    base += 1
                else:
                    snippets.append(entry)
                    base.append(entry)

        for entry in self.fast_snippets:
            if entry['song'] == song:
                if count:
                    snippets += 1
                    fast += 1
                else:
                    snippets.append(entry)
                    fast.append(entry)

        return snippets, fast, base, slow


    def add_song(self, song, verbose=False):
        if song in self.songs:
            if verbose:
                print('INFO: Song {} already exists in library, skipping.'.format(song))
            return

        self.songs.append(song)

        data, rate = soundfile.read(song)
        raw_beats = FrequencySelectedEnergyDetector(
            block_size=self.block_size
        ).transform(data)
        beats = beats_per_interval(raw_beats, self.block_size, rate, self.beat_interval_size)

        # if empty track, exit
        if len(beats) == 0:
            return

        # calculate beats
        # retains the beat of the previous section
        prev_section_beat = None

        # retains the beat value of the current section
        current_beat = beats[0]
        current_start = 0
        current_is_low = current_beat < self.low_base_beat_threshold
        current_is_med = current_beat < self.base_high_beat_threshold

        i = 1

        # loop through the beats
        while i < len(beats):
            # get the beat
            beat = beats[i]

            # calculate its class
            is_low = beat < self.low_base_beat_threshold
            is_med = beat < self.base_high_beat_threshold

            # if the same value
            if (current_is_low == is_low) and (current_is_med == is_med):
                # do nothing, this entry passes
                i += 1
                continue
            else:
                # if not the same value, then this is the end of the current section.
                if current_is_low:
                    entry_list = self.slow_snippets
                elif current_is_med:
                    entry_list = self.base_snippets
                else:
                    entry_list = self.fast_snippets

                # calculate the beat level of the previous entry in the list
                entry_from = FROM_UNKNOWN
                if prev_section_beat is not None:
                    if prev_section_beat < self.low_base_beat_threshold:
                        entry_from = FROM_LOW
                    elif prev_section_beat < self.base_high_beat_threshold:
                        entry_from = FROM_MED
                    else:
                        entry_from = FROM_HIGH

                # append the data to the list
                entry_list.append({
                    'song': song,
                    'from': entry_from,
                    'start': (current_start * self.beat_interval_size),
                    'end': (i * self.beat_interval_size),
                })

                # update the variables
                prev_section_beat = beats[i - 1]
                current_beat = beat
                current_start = i
                current_is_low = current_beat < self.low_base_beat_threshold
                current_is_med = current_beat < self.base_high_beat_threshold

                i += 1


        # if we had more than one entry prior to ending
        if current_start + 1 != i:
            # Once loop is finished, add final section
            if current_is_low:
                entry_list = self.slow_snippets
            elif current_is_med:
                entry_list = self.base_snippets
            else:
                entry_list = self.fast_snippets

            # calculate the beat level of the previous entry in the list
            entry_from = FROM_UNKNOWN
            if prev_section_beat is not None:
                if prev_section_beat < self.low_base_beat_threshold:
                    entry_from = FROM_LOW
                elif prev_section_beat < self.base_high_beat_threshold:
                    entry_from = FROM_MED
                else:
                    entry_from = FROM_HIGH

            # append the data to the list
            entry_list.append({
                'song': song,
                'from': entry_from,
                'start': (current_start * self.beat_interval_size),
                'end': ((i - 1) * self.beat_interval_size),
            })


    def load_from_disk(self, path):
        with open(path, 'r') as raw_data:
            json_data = json.load(raw_data)

        if json_data['version'] != VERSION:
            raise ValueError('Incompatible old version of format. Check Gitlab wiki for possible conversions.')

        self.songs = json_data['songs']

        self.block_size = int(json_data['block_size'])
        self.beat_interval_size = int(json_data['beat_interval_size'])
        self.low_base_beat_threshold = int(json_data['low_base_beat_threshold'])
        self.base_high_beat_threshold = int(json_data['base_high_beat_threshold'])

        self.slow_snippets = json_data['slow_snippets']
        self.fast_snippets = json_data['fast_snippets']
        self.base_snippets = json_data['base_snippets']


    def save_to_disk(self, path):
        save_obj = {}

        save_obj['songs'] = self.songs
        save_obj['version'] = VERSION


        save_obj['block_size'] = self.block_size
        save_obj['beat_interval_size'] = self.beat_interval_size
        save_obj['low_base_beat_threshold'] = self.low_base_beat_threshold
        save_obj['base_high_beat_threshold'] = self.base_high_beat_threshold

        save_obj['slow_snippets'] = self.slow_snippets
        save_obj['fast_snippets'] = self.fast_snippets
        save_obj['base_snippets'] = self.base_snippets

        with open(path, 'w') as raw_file:
            json.dump(save_obj, raw_file)





if __name__ == '__main__':
    parser = ArgumentParser(
        description='Helper script to manage the internal music library used by Type Music.'
    )

    parser.add_argument(
        '-p', '--profile', metavar='PROFILE', default='default',
        help='Type Music can maintain multiple libraries of songs to use for its music source - use this to '
        'group songs by different moods,etc. Defaults to the default profile.'
    )

    parser.add_argument(
        '-s', '--silent', action='store_true',
        help='Whether to run in silent mode (useful for scripts).'
    )

    parser.add_argument(
        'action', metavar='ACTION', choices=['add-song', 'remove-song', 'list-songs', 'list-snippets']
    )

    args, songs = parser.parse_known_args()
    profile = args.profile
    verbose = not args.silent

    mm = open_saved_mm(profile)

    if args.action == 'add-song':
        if not songs:
            print('Error: Please provide songs to be loaded.', file=sys.stderr)
            exit(-1)

        slist = songs

        if verbose:
            slist = tqdm(slist)

        for song in slist:
            song = str(Path(song).resolve())
            mm.add_song(song, verbose=verbose)

        save_new_mm(profile, mm)

    elif args.action == 'remove-song':
        if not songs:
            print('Error: Please provide songs to be removed.', file=sys.stderr)
            exit(-1)

        slist = songs
        if verbose:
            slist = tqdm(slist)


        for song in slist:
            mm.remove_song(song)

        save_new_mm(profile, mm)

    elif args.action == 'list-songs':
        slist = mm.songs
        if songs:
            slist = songs

        print('Songs under profile: {}'.format(profile))
        print('Saved under: {}'.format(str(SAVE_DIR / profile)))
        print('\t[{:3}]:|{:30}|{:30}|{:30}|{:30}|{:30}'.format(
            "ind", "Song Name", "Snippets", "Fast", "Base", "Slow"
        ))
        for index, song in enumerate(slist):
            snippets, fast, base, slow = mm.get_snippets(song, count=True)
            print('\t[{:3}]:|{:30}|{:30}|{:30}|{:30}|{:30}'.format(index,song,snippets, fast, base, slow))

    elif args.action == 'list-snippets':
        slist = mm.songs

        if songs:
            slist = songs

        print('Songs under profile: {}'.format(profile))
        print('Saved under: {}'.format(str(SAVE_DIR / profile)))


        for song in slist:
            snippets, fast, base, slow = mm.get_snippets(song)

            print('Song: {}'.format(song))

            print('\t\t{:3}: {:10} - {:10}: {:10} {:10}'.format("Ind", "Start (s)", "end(s)", "Prev Pace", "Length"))
            for (name, sel_list) in [('Fast Snippets', fast), ('Base Snippets', base), ('Slow Snippets', slow)]:
                print('\t{}:'.format(name))
                for index, snippet in enumerate(sel_list):
                    start = snippet['start']
                    end = snippet['end']
                    from_id = snippet['from']

                    from_str = ''
                    if from_id == FROM_HIGH:
                        from_str = 'From High'
                    elif from_id == FROM_MED:
                        from_str = 'From Base'
                    elif from_id == FROM_LOW:
                        from_str = 'From Low'
                    length = end - start

                    print('\t\t{:3}: {:10} - {:10}: {:10} {:5}'.format(index, start, end, from_str, length, length))

