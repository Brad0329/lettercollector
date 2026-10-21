"""Visualizer for cursive collections: Grid image compositor and HTML gallery generator."""
import html
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from src.collector.models import CursiveCharIndex
from src.common.logging import logger


def generate_grid_image(
    index_obj: CursiveCharIndex,
    output_path: Path,
    cols: int = 6,
    cell_size: int = 140,
    label_height: int = 30,
) -> Path:
    """Compose all cursive script images into a single grid image with white background and labels.

    Transparent GIF issues are resolved by pasting onto an opaque white canvas.
    """
    items = index_obj.items
    if not items:
        # Create empty placeholder image
        img = Image.new("RGB", (300, 100), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((10, 40), f"No cursive images for '{index_obj.char}'", fill=(0, 0, 0))
        img.save(output_path, format="PNG")
        return output_path

    total = len(items)
    cols = min(cols, total)
    rows = math.ceil(total / cols)

    cell_width = cell_size
    cell_total_height = cell_size + label_height

    grid_width = cols * cell_width
    grid_height = rows * cell_total_height

    # Create master canvas with pure white background
    grid_img = Image.new("RGB", (grid_width, grid_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(grid_img)

    # Use system font with CJK support if available, otherwise fallback
    font = None
    for candidate in [
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/gulim.ttc",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    ]:
        if Path(candidate).exists():
            try:
                font = ImageFont.truetype(candidate, size=11)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()

    for i, item in enumerate(items):
        r = i // cols
        c = i % cols
        x_offset = c * cell_width
        y_offset = r * cell_total_height

        # Draw cell border
        draw.rectangle(
            [x_offset, y_offset, x_offset + cell_width - 1, y_offset + cell_total_height - 1],
            outline=(230, 230, 230),
            width=1,
        )

        # Open image and paste onto white background
        p = Path(item.file_path)
        if p.exists():
            try:
                with Image.open(p) as raw_img:
                    # Convert to RGBA
                    converted = raw_img.convert("RGBA")
                    # Create white background square for this cell
                    char_canvas = Image.new("RGBA", (cell_size - 10, cell_size - 10), (255, 255, 255, 255))

                    # Scale while keeping aspect ratio
                    converted.thumbnail((cell_size - 10, cell_size - 10), Image.Resampling.LANCZOS)

                    # Center image on canvas
                    paste_x = (char_canvas.width - converted.width) // 2
                    paste_y = (char_canvas.height - converted.height) // 2
                    char_canvas.paste(converted, (paste_x, paste_y), mask=converted)

                    # Paste onto grid image
                    grid_img.paste(char_canvas.convert("RGB"), (x_offset + 5, y_offset + 5))
            except Exception as e:
                logger.warning("Failed to render image %s into grid: %s", p, e)

        # Label: "#1 서예가"
        label_text = f"#{item.index} {item.calligrapher_ko}"
        # Draw label centered
        bbox = draw.textbbox((0, 0), label_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_x = x_offset + max(0, (cell_width - text_w) // 2)
        text_y = y_offset + cell_size + 5
        draw.text((text_x, text_y), label_text, fill=(50, 50, 50), font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    grid_img.save(output_path, format="PNG")
    logger.info("Generated grid image at %s", output_path)
    return output_path


def generate_html_gallery(index_obj: CursiveCharIndex, output_path: Path) -> Path:
    """Generate a clean, standalone HTML gallery view for all images in the collection."""
    cards_html = []
    for item in index_obj.items:
        rel_img = Path(item.file_path).name
        c_ko = html.escape(item.calligrapher_ko)
        c_zh = html.escape(item.calligrapher)
        url = html.escape(item.url)

        cards_html.append(f"""
        <div class="card">
          <div class="img-container">
            <img src="{rel_img}" alt="{c_ko}" loading="lazy" />
          </div>
          <div class="info">
            <span class="index">#{item.index}</span>
            <span class="ko">{c_ko}</span>
            <span class="zh">({c_zh})</span>
          </div>
          <a class="source" href="{url}" target="_blank" rel="noopener">원본 링크</a>
        </div>
        """)

    char_esc = html.escape(index_obj.char)
    total_count = index_obj.total_count
    fetched_at = html.escape(index_obj.fetched_at[:19].replace("T", " "))

    # Breakdown by calligrapher
    stats_pills = []
    for calligrapher, count in sorted(index_obj.calligrapher_counts.items(), key=lambda x: -x[1]):
        stats_pills.append(
            f'<span class="pill">{html.escape(calligrapher)}: <strong>{count}</strong></span>'
        )
    stats_html = " ".join(stats_pills)

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>草書 '{char_esc}' 갤러리 - LetterCollector</title>
  <style>
    :root {{
      --bg: #f8f9fa;
      --card-bg: #ffffff;
      --text: #212529;
      --subtext: #6c757d;
      --border: #e9ecef;
      --accent: #228be6;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 24px;
    }}
    header {{
      max-width: 1200px;
      margin: 0 auto 24px auto;
      padding-bottom: 16px;
      border-bottom: 2px solid var(--border);
    }}
    h1 {{
      margin: 0 0 8px 0;
      font-size: 28px;
    }}
    .meta {{
      color: var(--subtext);
      font-size: 14px;
      margin-bottom: 12px;
    }}
    .stats {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .pill {{
      background: #e7f5ff;
      color: #1971c2;
      padding: 4px 10px;
      border-radius: 16px;
      font-size: 13px;
    }}
    .grid {{
      max-width: 1200px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 16px;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      display: flex;
      flex-direction: column;
      align-items: center;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
      transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .card:hover {{
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }}
    .img-container {{
      width: 130px;
      height: 130px;
      background: #ffffff; /* Contrast against transparent GIF */
      display: flex;
      align-items: center;
      justify-content: center;
      border: 1px solid #f1f3f5;
      border-radius: 4px;
      margin-bottom: 8px;
    }}
    .img-container img {{
      max-width: 120px;
      max-height: 120px;
      object-fit: contain;
    }}
    .info {{
      text-align: center;
      font-size: 14px;
      margin-bottom: 6px;
    }}
    .index {{
      font-weight: bold;
      color: var(--accent);
      margin-right: 4px;
    }}
    .zh {{
      color: var(--subtext);
      font-size: 12px;
    }}
    .source {{
      font-size: 12px;
      color: var(--subtext);
      text-decoration: none;
    }}
    .source:hover {{
      text-decoration: underline;
      color: var(--accent);
    }}
  </style>
</head>
<body>
  <header>
    <h1>草書 '{char_esc}' 서예 갤러리</h1>
    <div class="meta">
      총 <strong>{total_count}</strong>장 수집됨 | 수집 일시: {fetched_at} UTC | 출처: sf.zdic.net
    </div>
    <div class="stats">
      {stats_html}
    </div>
  </header>
  <main class="grid">
    {"".join(cards_html)}
  </main>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
    logger.info("Generated HTML gallery at %s", output_path)
    return output_path
