from scipy.io import wavfile
import matplotlib.pyplot as plt
import numpy as np
import scipy.fftpack

filename = "./music/sample.wav"

rate, data = wavfile.read(filename)


MAX_SAMPLE = 200_000
data = data[:MAX_SAMPLE,:]

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


# normalise the data
data = (data / 2 ** 16) * 2 - 1
fig, ax = plt.subplots(figsize=(10,10))
ax.plot(np.linspace(0, MAX_SAMPLE * rate, MAX_SAMPLE), data[:MAX_SAMPLE,0])


fig, ax = plt.subplots(figsize=(10,10))
yf = scipy.fftpack.fft(data[:MAX_SAMPLE,0])
xf = scipy.fftpack.fftfreq(yf.shape[0], MAX_SAMPLE * rate)
ax.plot(xf, yf)
plt.show()
