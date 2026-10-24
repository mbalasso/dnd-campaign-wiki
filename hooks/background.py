import os
import re

H1 = re.compile(r"^#\s+.+$", re.M)


def on_page_markdown(markdown, page, config, files, **kwargs):
    cover = page.meta.get("cover")
    if not cover:
        return markdown

    base = os.path.dirname(page.file.src_uri)
    rel = os.path.relpath(f"assets/{cover}", base).replace(os.sep, "/")
    img = f'![]({rel}){{ .hero }}'

    return H1.sub(lambda m: m.group(0) + "\n\n" + img, markdown, count=1)
