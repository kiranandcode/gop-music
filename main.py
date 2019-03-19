import numpy as np
import matplotlib.pyplot as plt
import scipy.fftpack

from pynput.keyboard import Key, Listener
import time

start_time = time.time()
last_reference_time = time.time()
REFERENCE_WINDOW_TIME = 0.3
current_count = 0
inputs_log = []

def on_press(key):
    """
    Called whenever a key is pressed.
    """
    global last_reference_time
    global current_count
    global inputs_log

    if isinstance(key, Key):
        print('Special key {}'.format(key))
        Key.alt
    else:
        current_time = time.time()

        print('Time between keyboard inputs: ', current_time - last_reference_time)

        if current_time - last_reference_time > REFERENCE_WINDOW_TIME:
            inputs_log.append((last_reference_time, current_count))

            current_count = 1
            last_reference_time = current_time
        else:
            current_count += 1


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


    inputs_log = np.array(inputs_log)
    plt.plot(inputs_log[:,0], inputs_log[:,1])
    plt.show()
    yf = scipy.fftpack.fft(inputs_log[:,1])
    xf = scipy.fftpack.fftfreq(yf.shape[0], REFERENCE_WINDOW_TIME)
    plt.plot(xf, yf)
    plt.show()


