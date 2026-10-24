import os
import re

H1 = re.compile(r"^#\s+.+$", re.M)


def on_page_markdown(markdown, page, config, files, **kwargs):
    cover = page.meta.get("cover")
    if not cover:
        return markdown

    # Accept "x.webp" as well as "assets/x.webp" or "/assets/x.webp" (as written by a CMS)
    name = str(cover).replace("\\", "/").lstrip("/")
    if "assets/" in name:
        name = name.split("assets/", 1)[1]

    base = os.path.dirname(page.file.src_uri)
    rel = os.path.relpath(f"assets/{name}", base).replace(os.sep, "/")
    img = f'![]({rel}){{ .hero }}'

    return H1.sub(lambda m: m.group(0) + "\n\n" + img, markdown, count=1)
