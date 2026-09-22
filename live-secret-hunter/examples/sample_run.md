# Ejemplo de ejecución

```bash
python3 src/main.py --url https://target.com/static/js/main.js
```

Salida esperada (valores ilustrativos):

```
[1/2] Descargando y escaneando 1 fichero(s) JS...
      -> 3 posibles secretos encontrados
[2/2] Verificando si cada secreto sigue activo (endpoints de solo lectura)...

======================================================================
🔴 SECRETOS ACTIVOS (1) -- impacto real, priorizar
======================================================================

[sendgrid_key] https://target.com/static/js/main.js
    valor: SG.xxxxxxxxxxxxxxxxxxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    estado: Clave válida, acceso confirmado a /v3/scopes

======================================================================
⚪ SIN VERIFICACIÓN AUTOMÁTICA (1) -- revisar manualmente
======================================================================

[aws_access_key] https://target.com/static/js/main.js
    valor: AKIAXXXXXXXXXXXXXXXX
    motivo: No hay checker automático implementado para este tipo de secreto

======================================================================
⚫ SECRETOS INACTIVOS (1) -- ya rotados/revocados
======================================================================
    [github_token] https://target.com/static/js/main.js
```

## Modo sin verificación

Si solo quieres extraer sin hacer ninguna llamada saliente a terceros:

```bash
python3 src/main.py --url https://target.com/static/js/main.js --no-verify
```

## Varios ficheros a la vez

```bash
cat > urls.txt << EOF
https://target.com/static/js/main.js
https://target.com/static/js/vendor.js
https://target.com/static/js/chunk-42.js
EOF

python3 src/main.py --url-list urls.txt
```

> **Nota:** Cada verificación de liveness hace una única llamada de
> solo lectura al endpoint oficial del proveedor (whoami, balance,
> scopes...). Ninguna llamada modifica, borra ni crea nada. Aun así,
> ejecuta esto solo contra targets para los que tengas autorización
> explícita.
