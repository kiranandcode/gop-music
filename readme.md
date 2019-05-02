# Gop-Music

Ever wanted to play music while working, but wanted more than just some plain background audio?

Ever felt that a static playlist could never capture the dynamism of your development process?

Well, friend, do I have the tool for you!

Gop-Music uses "algorithms and coding" to automatically play music suited your writing style.

Background music for coding, but done the right way.

## Screen Shots
![image]()


## Video
A video demonstration of gop-music in action can be found here: https://www.youtube.com/watch?v=OG7meAEAAaU


### WARNING
*In the interests of transparency, I should note that the functionality provided by Gop-music can only be achieved by tracking the frequency of key-presses, which, unfortunately, is a feature also used by many malicious applications. While Gop-Music doesn't log the exact keys you press, nor does it share any data with any devices, if you want to use Gop-music, it is strongly advised you read through the source code yourself.*



## Usage
I'm not sure how pipenv works, or if it works in this way, but I've been using pipenv to make my development 
environment, so maybe if you use pipenv shell it'll recreate the environment? If not, raise an issue, and I may 
fix it.
```
pipenv shell
```
Anyway, all subsequent commands assume that your python environment contains all the required packages.

### Loading Songs

Use the music_manager script to load songs to a profile (by default all profiles stored in `~/.typemusic/`)

    usage: music_manager.py [-h] [-p PROFILE] [-s] [-v] [--force-mood MOOD]
                            [--min-length MIN-LENGTH]
                            ACTION

    Helper script to manage the internal music library used by gop-music.

    positional arguments:
    ACTION                The action to perform. Should be one of: add-song,
                            remove-song, list-songs, list-snippets, test-run

    optional arguments:
    -h, --help            show this help message and exit
    -p PROFILE, --profile PROFILE
                            Type Music can maintain multiple libraries of songs to
                            use for its music source - use this to group songs by
                            different moods,etc. Defaults to the default profile.
    -s, --silent          Whether to run in silent mode (useful for scripts).
    -v, --visualise-beats
                            Whether plot the beats produced by each song. -
                            Requires manual saving
    --force-mood MOOD, -f MOOD
                            The beat detection is a bit iffy, so sometimes you may
                            want to manually force a certain mood.
    --min-length MIN-LENGTH, -m MIN-LENGTH
                            Minimum length for a snippet. Snippet lengths aren't
                            used when playing, only for the detection process

The beat detection is currently a bit iffy, so I often just use `--force-mood` to manually define a categorisation for the track I want to add.

Once music has been loaded, launch the main program to start gop-music:

    usage: main.py [-h] [-p PROFILE]

    Gop-Music automatic music player

    optional arguments:
    -h, --help            show this help message and exit
    -p PROFILE, --profile PROFILE
                            Name of the profile to load. Defaults to
                            the default profile.


## Note
If you are viewing this from micro$oft github, then note that any updates are first pushed to *gitlab*, 
and then only maybe will be pushed to Micro$oft's github at some delayed later date.

It can be found on gitlab at: https://gitlab.com/gopiandcode/gop-music
