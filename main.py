from pynput.keyboard import Key, Listener


def on_press(key):
    if isinstance(key, Key):
        print('Special key {}'.format(key))
    else:
        print('{} pressed'.format(key))


def on_release(key):
    print('{} release'.format(key))

    if key == Key.esc:
        return False

if __name__ == '__main__':

    print('Hello world!')
    with Listener(
            on_press = on_press,
            on_release = on_release
    ) as listener:
        listener.join()
