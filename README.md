# Pasywna Lokalizacja Hydroakustyczna - Estymacja TDOA
Autor: Maciej Tyszecki
Przedmiot: Projekt Przejściowy

## Opis projektu
Projekt realizuje zadanie wyznaczania różnicy czasu przybycia sygnału (TDOA) przy użyciu algorytmu GCC-PHAT. 
System symuluje warunki rzeczywiste (rewerberacje, szum, tłumienie) zgodnie z modelem Uricka.

## Struktura
- `main.py`: Punkt wejścia aplikacji.
- `processor.py`: Implementacja wagowanej korelacji wzajemnej.
- `simulator.py`: Silnik fizyczny propagacji fali (bazujący na `SimZopBsp.py`, którego autorem jest Pan kmdr dr hab. inż. Piotr Szymak, p.szymak@amw.gdynia.pl).
- `results/`: Wyniki analizy w formie graficznej i sprawozdanie.

## Jak uruchomić?
1. Otwórz projekt w Visual Studio 2026.
2. Zainstaluj zależności: `pip install -r requirements.txt`.
3. Uruchom `main.py`.
