import re

# mkdocs-ezlinks builds link targets with os.path.relpath, which yields
# backslashes on Windows ("..%5Cassets%5Cimg.webp") and breaks local builds.
# Hooks run after plugins, so this restores forward slashes before rendering.
LINK_TARGET = re.compile(r"(\]\()([^)\s]*%5C[^)\s]*)")


def on_page_markdown(markdown, page, config, files, **kwargs):
    return LINK_TARGET.sub(lambda m: m.group(1) + m.group(2).replace("%5C", "/"), markdown)
