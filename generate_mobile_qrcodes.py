from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont


OUTPUT_DIR = Path(__file__).resolve().parent / "QRCode"
FONT_PATH = Path(r"C:\Windows\Fonts\msjh.ttc")
ITEMS = [
    ("手機任務頁", "https://lgsaleout.superb-supplies.com.tw/mobile", "LGSale_mobile_QR.png"),
    ("手機拍照頁", "https://lgsaleout.superb-supplies.com.tw/photo", "LGSale_photo_QR.png"),
]


def font(size: int):
    return ImageFont.truetype(str(FONT_PATH), size) if FONT_PATH.exists() else ImageFont.load_default()


def make_card(title: str, url: str) -> Image.Image:
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=12, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    card = Image.new("RGB", (700, 850), "white")
    qr_x = (card.width - qr_image.width) // 2
    card.paste(qr_image, (qr_x, 105))
    draw = ImageDraw.Draw(card)
    draw.text((card.width // 2, 38), title, font=font(42), fill="black", anchor="ma")
    draw.text((card.width // 2, 765), url, font=font(20), fill="#333333", anchor="ma")
    return card


OUTPUT_DIR.mkdir(exist_ok=True)
cards = []
for title, url, filename in ITEMS:
    card = make_card(title, url)
    card.save(OUTPUT_DIR / filename)
    cards.append(card)

sheet = Image.new("RGB", (1440, 850), "#eeeeee")
sheet.paste(cards[0], (10, 0))
sheet.paste(cards[1], (730, 0))
sheet.save(OUTPUT_DIR / "LGSale_mobile_QR_codes.png")
