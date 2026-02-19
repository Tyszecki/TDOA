import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import spectrogram
from simulator import HydroStruct, SubmStruct, gen_sign_source, calc_paths, gen_sign_hydro
from processor import SignalProcessor

def get_input(prompt, current_val):
    """Pobiera dane od uzytkownika, wyswietlajac poprzednia wartosc."""
    user_input = input(f"{prompt} [{current_val}]: ").strip()
    if user_input == "":
        return current_val
    try:
        return float(user_input)
    except ValueError:
        print("Blad formatu. Zachowano poprzednia wartosc.")
        return current_val

def main():
    # Pamiec sesji - wartosci domyslne
    params = {
        "Vs": 1500.0,
        "S1_x": 50.0,
        "S1_y": 50.0,
        "S1_z": -20.0,
        "AM": 20.0,
        "TL": 0.5,
        "Fs": 100.0
    }

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("====================================================")
        print("   ZOP-BSP: ZAAWANSOWANY ANALIZATOR HYDROAKUSTYCZNY ")
        print("     Nacisnij ENTER, aby uzyc wartosci domyslnej    ")
        print("====================================================")

        # Pobieranie parametrow z pamiecia
        params["Vs"] = get_input("Predkosc dzwieku [m/s]", params["Vs"])
        params["S1_x"] = get_input("Pozycja zrodla X [m]", params["S1_x"])
        params["S1_y"] = get_input("Pozycja zrodla Y [m]", params["S1_y"])
        params["S1_z"] = get_input("Glebokosc zrodla Z [m]", params["S1_z"])
        params["AM"] = get_input("Wzmocnienie toru [dB]", params["AM"])
        params["Fs"] = get_input("Czestotliwosc probkowania [kHz]", params["Fs"])

        fs_hz = int(params["Fs"] * 1000)
        
        # Inicjalizacja struktur
        hydro_cfg = HydroStruct(
            S1=np.array([params["S1_x"], params["S1_y"], params["S1_z"]]),
            H1=np.array([0.0, 150.0, -4.0]), H2=np.array([50.0, 0.0, -4.0]),
            H3=np.array([300.0, 50.0, -4.0]), H4=np.array([50.0, 100.0, -4.0]),
            Bs=-45.0, AC=np.array([0.9, 0.9]), Vs=params["Vs"], TL=params["TL"]
        )

        subm_cfg = SubmStruct(
            TF=np.array([1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 18, 19, 20.0]),
            TA=np.array([0.1] * 11), AM=params["AM"], Fs=params["Fs"], Tp=0.2, RD=np.array([10, 0.005, 1, 30])
        )

        # 1. Symulacja
        print("\nTrwa generowanie danych i obliczenia...")
        signS = gen_sign_source(subm_cfg)
        paths = calc_paths(hydro_cfg)
        signH = gen_sign_hydro(signS, hydro_cfg, paths, fs_hz)
        processor = SignalProcessor(fs_hz)

        # 2. Generowanie Dashboardu
        plt.style.use('dark_background') # Profesjonalny, 'sonarowy' wyglad
        fig = plt.figure(figsize=(16, 9))
        fig.suptitle(f"DASHBOARD ANALITYCZNY TDOA (Vs={params['Vs']} m/s, Fs={params['Fs']} kHz)", fontsize=16, color='cyan')

        # Wykres 1: Geometria 3D
        ax1 = fig.add_subplot(221, projection='3d')
        ax1.scatter(hydro_cfg.S1[0], hydro_cfg.S1[1], hydro_cfg.S1[2], c='red', s=100, label='Zrodlo S1', edgecolors='white')
        h_pos = np.array([hydro_cfg.H1, hydro_cfg.H2, hydro_cfg.H3, hydro_cfg.H4])
        ax1.scatter(h_pos[:,0], h_pos[:,1], h_pos[:,2], c='lime', s=60, label='Hydrofony H1-H4')
        ax1.set_title("Geometria ukladu [m]")
        ax1.set_xlabel("X"); ax1.set_ylabel("Y"); ax1.set_zlabel("Z")
        ax1.legend()

        # Wykres 2: Porownanie sygnalow (Time Domain)
        ax2 = fig.add_subplot(222)
        t_plot = np.arange(len(signH[0])) / fs_hz * 1000
        ax2.plot(t_plot, signH[0], label='H1 (Ref)', color='yellow', alpha=0.7)
        ax2.plot(t_plot, signH[1], label='H2', color='cyan', alpha=0.7)
        ax2.set_xlim(30, 80) # Przyciecie do istotnego obszaru
        ax2.set_title("Sygnaly H1 vs H2 (Przesuniecie czasowe)")
        ax2.set_xlabel("Czas [ms]"); ax2.set_ylabel("Amplituda [V]")
        ax2.legend()
        ax2.grid(alpha=0.3)

        # Wykres 3: Spektrogram H1
        ax3 = fig.add_subplot(223)
        f_axis, tt_axis, Sxx = spectrogram(signH[0], fs_hz)
        im = ax3.pcolormesh(tt_axis*1000, f_axis/1000, 10 * np.log10(Sxx + 1e-15), shading='gouraud', cmap='viridis')
        ax3.set_title("Spektrogram sygnalu H1 (Analiza czestotliwosciowa)")
        ax3.set_ylabel("f [kHz]"); ax3.set_xlabel("t [ms]")
        plt.colorbar(im, ax=ax3, label="Moc [dB]")

        # Wykres 4: Wynik GCC-PHAT
        ax4 = fig.add_subplot(224)
        delay_est, cc, t_cc = processor.gcc_phat(signH[1], signH[0])
        ax4.plot(t_cc * 1000, cc, color='lime', linewidth=1.5)
        actual_tdoa = (np.linalg.norm(hydro_cfg.S1-hydro_cfg.H2) - np.linalg.norm(hydro_cfg.S1-hydro_cfg.H1))/hydro_cfg.Vs
        ax4.axvline(x=actual_tdoa*1000, color='red', linestyle='--', label='TDOA Real')
        ax4.set_title("Estymacja Opoznienia (GCC-PHAT)")
        ax4.set_xlabel("Opoznienie [ms]")
        ax4.set_xlim(actual_tdoa*1000 - 15, actual_tdoa*1000 + 15)
        ax4.legend()
        ax4.grid(alpha=0.3)

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        # Zapis i wyswietlenie
        if not os.path.exists('results'): os.makedirs('results')
        plt.savefig('results/tdoa_analysis_dashboard.png', dpi=120)
        
        # Wyswietlenie wynikow w konsoli
        print("\n" + "="*40)
        print(f" WYNIKI DLA Vs = {params['Vs']} m/s")
        print(f" Estymowane TDOA (H2-H1): {delay_est*1000:8.4f} ms")
        print(f" Rzeczywiste TDOA (H2-H1): {actual_tdoa*1000:8.4f} ms")
        print(f" BLAD: {abs(actual_tdoa - delay_est)*1000:10.6f} ms")
        print("="*40)
        print("\nWykres zapisano w: results/tdoa_analysis_dashboard.png")
        
        plt.show() # To zablokuje petle do czasu zamkniecia okna wykresu

        cont = input("\nCzy chcesz sprawdzic dla innych danych? (t/n): ").lower()
        if cont != 't':
            print("Zamykanie programu.")
            break

if __name__ == "__main__":
    main()