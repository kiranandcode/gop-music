#!/usr/bin/python3
from argparse import ArgumentParser
from fixed_beat_changer import FixedBeatChanger
from music_manager import open_saved_mm
from music_player import BeatChangerWrapperPlayer

if __name__ == '__main__':
    parser = ArgumentParser(description='Gop-Music automatic music player')

    parser.add_argument(
        '-p', '--profile',
        metavar='PROFILE', default='default',
        help='Name of the profile to load'
    )

    args = parser.parse_args()
    profile = args.profile

    music_manager = open_saved_mm(profile)

    if not music_manager.songs:
        raise ValueError(
            "Profile {} has no songs - please run music_manager.py to add songs to that profile.".format(
                profile
            )
        )

    beat_changer = FixedBeatChanger()

    player = BeatChangerWrapperPlayer(
        beat_changer, music_manager=music_manager,
        beat_window_size=10.0, min_change_time=120,
        exit_keys=['ctrl', 'e'],
        keys_events=[('good', ['ctrl', 'g']), ('bad', ['ctrl', 'b'])],
        send_notifications=True,
        plot_graph=True
    )

    player.run()
