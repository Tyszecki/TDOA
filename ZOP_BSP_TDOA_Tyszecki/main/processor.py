import numpy as np

class SignalProcessor:
    """Implementacja algorytmu GCC-PHAT (Knapp & Carter)."""
    
    def __init__(self, fs):
        self.fs = fs

    def gcc_phat(self, sig, refsig):
        """Wyznacza TDOA z wykorzystaniem normalizacji PHAT."""
        n = sig.shape[0] + refsig.shape[0]
        n_fft = 2**int(np.ceil(np.log2(n)))
        
        SIG = np.fft.rfft(sig, n=n_fft)
        REFSIG = np.fft.rfft(refsig, n=n_fft)
        
        R = SIG * np.conj(REFSIG)
        phi = R / (np.abs(R) + 1e-15) # Waga PHAT
        
        cc = np.fft.irfft(phi, n=n_fft)
        cc = np.concatenate((cc[-n_fft//2:], cc[:n_fft//2]))
        
        max_idx = np.argmax(np.abs(cc))
        shift = n_fft // 2
        delay = (max_idx - shift) / self.fs
        
        return delay, cc, np.arange(-shift, n_fft-shift) / self.fs