# Pasywna Lokalizacja Hydroakustyczna - Estymacja TDOA
Autor: Maciej Tyszecki
Przedmiot: Projekt Przejœciowy

## Opis projektu
Projekt realizuje zadanie wyznaczania ró¿nicy czasu przybycia sygna³u (TDOA) przy u¿yciu algorytmu GCC-PHAT. 
System symuluje warunki rzeczywiste (rewerberacje, szum, t³umienie) zgodnie z modelem Uricka.

## Struktura
- `main.py`: Punkt wejœcia aplikacji.
- `processor.py`: Implementacja wagowanej korelacji wzajemnej.
- `simulator.py`: Silnik fizyczny propagacji fali (bazuj¹cy na `SimZopBsp.py`).
- `results/`: Wyniki analizy w formie graficznej.

## Jak uruchomiæ
1. Otwórz projekt w Visual Studio 2026.
2. Zainstaluj zale¿noœci: `pip install -r requirements.txt`.
3. Uruchom `main.py`.