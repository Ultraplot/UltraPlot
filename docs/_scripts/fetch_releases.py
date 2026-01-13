"""
Dynamically build what's new page based on github releases
"""

import re
from pathlib import Path

import requests

GITHUB_REPO = "ultraplot/ultraplot"
OUTPUT_RST = Path("whats_new.rst")


GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases"


def format_release_body(text):
    """Formats GitHub release notes for better RST readability."""
    lines = text.split("\n")
    formatted = []
    in_code_block = False
    indent_string = "    "
    current_indent = 0

    for line in lines:
        # Preserve original line for code blocks, but strip for processing directives
        stripped_line = line.strip()

        # Detect Dropdown Start
        # <details> <summary> snippet </summary>
        match_details = re.search(
            r"<details>\s*<summary>(.*?)</summary>", stripped_line, re.IGNORECASE
        )
        if match_details:
            summary = match_details.group(1).strip()
            formatted.append(
                f"{indent_string * current_indent}.. dropdown:: {summary}\n"
            )
            current_indent += 1
            continue

        # Detect Dropdown End
        if stripped_line == "</details>":
            if current_indent > 0:
                current_indent -= 1
            continue

        # Code Block Start/End
        if stripped_line.startswith("```"):
            if in_code_block:
                in_code_block = False
                formatted.append("")
            else:
                in_code_block = True
                lang = stripped_line.strip("`").strip()
                formatted.append(
                    f"{indent_string * current_indent}.. code-block:: {lang if lang else 'text'}\n"
                )
            continue

        if in_code_block:
            # Code lines need 1 extra indent relative to current context
            formatted.append(f"{indent_string * (current_indent + 1)}{line}")
            continue

        # Normal lines
        if not stripped_line:
            formatted.append("")
            continue

        # Images
        # <img ... src="..." ... />
        match_img = re.search(
            r'<img\s+.*?src=["\']([^"\']+)["\'].*?>', stripped_line, re.IGNORECASE
        )
        if match_img:
            src = match_img.group(1)
            formatted.append(f"{indent_string * current_indent}.. image:: {src}\n")
            continue

        # Markdown Images
        # ![alt](url)
        match_md_img = re.search(r"!\[([^\]]*)\]\(([^)]+)\)", stripped_line)
        if match_md_img:
            alt = match_md_img.group(1)
            src = match_md_img.group(2)
            formatted.append(f"{indent_string * current_indent}.. image:: {src}")
            if alt:
                formatted.append(f"{indent_string * current_indent}   :alt: {alt}")
            formatted.append("")
            continue

        # Headers
        # Note: Previous implementation used ~ for H2 (##).
        # But H1 is =, H2 is -.
        # So ## should be H3 (~), ### H4 (^), #### H5 (")
        if stripped_line.startswith("## "):
            title = stripped_line[3:].strip()
            formatted.append(
                f"{indent_string * current_indent}{title}\n{indent_string * current_indent}{'~' * len(title)}\n"
            )
            continue
        elif stripped_line.startswith("### "):
            title = stripped_line[4:].strip()
            formatted.append(
                f"{indent_string * current_indent}{title}\n{indent_string * current_indent}{'^' * len(title)}\n"
            )
            continue
        elif stripped_line.startswith("#### "):
            title = stripped_line[5:].strip()
            formatted.append(
                f"{indent_string * current_indent}{title}\n{indent_string * current_indent}{'"' * len(title)}\n"
            )
            continue

        # Links
        stripped_line = re.sub(
            r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)", r"`\1 <\2>`_", stripped_line
        )

        # Italics using _text_
        stripped_line = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"*\1*", stripped_line)

        formatted.append(f"{indent_string * current_indent}{stripped_line}")

    formatted_text = "\n".join(formatted)

    # Convert PR references (remove "by @user in ..." but keep the link)
    formatted_text = re.sub(
        r" by @\w+ in (https://github.com/[^\s]+)", r" (\1)", formatted_text
    )

    return formatted_text.strip()


def fetch_all_releases():
    """Fetches all GitHub releases across multiple pages."""
    releases = []
    page = 1

    while True:
        response = requests.get(GITHUB_API_URL, params={"per_page": 30, "page": page})
        if response.status_code != 200:
            print(f"Error fetching releases: {response.status_code}")
            break

        page_data = response.json()
        # If the page is empty, stop fetching
        if not page_data:
            break

        releases.extend(page_data)
        page += 1

    return releases


def fetch_releases():
    """Fetches the latest releases from GitHub and formats them as RST."""
    releases = fetch_all_releases()
    if not releases:
        print(f"Error fetching releases!")
        return ""

    header = "What's new?"
    rst_content = f".. _whats_new:\n\n{header}\n{'=' * len(header)}\n\n"  # H1

    for release in releases:
        # ensure title is formatted as {tag}: {title}
        tag = release["tag_name"].lower()
        title = release["name"]
        if title.startswith(tag):
            title = title[len(tag) :]
            while title:
                if not title[0].isalpha():
                    title = title[1:]
                    title = title.strip()
                else:
                    title = title.strip()
                    break

        if title:
            title = f"{tag}: {title}"
        else:
            title = tag

        date = release["published_at"][:10]
        body = format_release_body(release["body"] or "")

        # Version header (H2)
        rst_content += f"{title} ({date})\n{'-' * (len(title) + len(date) + 3)}\n\n"

        # Process body content
        rst_content += f"{body}\n\n"

    return rst_content


def write_rst():
    """Writes fetched releases to an RST file."""
    content = fetch_releases()
    if content:
        with open(OUTPUT_RST, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {OUTPUT_RST}")
    else:
        print("No updates to write.")


if __name__ == "__main__":
    write_rst()
