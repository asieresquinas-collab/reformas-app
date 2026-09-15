# Vornicu Reformas · app de presupuestos

PWA de presupuestos de reformas (dosier + presupuesto + contrato) para Vornicu Ioan Marian, Santutxu (Bilbao).
Hecha por Azkar Servicios sobre la misma base que la app de Azkar Mudanzas.

- `index.html` — toda la app (HTML + CSS + JS). Tarifa dentro (`TARIFA_BASE`).
- `sw.js`, `manifest.json`, `icons/` — instalación como app en el móvil.
- Datos guardados en el propio dispositivo (localStorage). Copia de seguridad en Ajustes.

Cada cambio: subir `APP_VERSION` en index.html y el nombre de caché en `sw.js`.
