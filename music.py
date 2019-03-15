from scipy.io import wavfile
import matplotlib.pyplot as plt
import numpy as np
import scipy.fftpack
import sounddevice as sd
from collections import deque



class SoundEnergyDetector:

    def __init__(
            self,
            block_size = 1000,
            threshold = None,
            window_size = 40
    ):
        """
        Class implementing the sound energy technique for detecting beats in audio

        :param block_size: the number of samples which constitute a block. This
                        represents the maximum resolution at which beats may
                        be detected. A smaller value allows for detecting
                        faster beats, but also increases the chance of spurious
                        results
        """
        self.block_size = block_size
        self.threshold = threshold
        self.window_size = window_size


    def transform(self, data):

        n_blocks = data.shape[0] // self.block_size + 1
        block_window = deque()

        def get_window_average():
            current_average = np.array(block_window).mean()
            return current_average

        def get_window_variance():
            current_variance = np.array(block_window).var()
            return current_variance



        def get_block_at_index(block_index):
            lower_bound = min(self.block_size * block_index, data.shape[0])
            upper_bound = min((self.block_size + 1) * block_index, data.shape[0])

            return data[lower_bound:upper_bound,:]

        def calculate_block_energy(block):
            if block.shape[1] == 2:
                return np.sum((block[:,0] ** 2) + (block[:,0] ** 2))
            else:
                return np.sum((block[:,0] ** 2))

        def append_block_energy(energy):
            block_window.append(energy)

            while len(block_window) > self.window_size:
                rem_energy = block_window.popleft()


        results = []

        threshold_values = []
        average_values = []
        energy_values = []
        edge_values = []
        lower_edge_values = []

        for block_index in range(n_blocks):
            if self.threshold is None:
                threshold = -0.0000000000015 * get_window_variance() + 0.5142857
            else:
                threshold = self.threshold

            average = get_window_average()
            block = get_block_at_index(block_index)
            energy = calculate_block_energy(block)

            threshold_values.append(threshold)
            average_values.append(average)
            energy_values.append(energy)
            edge_values.append(abs(threshold * average))
            lower_edge_values.append(-abs(threshold * average))

            if abs(energy) > abs(average * threshold):
                results.extend([1] * self.block_size)
            else:
                results.extend([0] * self.block_size)

            append_block_energy(energy)


        fig,ax = plt.subplots(figsize=(10,10))
        ax.grid(True)
        ax.plot(np.arange(0, len(threshold_values)), threshold_values, label='Threshold')
        ax.plot(np.arange(0, len(edge_values)), edge_values, label='Edge')
        ax.plot(np.arange(0, len(lower_edge_values)), lower_edge_values, label='Edge')
        ax.plot(np.arange(0, len(average_values)), average_values, label='Average')
        ax.plot(np.arange(0, len(energy_values)), energy_values, label='Energy')
        ax.legend()
        plt.show()
        return np.array(results)


filename = "./music/sample.wav"

rate, data = wavfile.read(filename)



MAX_SAMPLE = 200000
data = data[:MAX_SAMPLE,:]

result = SoundEnergyDetector().transform(data)

sd.play(data//100 + np.c_[result,result][:MAX_SAMPLE,:].astype(np.int16) * 2000, rate)




if data.shape[1] == 2:
    print('Bi-channel data')
    # average both channels
    data = np.sum(data, axis=1) / 2

samples = data.shape[0]

seconds = samples/rate
print('Length of data: {}s'.format(seconds))



time = np.arange(0, seconds,1/rate)[:MAX_SAMPLE]
fft_signal = scipy.fftpack.fft(data)
fft_side = fft_signal[range(samples//2)]
fft_freqs = scipy.fftpack.fftfreq(samples, 1/rate)
fft_freqs_side = fft_freqs[range(samples//2)]

print(time.shape, data.shape, fft_freqs.shape, fft_signal.shape, fft_side.shape)

plt.subplot(311)
plt.plot(time, data)
plt.xlabel('Time')
plt.ylabel('Amplitude')
plt.subplot(312)
plt.plot(fft_freqs, fft_signal)
plt.xlabel('Frequency (Hz)')
plt.ylabel('Count dbl-sided')
plt.subplot(313)
plt.plot(fft_freqs_side, abs(fft_side), "b")
plt.xlabel("Frequency (Hz)")
plt.ylabel('Count single-sided')
plt.show()

