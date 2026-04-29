# Elden Ring Routebook

Локальный чеклист прохождения на основе сохраненного `Walkthrough.html` из `eldenring.redmaw.dev/sheets/walkthrough`.

## Запуск

Из папки `C:\Users\blagodaren\Desktop\Claude`:

```powershell
python -m http.server 4173
```

Открыть:

```text
http://localhost:4173/elden-ring-walkthrough/
```

Сервер лучше запускать именно из `Claude`, чтобы приложение могло читать соседний файл:

```text
elden-ring-wiki/meta/manifest.json
```

## Возможности

- чеклист маршрута с автосохранением в браузере;
- прогресс по всему прохождению и по каждой секции;
- поиск по шагам маршрута;
- фильтры по сюжетным, необязательным, NPC, боссам, луту и пропускаемым шагам;
- импорт и экспорт прогресса;
- поиск по локальному манифесту русской wiki.

## Импорт гайда

```powershell
python "C:\Users\blagodaren\Desktop\Claude\elden-ring-walkthrough\tools\import-redmaw-walkthrough.py" "C:\Users\blagodaren\Downloads\Walkthrough.html" "C:\Users\blagodaren\Desktop\Claude\elden-ring-walkthrough\data\route-data.js"
```

Текущий импорт: `49` секций и `3354` шага.
