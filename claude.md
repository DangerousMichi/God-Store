# BadStore → GodStore Pipeline

## Contexto del proyecto
Práctica de ciberseguridad universitaria (UTSJR — DS01SV-25).
BadStore es una app LAMP vulnerable (Perl/CGI + MySQL + Apache).
El objetivo es: auditar vulnerabilidades → parchearlas → rediseñar como GodStore.

## Stack original
- Backend: Perl CGI scripts en www/cgi-bin/
- Base de datos: MySQL (mariadb/bin/badstore-setup.sql)
- Frontend: HTML estático en www/
- Servidor: Apache en Docker

## Stack objetivo (GodStore)
- Frontend: HTML/CSS/JS moderno con diseño limpio
- Backend: Perl CGI refactorizado con queries preparadas
- Seguridad: OWASP Top 10 parcheado

## Agentes del pipeline
1. Agente Auditor — detecta vulns OWASP en archivos .pl y .cgi
2. Agente Parchador — genera código corregido con comentarios de fix
3. Agente Rediseñador — convierte frontend a GodStore moderno
4. Agente Reportero — genera reporte ejecutivo de la práctica

## Comandos útiles
- Build: docker build -t badstore .
- Run: docker run -d -p 80:80 badstore
- Archivos vulnerables: www/cgi-bin/*.pl

## Convenciones de commits
- feat(audit): cuando se detectan nuevas vulns
- fix(security): cuando se parchea una vulnerabilidad
- refactor(godstore): cuando se aplica rediseño
- docs(report): cuando se actualiza el reporte