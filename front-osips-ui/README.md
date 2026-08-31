# front-osips-ui

Frontend web-интерфейса управления OpenSIPS: Vue 3 + Vuetify 3 + Pinia + Vue Router, сборка Vite.

Документация по сборке и запуску всего проекта — в [README.md](../README.md) корня репозитория.

```bash
npm install
npm run dev      # http://localhost:5173, /api проксируется на http://127.0.0.1:8000
npm run build    # прод-сборка в dist/, её отдаёт backend (STATIC_DIR)
```

Структура `src/`:

| Каталог | Содержимое |
|---|---|
| `api/` | axios-клиент и вызовы эндпоинтов |
| `stores/` | Pinia: авторизация, список серверов, уведомления |
| `router/` | маршруты и guard по правам (`meta.permission`) |
| `layouts/` | каркас с меню и выбором сервера |
| `views/` | страницы разделов |
| `components/` | таблицы dispatcher/LB, диалоги, switcher состояния ноды |
