"""Generate the M6X battery monitor's app icon: mouse + charge gauge."""
from PIL import Image, ImageDraw


def blend(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def make_icon(size):
    scale = 4
    side = size * scale
    image = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    mask = Image.new("L", (side, side), 0)
    mask_draw = ImageDraw.Draw(mask)
    margin = side * 0.04
    radius = side * 0.22
    mask_draw.rounded_rectangle(
        (margin, margin, side - margin, side - margin),
        radius=radius,
        fill=255,
    )

    # Deep indigo tile with a quiet top-to-bottom shift.
    bg = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg)
    top_color, bottom_color = (31, 43, 69, 255), (13, 20, 38, 255)
    for y in range(side):
        color = blend(top_color, bottom_color, y / max(1, side - 1))
        bg_draw.line((0, y, side, y), fill=color)
    image.alpha_composite(Image.composite(bg, Image.new("RGBA", (side, side)), mask))

    draw = ImageDraw.Draw(image)
    # Fine inner keyline gives the tile a crisp silhouette at small sizes.
    draw.rounded_rectangle(
        (margin + 2, margin + 2, side - margin - 2, side - margin - 2),
        radius=radius,
        outline=(150, 190, 225, 38),
        width=max(2, side // 128),
    )

    # Wireless mouse silhouette: a vertical capsule, slightly above center.
    body_w = side * 0.44
    body_h = side * 0.66
    left = (side - body_w) / 2
    body_top = side * 0.16
    body_bottom = body_top + body_h
    body_radius = body_w / 2
    draw.rounded_rectangle(
        (left, body_top, left + body_w, body_bottom),
        radius=body_radius,
        fill=(238, 244, 252, 255),
    )

    # Button split line across the upper shell.
    split_y = body_top + body_h * 0.28
    inset = body_w * 0.16
    draw.line(
        (left + inset, split_y, left + body_w - inset, split_y),
        fill=(148, 163, 184, 255),
        width=max(2, side // 110),
    )

    # Charge slot in the body: reads as the scroll area and the battery level.
    slot_w = body_w * 0.26
    slot_h = body_h * 0.40
    slot_x = (side - slot_w) / 2
    slot_y = split_y + body_h * 0.14
    draw.rounded_rectangle(
        (slot_x, slot_y, slot_x + slot_w, slot_y + slot_h),
        radius=slot_w / 2,
        fill=(22, 32, 52, 255),
    )

    # Green charge fill, ~72% from the bottom, leaving headroom at the top.
    pad = slot_w * 0.15
    inner_w = slot_w - 2 * pad
    inner_h = slot_h - 2 * pad
    fill_h = inner_h * 0.72
    fill_top = slot_y + pad + (inner_h - fill_h)
    draw.rounded_rectangle(
        (slot_x + pad, fill_top, slot_x + pad + inner_w, slot_y + pad + inner_h),
        radius=inner_w / 2,
        fill=(52, 211, 133, 255),
    )

    return image.resize((size, size), Image.Resampling.LANCZOS)


if __name__ == "__main__":
    sizes = (16, 24, 32, 48, 64, 96, 128, 256)
    images = [make_icon(size) for size in sizes]
    images[-1].save("app_icon.ico", format="ICO", sizes=[(size, size) for size in sizes])
    images[-1].save("icon_preview.png")
