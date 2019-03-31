from argparse import ArgumentParser
from beat_changer import BasicBeatChanger
from music_manager import open_saved_mm
from music_player import BeatChangerWrapperPlayer

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

    beat_changer = BasicBeatChanger()

    player = BeatChangerWrapperPlayer(
        beat_changer, music_manager=music_manager,
        beat_window_size=10.0, min_change_time=120,
        exit_keys=['ctrl', 'e'],
        keys_events=[('good', ['ctrl', 'g']), ('bad', ['ctrl', 'b'])],
        send_notifications=True,
        plot_graph=True
    )

    player.run()
