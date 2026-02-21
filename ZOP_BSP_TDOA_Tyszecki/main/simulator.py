import numpy as np
from dataclasses import dataclass

# =================================================================
# STRUKTURY DANYCH (Zgodnie z formatka projektu)
# =================================================================

@dataclass
class HydroStruct:
    S1: np.ndarray  
    H1: np.ndarray  
    H2: np.ndarray
    H3: np.ndarray
    H4: np.ndarray
    Bs: float       
    AC: np.ndarray  
    Vs: float       
    TL: float       

@dataclass
class SubmStruct:
    TF: np.ndarray  
    TA: np.ndarray  
    AM: float       
    Fs: float       
    Tp: float       
    RD: np.ndarray  

# =================================================================
# FUNKCJE SYMULACYJNE
# =================================================================

def db2mag(db):
    return 10 ** (db / 20.0)

def gen_sign_source(Subm):
    fs = Subm.Fs * 1000.0
    f = Subm.TF * 1000.0
    t = np.arange(0, Subm.Tp, 1.0 / fs)
    sign = np.zeros_like(t)
    
    # Sygnał tonalny
    for i in range(len(f)):
        sign += Subm.TA[i] * np.sin(2 * np.pi * f[i] * t)
    
    rng = np.random.default_rng(seed=0)
    
    # 1. Szum szerokopasmowy (AM)
    noise = rng.normal(0, np.std(sign) / db2mag(Subm.AM), size=sign.shape)
    sign += noise
    
    # 2. Zakłócenia impulsowe (RD) - NOWOŚĆ
    # RD[0] to liczba impulsów, RD[1] to ich max amplituda
    num_impulses = int(Subm.RD[0])
    if num_impulses > 0:
        indices = rng.integers(0, len(sign), size=num_impulses)
        amplitudes = rng.uniform(0, Subm.RD[1], size=num_impulses)
        sign[indices] += amplitudes * np.max(np.abs(sign))
        
    return sign

def calc_paths(Hydro):
    S1 = np.array(Hydro.S1, dtype=float)
    H = np.array([Hydro.H1, Hydro.H2, Hydro.H3, Hydro.H4], dtype=float)
    d = np.zeros(4)
    for i in range(4):
        d[i] = np.linalg.norm(S1 - H[i])
    return np.column_stack((d, d, d))

def gen_sign_hydro(signS, Hydro, propPaths, fs):
    signH = []
    v = Hydro.Vs
    dt = np.round(propPaths[:, 0] / v * fs).astype(int)
    for i in range(4):
        delay = np.zeros(dt[i])
        sig_delayed = np.concatenate((delay, signS))
        signH.append(sig_delayed)
    
    max_len = max(len(s) for s in signH)
    final_signs = []
    for s in signH:
        padded = np.pad(s, (0, max_len - len(s)), mode='constant')
        final_signs.append(padded)
    return final_signs
