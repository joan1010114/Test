"""PIL-based image composition for e-commerce promotional images."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"

THEMES = {
    "sunset": {
        "bg_top": (255, 243, 229),
        "bg_bottom": (255, 201, 173),
        "primary": (232, 74, 74),
        "accent": (255, 193, 60),
        "text_dark": (40, 30, 30),
        "text_light": (255, 255, 255),
        "text_muted": (120, 110, 110),
    },
    "ocean": {
        "bg_top": (232, 245, 253),
        "bg_bottom": (168, 216, 234),
        "primary": (27, 117, 188),
        "accent": (255, 180, 70),
        "text_dark": (20, 40, 60),
        "text_light": (255, 255, 255),
        "text_muted": (100, 120, 140),
    },
    "mono": {
        "bg_top": (245, 245, 245),
        "bg_bottom": (220, 220, 220),
        "primary": (30, 30, 30),
        "accent": (255, 90, 60),
        "text_dark": (30, 30, 30),
        "text_light": (255, 255, 255),
        "text_muted": (130, 130, 130),
    },
}


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


def _gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size, top)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _text_height(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for ch in text:
        probe = current + ch
        if _text_width(draw, probe, font) <= max_width:
            current = probe
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def _load_product_image(path: str | None, box: tuple[int, int]) -> Image.Image | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    img = Image.open(p).convert("RGBA")
    img.thumbnail(box, Image.LANCZOS)
    return img


def _rounded_rect(size: tuple[int, int], radius: int, fill) -> Image.Image:
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (size[0] - 1, size[1] - 1)], radius=radius, fill=fill)
    return img


def _paste_shadow(canvas: Image.Image, layer: Image.Image, pos: tuple[int, int], blur: int = 12, offset: tuple[int, int] = (0, 6)) -> None:
    shadow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.bitmap((0, 0), layer.split()[-1], fill=(0, 0, 0, 90))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(shadow, (pos[0] + offset[0], pos[1] + offset[1]))
    canvas.alpha_composite(layer, pos)


def render_square(product: dict, copy: dict, theme: str = "sunset", output: str = "output.png") -> str:
    """Render a 1080x1080 square social-media post."""
    size = (1080, 1080)
    colors = THEMES.get(theme, THEMES["sunset"])

    canvas = _gradient(size, colors["bg_top"], colors["bg_bottom"]).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    padding = 60
    image_box = (size[0] - padding * 2, 560)
    product_img = _load_product_image(product.get("image"), image_box)

    if product_img:
        card_w, card_h = image_box
        card = _rounded_rect((card_w, card_h), 40, (255, 255, 255, 255))
        _paste_shadow(canvas, card, (padding, padding), blur=24, offset=(0, 10))
        ix = padding + (card_w - product_img.width) // 2
        iy = padding + (card_h - product_img.height) // 2
        canvas.alpha_composite(product_img, (ix, iy))
    else:
        card = _rounded_rect(image_box, 40, (255, 255, 255, 255))
        _paste_shadow(canvas, card, (padding, padding), blur=24, offset=(0, 10))
        placeholder_font = _font(64)
        ph_text = product.get("name", "商品")
        tw = _text_width(draw, ph_text, placeholder_font)
        draw.text(
            (padding + (image_box[0] - tw) // 2, padding + image_box[1] // 2 - 40),
            ph_text,
            font=placeholder_font,
            fill=colors["text_muted"],
        )

    text_top = padding + image_box[1] + 40
    name_font = _font(62)
    name = product.get("name", "")
    name_lines = _wrap_text(draw, name, name_font, size[0] - padding * 2)
    y = text_top
    for line in name_lines[:2]:
        draw.text((padding, y), line, font=name_font, fill=colors["text_dark"])
        y += 76

    tagline_font = _font(36)
    tagline = copy.get("tagline", "")
    if tagline:
        y += 6
        for line in _wrap_text(draw, tagline, tagline_font, size[0] - padding * 2)[:1]:
            draw.text((padding, y), line, font=tagline_font, fill=colors["primary"])
            y += 48

    price_font = _font(72)
    discount_font = _font(36)
    price = product.get("price")
    discount_price = product.get("discount_price")
    price_x = padding
    price_y = size[1] - padding - 100

    if discount_price is not None and price is not None:
        draw.text((price_x, price_y + 28), f"NT$ {int(discount_price):,}", font=price_font, fill=colors["primary"])
        dw = _text_width(draw, f"NT$ {int(discount_price):,}", price_font)
        orig = f"NT$ {int(price):,}"
        ox = price_x + dw + 20
        oy = price_y + 50
        draw.text((ox, oy), orig, font=discount_font, fill=colors["text_muted"])
        ow = _text_width(draw, orig, discount_font)
        draw.line([(ox, oy + 22), (ox + ow, oy + 22)], fill=colors["text_muted"], width=3)
    elif price is not None:
        draw.text((price_x, price_y + 28), f"NT$ {int(price):,}", font=price_font, fill=colors["primary"])

    cta_text = copy.get("cta") or "立即購買"
    cta_font = _font(38)
    cta_w = _text_width(draw, cta_text, cta_font) + 70
    cta_h = 76
    cta_x = size[0] - padding - cta_w
    cta_y = size[1] - padding - cta_h
    cta_btn = _rounded_rect((cta_w, cta_h), cta_h // 2, colors["primary"] + (255,))
    canvas.alpha_composite(cta_btn, (cta_x, cta_y))
    tw = _text_width(draw, cta_text, cta_font)
    th = _text_height(draw, cta_text, cta_font)
    draw.text(
        (cta_x + (cta_w - tw) // 2, cta_y + (cta_h - th) // 2 - 6),
        cta_text,
        font=cta_font,
        fill=colors["text_light"],
    )

    badge = copy.get("badge")
    if badge:
        badge_font = _font(30)
        bw = _text_width(draw, badge, badge_font) + 36
        bh = 54
        bx, by = size[0] - padding - bw, padding
        badge_img = _rounded_rect((bw, bh), bh // 2, colors["accent"] + (255,))
        canvas.alpha_composite(badge_img, (bx, by))
        tw = _text_width(draw, badge, badge_font)
        th = _text_height(draw, badge, badge_font)
        draw.text(
            (bx + (bw - tw) // 2, by + (bh - th) // 2 - 4),
            badge,
            font=badge_font,
            fill=colors["text_dark"],
        )

    canvas.convert("RGB").save(output, "PNG", optimize=True)
    return output


def render_banner(product: dict, copy: dict, theme: str = "sunset", output: str = "banner.png") -> str:
    """Render a 1200x628 landscape banner (FB/Line share style)."""
    size = (1200, 628)
    colors = THEMES.get(theme, THEMES["sunset"])

    canvas = _gradient(size, colors["bg_top"], colors["bg_bottom"]).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    padding = 50
    image_box = (520, size[1] - padding * 2)
    product_img = _load_product_image(product.get("image"), image_box)

    if product_img:
        card = _rounded_rect(image_box, 32, (255, 255, 255, 255))
        _paste_shadow(canvas, card, (padding, padding), blur=20, offset=(0, 8))
        ix = padding + (image_box[0] - product_img.width) // 2
        iy = padding + (image_box[1] - product_img.height) // 2
        canvas.alpha_composite(product_img, (ix, iy))

    text_x = padding + image_box[0] + 50
    text_w = size[0] - text_x - padding

    name_font = _font(54)
    name_lines = _wrap_text(draw, product.get("name", ""), name_font, text_w)
    y = padding + 10
    for line in name_lines[:2]:
        draw.text((text_x, y), line, font=name_font, fill=colors["text_dark"])
        y += 66

    tagline_font = _font(30)
    tagline = copy.get("tagline", "")
    if tagline:
        y += 4
        for line in _wrap_text(draw, tagline, tagline_font, text_w)[:2]:
            draw.text((text_x, y), line, font=tagline_font, fill=colors["primary"])
            y += 40

    y += 10
    hl_font = _font(26)
    for hl in (copy.get("highlights") or [])[:3]:
        draw.ellipse([(text_x, y + 10), (text_x + 12, y + 22)], fill=colors["primary"])
        draw.text((text_x + 26, y), hl, font=hl_font, fill=colors["text_dark"])
        y += 40

    price_font = _font(56)
    price = product.get("price")
    discount_price = product.get("discount_price")
    price_y = size[1] - padding - 90

    if discount_price is not None and price is not None:
        draw.text((text_x, price_y), f"NT$ {int(discount_price):,}", font=price_font, fill=colors["primary"])
    elif price is not None:
        draw.text((text_x, price_y), f"NT$ {int(price):,}", font=price_font, fill=colors["primary"])

    cta_text = copy.get("cta") or "立即購買"
    cta_font = _font(30)
    cta_w = _text_width(draw, cta_text, cta_font) + 60
    cta_h = 62
    cta_x = size[0] - padding - cta_w
    cta_y = size[1] - padding - cta_h
    cta_btn = _rounded_rect((cta_w, cta_h), cta_h // 2, colors["primary"] + (255,))
    canvas.alpha_composite(cta_btn, (cta_x, cta_y))
    tw = _text_width(draw, cta_text, cta_font)
    th = _text_height(draw, cta_text, cta_font)
    draw.text(
        (cta_x + (cta_w - tw) // 2, cta_y + (cta_h - th) // 2 - 4),
        cta_text,
        font=cta_font,
        fill=colors["text_light"],
    )

    canvas.convert("RGB").save(output, "PNG", optimize=True)
    return output


LAYOUTS = {
    "square": render_square,
    "banner": render_banner,
}


def render(product: dict, copy: dict, layout: str = "square", theme: str = "sunset", output: str = "output.png") -> str:
    fn = LAYOUTS.get(layout)
    if not fn:
        raise ValueError(f"Unknown layout: {layout}. Available: {list(LAYOUTS)}")
    return fn(product, copy, theme=theme, output=output)
