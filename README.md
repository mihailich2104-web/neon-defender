# Neon Defender

Один файл `game.py` — вся игра (процедурная графика/звук, bloom, частицы,
параллакс, волны врагов, боссы, сохранение рекорда).

## Запуск локально (в т.ч. в Termux с X11, для отладки на Android)
```bash
pkg update && pkg upgrade -y
pkg install -y python
pip install pygame numpy pillow
python game.py
```
Термукс = ARM Linux, поэтому запустить .py тут можно, а собрать через него
нативный Windows .exe — нельзя (PyInstaller собирает бинарник под ту ОС/архитектуру,
на которой сам работает; Wine на ARM для такой сборки ненадёжен).

## Как получить Setup.exe с телефона (реальный рабочий способ)
1. Создайте пустой репозиторий на GitHub (можно прямо в приложении GitHub
   или через `git` в Termux: `pkg install git`, `git init`, `git remote add origin ...`).
2. Положите в репозиторий `game.py` и папку `.github/workflows/build.yml`
   (уже в этом архиве).
3. Запушьте с телефона:
   ```bash
   git add .
   git commit -m "neon defender"
   git push origin main
   ```
4. На GitHub откройте вкладку **Actions** — сборка стартует автоматически
   на бесплатном windows-runner'е GitHub, соберёт `NeonDefender.exe`
   (PyInstaller) и упакует его в `Setup.exe` (Inno Setup).
5. Готовый `Setup.exe` скачивается из результатов запуска (Artifacts →
   `NeonDefender-Setup`).

Это и есть единственный надёжный маршрут "собрать Windows-инсталлятор,
управляя всем с Android/Termux" — сама сборка идёт в облаке, на настоящей
Windows-машине.
