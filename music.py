from scipy.io import wavfile
import matplotlib.pyplot as plt
import numpy as np
import scipy.fftpack
import sounddevice as sd
from collections import deque
import math
import time

class FrequencySelectedEnergyDetector:

    def __init__(
            self,
            block_size = 1000,
            threshold = None,
            window_size = 40,
            frequency_bands = 32,
            plot_waveform=True
    ):
        """
        Class implementing the frequency selection based energy technique for
        detecting beats in audio

        :param block_size: the number of samples which constitute a block. This
                        represents the maximum resolution at which beats may
                        be detected. A smaller value allows for detecting
                        faster beats, but also increases the chance of spurious
                        results.
        :param threshold: if specified, represents the amplitude that a sound wave
                        must exceed to be considered a beat.

        :param window_size: the size of the windows of past entries to be used.

        """
        self.block_size = block_size
        self.threshold = threshold
        self.window_size = window_size
        self.frequency_bands = frequency_bands
        self.plot_waveform = plot_waveform



    def transform(self, data):
        if data.shape[1] == 2:
            data = data[:,0] + 1j * data[:,1]

        n_blocks = data.shape[0] // self.block_size
        band_energy_history = [deque() for i in range(self.frequency_bands)]

        fft_data = scipy.fftpack.fft(data)


        def get_block_at_index(block_index):
            lower_bound = min(self.block_size * block_index, data.shape[0])
            upper_bound = min(self.block_size * block_index + self.block_size, data.shape[0])

            return data[lower_bound:upper_bound]

        def calculate_block_energy(block):
            energy_block = np.absolute(scipy.fftpack.fft(block))

            band_energy = [
                band.mean()
                for band in
                np.array_split(energy_block, self.frequency_bands)
            ]

            return band_energy

        def record_block_energy(band_energy):
            for band_hist, energy in zip(
                    band_energy_history,
                    band_energy
            ):
                band_hist.append(energy)

                if len(band_hist) > self.window_size:
                    band_hist.popleft()

        def is_beat(block_band_energy, thresholds):
            return any(
                 block_energy > np.mean(band) * threshold
                for band, block_energy, threshold in zip(band_energy_history, block_band_energy, thresholds)
            )


        def get_window_variance():
            return np.array([np.var(band) for band in band_energy_history])

        results = []

        threshold_values = []
        energy_values = []

        for block_index in range(n_blocks):

            if self.threshold is None:
                threshold = list((-0.00000000000015 * get_window_variance() + 1.6142857).ravel())
            else:
                threshold = [self.threshold] * len(band_energy_history)

            block = get_block_at_index(block_index)
            energy = calculate_block_energy(block)


            if self.plot_waveform:
                energy_values.append(energy)

                thresholds = [np.mean(band) * thres for band, thres in zip(band_energy_history, threshold)]
                threshold_values.append(thresholds)

            if is_beat(energy, threshold):
                results.append(1)
            else:
                results.append(0)

            record_block_energy(energy)


        if self.plot_waveform:
            fig,ax = plt.subplots(figsize=(10,10))
            ax.grid(True)

            energy_values = np.array(energy_values)
            threshold_values = np.array(threshold_values)

            for i in range(self.frequency_bands):
                fig, ax = plt.subplots()
                ax.set_title('Frequency Plot for Frequency Band {}'.format(i))
                ax.plot(np.arange(0, energy_values.shape[0]), energy_values[:,i], label='Energy for Band {}'.format(i))
                ax.plot(np.arange(0, threshold_values.shape[0]), threshold_values[:,i], label='Threshold for Band {}'.format(i))
                ax.legend()

            plt.show()


            for i in range(self.frequency_bands):
                ax.plot(np.arange(0, energy_values.shape[0]), energy_values[:,i], label='Energy for Band {}'.format(i))
            ax.legend()
            plt.show()
        return np.array(results)





class SoundEnergyDetector:

    def __init__(
            self,
            block_size = 1000,
            threshold = 250,
            window_size = 40,
            plot_waveform=False,
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
        self.plot_waveform = plot_waveform


    def transform(self, data):

        n_blocks = data.shape[0] // self.block_size
        block_window = deque()

        def get_window_average():
            current_average = np.array(block_window).mean()
            return current_average

        def get_window_variance():
            current_variance = np.array(block_window).var()
            return current_variance



        def get_block_at_index(block_index):
            lower_bound = min(self.block_size * block_index, data.shape[0])
            upper_bound = min(self.block_size  * block_index + self.block_size, data.shape[0])

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
                threshold = -0.000000000015 * get_window_variance() + 0.3142857
            else:
                threshold = self.threshold

            average = get_window_average()
            block = get_block_at_index(block_index)
            energy = calculate_block_energy(block)

            if self.plot_waveform:
                threshold_values.append(threshold)
                average_values.append(average)
                energy_values.append(energy)
                edge_values.append(abs(threshold * average))
                lower_edge_values.append(-abs(threshold * average))

            if abs(energy) > abs(average * threshold):
                results.append(1)
            else:
                results.append(0)

            append_block_energy(energy)


        if self.plot_waveform:
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


def beats_per_interval(raw, block_size, rate, interval):
    sample_time = 1/rate
    block_time = block_size * sample_time

    blocks_per_interval = max(int(math.ceil(interval/block_time)),1)

    columns = blocks_per_interval
    rows = max(int(math.ceil(raw.size / columns)),1)

    raw_padded = np.resize(raw, rows*columns)
    return np.reshape(np.sum(np.reshape(raw_padded, (rows,columns)), axis=1), (-1,))


filename = "./music/sample_2.wav"
rate, data = wavfile.read(filename)



# MAX_SAMPLE = 200000
# data = data[:MAX_SAMPLE,:]

print('Running Sound Energy Detector')
start =time.clock()
result_b = SoundEnergyDetector(plot_waveform=False).transform(data)
end =time.clock()
print('Ran in {}'.format(end - start))
print('Running Frequency Energy Detector')
start =time.clock()
result = FrequencySelectedEnergyDetector(plot_waveform=False).transform(data)
end =time.clock()
print('Ran in {}'.format(end - start))


# plt.plot(np.arange(0, len(result)), result)
# plt.plot(np.arange(0, len(result_b)), result_b)
# plt.show()

count_size = 5
bpm = beats_per_interval(result, 1000, rate, count_size)
bpm_b = beats_per_interval(result_b, 1000, rate, count_size)
plt.plot(np.arange(0, len(data)) / rate , data[:,0]//1000)
plt.plot(np.arange(0, len(bpm)) * count_size, bpm)
plt.plot(np.arange(0, len(bpm_b)) * count_size, bpm_b)
plt.show()

