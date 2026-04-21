"""Generate a simple placeholder product image for testing."""
from PIL import Image, ImageDraw

SIZE = (800, 800)
img = Image.new("RGBA", SIZE, (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

cx, cy = SIZE[0] // 2, SIZE[1] // 2
draw.ellipse([(cx - 220, cy - 220), (cx + 220, cy + 220)], fill=(30, 30, 40, 255))
draw.ellipse([(cx - 180, cy - 180), (cx + 180, cy + 180)], fill=(60, 60, 70, 255))
draw.ellipse([(cx - 120, cy - 120), (cx + 120, cy + 120)], fill=(20, 20, 25, 255))
draw.ellipse([(cx - 60, cy - 60), (cx + 60, cy + 60)], fill=(140, 140, 150, 255))
draw.ellipse([(cx - 80, cy - 200), (cx - 60, cy - 60)], fill=(30, 30, 40, 255))
draw.ellipse([(cx + 60, cy - 200), (cx + 80, cy - 60)], fill=(30, 30, 40, 255))

img.save("examples/placeholder.png")
print("examples/placeholder.png")
