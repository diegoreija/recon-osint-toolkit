# Ejemplo de ejecución

```bash
python3 src/main.py --domain <dominio>.com --show-unresolved
```

Salida esperada (valores ilustrativos, varían con el tiempo y el dominio):

```
[1/3] Consultando crt.sh para *.empresa.com...
      -> 340 certificados encontrados, 87 nombres únicos extraídos
[2/3] Resolviendo nombres y agrupando por IP compartida...
      -> 12 IPs distintas, 9 nombres sin resolución activa
[3/3] Analizando patrones de naming...

======================================================================
INFRAESTRUCTURA AGRUPADA POR IP (top 10 por nº de nombres)
======================================================================

203.0.113.10  (14 nombres)
    - www.empresa.com
    - api.empresa.com
    - portal.empresa.com
    ...

198.51.100.20  (3 nombres)
    - mail.empresa.com
    - smtp.empresa.com
    - imap.empresa.com

======================================================================
NOMBRES SIN RESOLUCIÓN ACTIVA (9) -- candidatos históricos
======================================================================
    - old-staging.empresa.com
    - legacy-api-v1.empresa.com
    ...

======================================================================
PATRONES DE NAMING DETECTADOS
======================================================================
Prefijos frecuentes: dev, staging
Sufijos frecuentes:  api, portal

Candidatos sugeridos (4, basados en patrones reales del dominio):
    - prod-api.empresa.com
    - qa-portal.empresa.com
    ...
```

> **Nota:** Los "candidatos sugeridos" son hipótesis basadas en el
> patrón de naming ya observado en certificados reales del dominio,
> no un listado genérico de fuerza bruta. Se deben verificar con
> resolución DNS antes de asumir que existen.
