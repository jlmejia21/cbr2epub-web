# CBR/CBZ a EPUB - Web Application

Convertidor de archivos CBR/CBZ a formato EPUB optimizado para Kindle e iPad.

## Deployment en Render

### Pasos:

1. **Crear cuenta en Render** (render.com)

2. **Crear repositorio en GitHub** con estos archivos:
   ```
   cbr2epub_web/
   ├── app.py
   ├── requirements.txt
   ├── Procfile
   ├── templates/
   │   └── index.html
   └── lib/
       ├── extractor.py
       ├── image_proc.py
       ├── epub_builder.py
       └── utils.py
   ```

3. **Conectar Render a GitHub:**
   - New → Web Service
   - Connect tu repositorio
   - Configurar:
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`

4. **Desplegar:**
   - Click "Create Web Service"
   - Esperar a que termine el build
   - Obtener URL (ej: `https://cbr2epub.onrender.com`)

### Configuracion en Render Dashboard:

| Setting | Value |
|---------|-------|
| Environment | Python 3.9+ |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT` |
| Plan | Free (limitado a 512MB RAM) |

### Notas Importantes:

- **Memoria limitada:** El plan gratuito tiene 512MB. Archivos CBR grandes pueden fallar.
- **Tiempo limite:** 30 segundos para requests.
- **Archivos temporales:** Se borran automaticamente despues de descargar.

### Para archivos grandes (>100MB):

Considerar usar un VPS con mas recursos:
- DigitalOcean ($4-6/mes)
- Linode ($5-10/mes)
- AWS EC2 (t2.micro gratis)

### Locally:

```bash
cd cbr2epub_web
pip install -r requirements.txt
python3 app.py
# Abrir http://localhost:5000
```# cbr2epub-web
# cbr2epub-web
