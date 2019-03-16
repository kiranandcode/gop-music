from scipy.io import wavfile
import matplotlib.pyplot as plt
import numpy as np
import scipy.fftpack
import sounddevice as sd
from collections import deque

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
                results.extend([1] * self.block_size)
            else:
                results.extend([0] * self.block_size)

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
                threshold = -0.0000000000015 * get_window_variance() + 0.5142857
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
                results.extend([1] * self.block_size)
            else:
                results.extend([0] * self.block_size)

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


filename = "./music/sample.wav"

rate, data = wavfile.read(filename)



MAX_SAMPLE = 200000
data = data[:MAX_SAMPLE,:]

result = FrequencySelectedEnergyDetector(plot_waveform=False).transform(data)
result_b = SoundEnergyDetector(plot_waveform=False).transform(data)



plt.plot(np.arange(0, len(result)), result)
plt.plot(np.arange(0, len(result_b)), result_b)
plt.show()

sd.play(data//30 + np.c_[result,result][:MAX_SAMPLE,:].astype(np.int16) * 5000, rate)
input('n song')
sd.play(data//30 + np.c_[result_b,result_b][:MAX_SAMPLE,:].astype(np.int16) * 5000, rate)
wavfile.write('output_a.wav', rate, data//30 + np.c_[result,result][:MAX_SAMPLE,:].astype(np.int16) * 5000)
wavfile.write('output_b.wav', rate, data//30 + np.c_[result_b,result_b][:MAX_SAMPLE,:].astype(np.int16) * 5000)

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

