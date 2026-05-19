#!/usr/bin/env python3
"""Apply translations-pt-BR.json to all figures/*.dia, output translated copies to a target dir.

After substituting strings, recompute obj_bb for each Standard - Text object so that
text-with-background labels (e.g. "Output X") don't render with stale wider-than-text
background rectangles from the English source.
"""
import gzip
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent

# Helvetica character widths in 1/1000 em units (Adobe AFM standard).
# Default 556 for unmapped chars (matches digit/lowercase width).
HELVETICA = {
    ' ': 278, '!': 278, '"': 355, '#': 556, '$': 556, '%': 889, '&': 667,
    "'": 191, '(': 333, ')': 333, '*': 389, '+': 584, ',': 278, '-': 333,
    '.': 278, '/': 278, ':': 278, ';': 278, '<': 584, '=': 584, '>': 584,
    '?': 556, '@': 1015, '[': 278, '\\': 278, ']': 278, '^': 469, '_': 556,
    '`': 333, '{': 334, '|': 260, '}': 334, '~': 584,
    '0': 556, '1': 556, '2': 556, '3': 556, '4': 556, '5': 556, '6': 556,
    '7': 556, '8': 556, '9': 556,
    'A': 667, 'B': 667, 'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778,
    'H': 722, 'I': 278, 'J': 500, 'K': 667, 'L': 556, 'M': 833, 'N': 722,
    'O': 778, 'P': 667, 'Q': 778, 'R': 722, 'S': 667, 'T': 611, 'U': 722,
    'V': 667, 'W': 944, 'X': 667, 'Y': 667, 'Z': 611,
    'a': 556, 'b': 556, 'c': 500, 'd': 556, 'e': 556, 'f': 278, 'g': 556,
    'h': 556, 'i': 222, 'j': 222, 'k': 500, 'l': 222, 'm': 833, 'n': 556,
    'o': 556, 'p': 556, 'q': 556, 'r': 333, 's': 500, 't': 278, 'u': 556,
    'v': 500, 'w': 722, 'x': 500, 'y': 500, 'z': 500,
    'á': 556, 'à': 556, 'â': 556, 'ã': 556, 'ä': 556, 'å': 556,
    'é': 556, 'è': 556, 'ê': 556, 'ë': 556,
    'í': 278, 'ì': 278, 'î': 278, 'ï': 278,
    'ó': 556, 'ò': 556, 'ô': 556, 'õ': 556, 'ö': 556,
    'ú': 556, 'ù': 556, 'û': 556, 'ü': 556,
    'ñ': 556, 'ç': 500, 'ß': 611,
    'Á': 667, 'À': 667, 'Â': 667, 'Ã': 667, 'Ä': 667, 'Å': 667,
    'É': 667, 'È': 667, 'Ê': 667, 'Ë': 667,
    'Í': 278, 'Ì': 278, 'Î': 278, 'Ï': 278,
    'Ó': 778, 'Ò': 778, 'Ô': 778, 'Õ': 778, 'Ö': 778,
    'Ú': 722, 'Ù': 722, 'Û': 722, 'Ü': 722,
    'Ñ': 722, 'Ç': 722,
}
# Empirically derived from the English source's cached obj_bb vs. AFM width sums.
SCALE = 0.92


def text_width_cm(text, font_height_cm):
    return sum(HELVETICA.get(c, 556) for c in text) * font_height_cm * SCALE / 1000


def update_text_object(obj_xml, translations):
    """Substitute string and recompute obj_bb if it changed."""
    text_match = re.search(r'<dia:string>#(.*?)#</dia:string>', obj_xml, re.DOTALL)
    if not text_match:
        return obj_xml
    original = text_match.group(1)
    translated = translations.get(original)
    if translated is None or translated == original:
        return obj_xml

    # Substitute the string first
    obj_xml = obj_xml.replace(
        f'<dia:string>#{original}#</dia:string>',
        f'<dia:string>#{translated}#</dia:string>',
    )

    # Only Standard - Text objects have obj_bb that visibly affects rendering
    if 'type="Standard - Text"' not in obj_xml:
        return obj_xml

    pos_m = re.search(r'name="obj_pos">\s*<dia:point val="([-\d.]+),([-\d.]+)"', obj_xml)
    bb_m = re.search(r'name="obj_bb">\s*<dia:rectangle val="([-\d.]+),([-\d.]+);([-\d.]+),([-\d.]+)"', obj_xml)
    h_m = re.search(r'name="height">\s*<dia:real val="([-\d.eE]+)"', obj_xml)
    align_m = re.search(r'name="alignment">\s*<dia:enum val="(\d+)"', obj_xml)
    if not (pos_m and bb_m and h_m):
        return obj_xml

    pos_x = float(pos_m.group(1))
    font_height = float(h_m.group(1))
    alignment = int(align_m.group(1)) if align_m else 0

    lines = translated.split('\n')
    width = max(text_width_cm(line, font_height) for line in lines) if lines else 0
    # Padding to avoid clipping; AFM-derived widths are slightly conservative
    # for some accented characters and Dia's own metric can be marginally larger.
    width += 0.15

    if alignment == 0:    # left
        new_x1, new_x2 = pos_x, pos_x + width
    elif alignment == 1:  # center
        new_x1, new_x2 = pos_x - width / 2, pos_x + width / 2
    else:                 # right
        new_x1, new_x2 = pos_x - width, pos_x

    # Preserve y range from the cached bb (height handling is more involved
    # and the y dimension is usually fine for these labels).
    y1, y2 = bb_m.group(2), bb_m.group(4)
    new_bb = f'{new_x1:.4f},{y1};{new_x2:.4f},{y2}'

    return re.sub(
        r'(name="obj_bb">\s*<dia:rectangle val=")[-\d.,;]+(")',
        rf'\g<1>{new_bb}\g<2>',
        obj_xml,
        count=1,
    )


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: translate-pt-BR.py <output-dir>")

    out_dir = Path(sys.argv[1])
    out_dir.mkdir(exist_ok=True)

    translations = json.loads((HERE / "translations-pt-BR.json").read_text(encoding="utf-8"))

    obj_re = re.compile(r'<dia:object\b.*?</dia:object>', re.DOTALL)

    for src in sorted(HERE.glob("*.dia")):
        content = gzip.decompress(src.read_bytes()).decode("utf-8")
        translated = obj_re.sub(lambda m: update_text_object(m.group(0), translations), content)
        (out_dir / src.name).write_bytes(gzip.compress(translated.encode("utf-8")))
        print(f"  {src.name}")

    print(f"Translated {len(list(HERE.glob('*.dia')))} files into {out_dir}/")


if __name__ == "__main__":
    main()
