import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from simulator import HydroStruct, SubmStruct, gen_sign_source, calc_paths, gen_sign_hydro
from processor import SignalProcessor
import os

def run_sensitivity_test():
    # --- Konfiguracja bazowa ---
    fs_khz = 100.0
    fs_hz = int(fs_khz * 1000)
    vs = 1500.0
    
    # Geometria (H1 i H2)
    h_cfg = HydroStruct(
        S1=np.array([120.0, 80.0, -20.0]), # Zrodlo w konkretnym miejscu
        H1=np.array([0, 150, -4.0]), 
        H2=np.array([50, 0, -4.0]),
        H3=np.array([300, 50, -4.0]), H4=np.array([50, 100, -4.0]),
        Bs=-45.0, AC=np.array([0.9, 0.9]), Vs=vs, TL=0.5
    )

    # Teoretyczny TDOA (Ground Truth) miedzy H2 a H1
    dist1 = np.linalg.norm(h_cfg.S1 - h_cfg.H1)
    dist2 = np.linalg.norm(h_cfg.S1 - h_cfg.H2)
    theoretical_tdoa = (dist2 - dist1) / vs

    # --- Parametry testu degradacji ---
    snr_values = np.arange(-5, 26, 2)  # SNR od -5dB do 25dB co 2dB
    iterations = 20                   # Ile razy powtarzamy dla kazdego SNR (statystyka)
    results = []

    print(f"Rozpoczynam analize wrazliwosci (RMSE vs SNR)... Teoretyczny TDOA: {theoretical_tdoa*1000:.4f} ms")

    proc = SignalProcessor(fs_hz)

    for snr in snr_values:
        errors = []
        for i in range(iterations):
            # Konfiguracja sygnalu dla danego SNR
            s_cfg = SubmStruct(
                TF=np.array([1.0, 1.5, 2.0]), 
                TA=np.array([0.1, 0.1, 0.1]), 
                AM=snr, 
                Fs=fs_khz, Tp=0.2, 
                RD=np.array([50, 0.5]) # Sta³a liczba zak³óceñ impulsowych
            )

            # Symulacja
            signS = gen_sign_source(s_cfg)
            signH = gen_sign_hydro(signS, h_cfg, calc_paths(h_cfg), fs_hz)

            # Estymacja
            try:
                delay_est, _, _ = proc.gcc_phat(signH[1], signH[0])
                error = abs(delay_est - theoretical_tdoa)
                errors.append(error)
            except:
                continue
        
        # Obliczanie RMSE (Root Mean Square Error) w milisekundach
        rmse = np.sqrt(np.mean(np.square(errors))) * 1000 
        results.append({"SNR": snr, "RMSE_ms": rmse})
        print(f" SNR: {snr:2} dB | RMSE: {rmse:.5f} ms")

    # --- Zapis i Wizualizacja ---
    df = pd.DataFrame(results)
    if not os.path.exists('results'): os.makedirs('results')
    df.to_csv('results/degradation_report.csv', index=False)

    plt.figure(figsize=(10, 6))
    plt.plot(df['SNR'], df['RMSE_ms'], 'o-', color='lime', linewidth=2, label='GCC-PHAT')
    plt.axhline(y=(1/fs_hz)*1000, color='red', linestyle='--', label='Rozdzielczosc probkowania (1/Fs)')
    plt.yscale('log') # Skala logarytmiczna dla b³êdu
    plt.grid(True, which="both", ls="-", alpha=0.5)
    plt.title("Analiza wrazliwosci algorytmu: RMSE vs SNR", fontsize=14)
    plt.ylabel("Blad RMSE [ms] (Skala Log)")
    plt.ylabel("Blad RMSE [ms] (Skala Log)")
    plt.legend()
    plt.savefig('results/rmse_degradation.png')
    plt.show()

if __name__ == "__main__":
    run_sensitivity_test()