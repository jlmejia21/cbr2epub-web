"""EPUB builder optimized for Kindle and iPad reading of comics."""
import os
import zipfile
import uuid
import tempfile
import shutil
from datetime import datetime


class EpubBuilder:
    """Build a valid EPUB 3.0 file optimized for comics/visual content on Kindle/iPad."""

    def __init__(self, title, author='Desconocido', language='es'):
        self.title = title
        self.author = author
        self.language = language
        self.uuid = str(uuid.uuid4())
        self.date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        self.images = []

    def add_image(self, image_path):
        """Add an image to the EPUB."""
        self.images.append(image_path)

    def _escape_xml(self, text):
        """Escape XML special characters."""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

    def _get_mime_type(self, filename):
        """Get MIME type for image."""
        ext = os.path.splitext(filename)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.webp': 'image/webp',
        }
        return mime_types.get(ext, 'application/octet-stream')

    def build(self, output_path):
        """Build the EPUB file optimized for Kindle/iPad."""
        if not self.images:
            raise ValueError("No hay imagenes para incluir en el EPUB.")

        with tempfile.TemporaryDirectory() as temp_dir:
            ops_dir = os.path.join(temp_dir, 'OPS')
            images_dir = os.path.join(ops_dir, 'images')
            meta_inf = os.path.join(temp_dir, 'META-INF')

            os.makedirs(images_dir)
            os.makedirs(meta_inf)

            for i, img_path in enumerate(self.images):
                img_name = os.path.basename(img_path)
                dest_path = os.path.join(images_dir, img_name)
                if os.path.exists(img_path):
                    shutil.copy2(img_path, dest_path)

            mimetype_path = os.path.join(temp_dir, 'mimetype')
            with open(mimetype_path, 'w', encoding='utf-8') as f:
                f.write('application/epub+zip')

            container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OPS/package.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
            container_path = os.path.join(meta_inf, 'container.xml')
            with open(container_path, 'w', encoding='utf-8') as f:
                f.write(container_xml)

            cover_img_name = os.path.basename(self.images[0]) if self.images else ''

            manifest_items = []

            for i, img_path in enumerate(self.images):
                img_name = os.path.basename(img_path)
                mime = self._get_mime_type(img_name)
                props = 'cover-image' if i == 0 else ''
                manifest_items.append(f'    <item id="img_{i}" href="images/{img_name}" media-type="{mime}"/>' + (f' properties="{props}"' if props else ''))

            manifest_items.append('    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')
            manifest_items.append('    <item id="css" href="styles.css" media-type="text/css"/>')
            manifest_items.append('    <item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>')

            spine_items = ['    <itemref idref="cover"/>']
            for i in range(len(self.images)):
                spine_items.append(f'    <itemref idref="page_{i}"/>')
                manifest_items.append(f'    <item id="page_{i}" href="page_{i}.xhtml" media-type="application/xhtml+xml"/>')

            manifest = '\n'.join(manifest_items)
            spine = '\n'.join(spine_items)

            package_opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:meta="http://www.idpf.org/2007/opf">
    <dc:title>{self._escape_xml(self.title)}</dc:title>
    <dc:creator>{self._escape_xml(self.author)}</dc:creator>
    <dc:language>{self.language}</dc:language>
    <meta property="dcterms:modified">{self.date}</meta>
    <dc:identifier id="uid">urn:uuid:{self.uuid}</dc:identifier>
    <meta name="cover" content="img_0"/>
    <meta property="rendition:layout">pread-read</meta>
    <meta property="rendition:orientation">landscape</meta>
    <meta property="rendition:spread">landscape</meta>
  </metadata>
  <manifest>
{manifest}
  </manifest>
  <spine>
{spine}
  </spine>
</package>'''
            package_path = os.path.join(ops_dir, 'package.opf')
            with open(package_path, 'w', encoding='utf-8') as f:
                f.write(package_opf)

            nav_xhtml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2011/epub" lang="es">
<head>
  <title>Contenido</title>
  <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Contenido</h1>
    <ol>
      <li><a href="cover.xhtml">Portada</a></li>
'''
            for i in range(len(self.images)):
                nav_xhtml += f'      <li><a href="page_{i}.xhtml">Pagina {i + 1}</a></li>\n'
            nav_xhtml += '''    </ol>
  </nav>
</body>
</html>'''
            nav_path = os.path.join(ops_dir, 'nav.xhtml')
            with open(nav_path, 'w', encoding='utf-8') as f:
                f.write(nav_xhtml)

            styles_css = '''@page {
  margin: 0;
  padding: 0;
}
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
html, body {
  width: 100%;
  height: 100%;
  background-color: #1a1a1a;
}
body {
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
}
img {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  display: block;
}
figure {
  margin: 0;
  padding: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}
.cover-page {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #1a1a1a;
  width: 100%;
}
.cover-image {
  max-height: 70vh;
  width: auto;
  max-width: 100%;
  object-fit: contain;
}
.book-title {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.8em;
  color: white;
  text-align: center;
  margin: 20px 10px;
  padding: 0 20px;
}
.book-author {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.1em;
  color: #aaaaaa;
  text-align: center;
  margin-top: 10px;
}'''
            styles_path = os.path.join(ops_dir, 'styles.css')
            with open(styles_path, 'w', encoding='utf-8') as f:
                f.write(styles_css)

            cover_xhtml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="es">
<head>
  <title>Portada</title>
  <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
  <div class="cover-page">
    <img class="cover-image" src="images/{cover_img_name}" alt="Portada"/>
    <h1 class="book-title">{self._escape_xml(self.title)}</h1>
    <p class="book-author">{self._escape_xml(self.author)}</p>
  </div>
</body>
</html>'''
            cover_path = os.path.join(ops_dir, 'cover.xhtml')
            with open(cover_path, 'w', encoding='utf-8') as f:
                f.write(cover_xhtml)

            for i in range(len(self.images)):
                img_name = os.path.basename(self.images[i])
                page_xhtml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="es">
<head>
  <title>Pagina {i + 1}</title>
  <link rel="stylesheet" type="text/css" href="styles.css"/>
  <meta name="viewport" content="width=device-width, height=device-height, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"/>
</head>
<body>
  <figure>
    <img src="images/{img_name}" alt="Pagina {i + 1}"/>
  </figure>
</body>
</html>'''
                page_path = os.path.join(ops_dir, f'page_{i}.xhtml')
                with open(page_path, 'w', encoding='utf-8') as f:
                    f.write(page_xhtml)

            with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                zf.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file == 'mimetype':
                            continue
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zf.write(file_path, arcname)

        return output_path