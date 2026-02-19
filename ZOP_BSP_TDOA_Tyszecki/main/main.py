import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import spectrogram
from simulator import HydroStruct, SubmStruct, gen_sign_source, calc_paths, gen_sign_hydro
from processor import SignalProcessor

def get_input(prompt, current_val):
    user_input = input(f"{prompt} [{current_val}]: ").strip()
    if user_input == "": return current_val
    try: return float(user_input)
    except: return current_val

def main():
    params = {"Vs": 1500.0, "S1_x": 50.0, "S1_y": 50.0, "S1_z": -20.0, "AM": 20.0, "TL": 0.5, "Fs": 100.0}
    
    if not os.path.exists('results'):
        os.makedirs('results')

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("||||||||||||||||||||||||||||||||||||||||||||||||||||")
        print("   ZOP-BSP: PANEL ANALITYCZNY Z POPRAWIONA TABELA   ")
        print("||||||||||||||||||||||||||||||||||||||||||||||||||||")

        params["Vs"] = get_input("Predkosc dzwieku [m/s]", params["Vs"])
        params["S1_x"] = get_input("Pozycja zrodla X [m]", params["S1_x"])
        params["S1_y"] = get_input("Pozycja zrodla Y [m]", params["S1_y"])
        params["S1_z"] = get_input("Glebokosc zrodla Z [m]", params["S1_z"])
        params["AM"] = get_input("Wzmocnienie toru (SNR) [dB]", params["AM"])
        params["Fs"] = get_input("Czestotliwosc probkowania [kHz]", params["Fs"])
        
        filename = input("Nazwa pliku wynikowego: ").strip()
        if not filename: filename = "tdoa_report_latest"
        save_path = os.path.join('results', f"{filename}.png")

        fs_hz = int(params["Fs"] * 1000)
        hydro_cfg = HydroStruct(
            S1=np.array([params["S1_x"], params["S1_y"], params["S1_z"]]),
            H1=np.array([0, 150, -4.0]), H2=np.array([50, 0, -4.0]),
            H3=np.array([300, 50, -4.0]), H4=np.array([50, 100, -4.0]),
            Bs=-45.0, AC=np.array([0.9, 0.9]), Vs=params["Vs"], TL=params["TL"]
        )
        subm_cfg = SubmStruct(
            TF=np.array([1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 18, 19, 20.0]),
            TA=np.array([0.1]*11), AM=params["AM"], Fs=params["Fs"], Tp=0.2, RD=np.array([10, 0.005, 1, 30])
        )

        signS = gen_sign_source(subm_cfg)
        signH = gen_sign_hydro(signS, hydro_cfg, calc_paths(hydro_cfg), fs_hz)
        proc = SignalProcessor(fs_hz)

        # Dashboard
        plt.style.use('dark_background')
        fig = plt.figure(figsize=(16, 10))
        fig.suptitle(f"RAPORT HYDROAKUSTYCZNY: {filename}", fontsize=18, color='cyan', fontweight='bold')

        ax1 = plt.subplot2grid((2, 3), (0, 0), projection='3d')
        ax2 = plt.subplot2grid((2, 3), (0, 1), colspan=2)
        ax3 = plt.subplot2grid((2, 3), (1, 0)) 
        ax4 = plt.subplot2grid((2, 3), (1, 1), colspan=2)

        # 1. Geometria
        ax1.scatter(hydro_cfg.S1[0], hydro_cfg.S1[1], hydro_cfg.S1[2], c='red', s=100, label='S1')
        h_pos = np.array([hydro_cfg.H1, hydro_cfg.H2, hydro_cfg.H3, hydro_cfg.H4])
        ax1.scatter(h_pos[:,0], h_pos[:,1], h_pos[:,2], c='lime', s=50, label='H1-H4')
        ax1.set_title("Geometria ukladu [m]")

        # 2. Przebiegi (Zoom)
        t = np.arange(len(signH[0])) / fs_hz * 1000
        ax2.plot(t, signH[0], label='H1 (Ref)', color='yellow', alpha=0.7)
        ax2.plot(t, signH[1], label='H2', color='cyan', alpha=0.7)
        ax2.set_xlim(35, 75); ax2.set_title("Przebiegi czasowe (ms)"); ax2.legend()

        # 3. TABELA PARAMETROW (Poprawiona kolorystyka)
        ax3.axis('off')
        table_data = [
            ["PARAMETR", "WARTOSC"],
            ["Predkosc Vs", f"{params['Vs']} m/s"],
            ["S1 [X, Y, Z]", f"[{params['S1_x']}, {params['S1_y']}, {params['S1_z']}]"],
            ["AM (SNR)", f"{params['AM']} dB"],
            ["Probkowanie", f"{params['Fs']} kHz"],
            ["Straty TL", f"{params['TL']} dB/10m"]
        ]
        
        # Tworzenie tabeli z wymuszonymi kolorami
        table = ax3.table(cellText=table_data, loc='center', cellLoc='left')
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1.1, 2.5)
        
        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor('white')
            if row == 0:
                cell.set_facecolor('#003366')
                cell.get_text().set_color('cyan')
                cell.get_text().set_weight('bold')
            else:
                cell.set_facecolor('#1a1a1a')
                cell.get_text().set_color('white')

        ax3.set_title("KONFIGURACJA EKSPERYMENTU", pad=20, color='cyan', weight='bold')

        # 4. GCC-PHAT
        delay_est, cc_phat, t_cc = proc.gcc_phat(signH[1], signH[0])
        ax4.plot(t_cc*1000, cc_phat, color='lime', label='GCC-PHAT')
        actual_tdoa = (np.linalg.norm(hydro_cfg.S1-hydro_cfg.H2) - np.linalg.norm(hydro_cfg.S1-hydro_cfg.H1))/hydro_cfg.Vs
        ax4.axvline(x=actual_tdoa*1000, color='red', linestyle='--', label='Teoria')
        ax4.set_title("Wynik Estymacji TDOA (ms)")
        ax4.set_xlim(actual_tdoa*1000 - 10, actual_tdoa*1000 + 10); ax4.legend()

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        # Zapis i wyświetlenie
        plt.savefig(save_path, dpi=150)
        print(f"\n[OK] Dashboard zapisany pomyślnie: {save_path}")
        plt.show()

        if input("\nCzy chcesz sprawdzic dla innych danych? (t/n): ").lower() != 't': break

if __name__ == "__main__":
    main()
