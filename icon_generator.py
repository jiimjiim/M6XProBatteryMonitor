"""Render a high-contrast, number-only battery tray icon."""
from PIL import Image, ImageDraw, ImageFont


def _battery_color(percentage: int):
    red = (239, 55, 48)
    orange = (255, 157, 35)
    green = (42, 205, 112)
    if percentage <= 50:
        start, end = red, orange
        amount = percentage / 50
    else:
        start, end = orange, green
        amount = (percentage - 50) / 50
    amount = max(0.0, min(1.0, amount))
    return tuple(round(a + (b - a) * amount) for a, b in zip(start, end))


def create_battery_icon(percentage: int, charging: bool = False, offline: bool = False) -> Image.Image:
    """Draw only the battery percentage, colored by remaining charge."""
    scale = 2
    size = 64 * scale
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    if offline:
        text = "--"
        fill = (150, 158, 166, 255)
    else:
        percentage = max(0, min(100, int(percentage)))
        text = str(percentage)
        fill = (*_battery_color(percentage), 255)

    preferred_size = {1: 108, 2: 88, 3: 68}[len(text)]
    try:
        font = ImageFont.truetype("arialbd.ttf", preferred_size)
    except OSError:
        font = ImageFont.load_default()

    # Fit wide three-digit values inside the 64 px tray image.
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=3)
    while bbox[2] - bbox[0] > size - 8 and preferred_size > 42:
        preferred_size -= 2
        font = ImageFont.truetype("arialbd.ttf", preferred_size)
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=3)

    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = (size - width) / 2 - bbox[0]
    y = (size - height) / 2 - bbox[1] - 2
    draw.text(
        (x, y), text, font=font, fill=fill,
        stroke_width=3, stroke_fill=(20, 24, 29, 245),
    )
    return image.resize((64, 64), Image.Resampling.LANCZOS)
