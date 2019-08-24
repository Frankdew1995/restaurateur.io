# from PIL import Image, ImageDraw, ImageFont
#
# from PIL import Image
#
# from pathlib import Path
# from app import app
#
#
# font_ttf = str(Path(app.root_path) / 'static'
#                / 'fonts' / 'OpenSans-Bold.ttf')
#
# img = Image.new('RGB', (60, 60), color="white")
#
# w, h = img.size
#
# d = ImageDraw.Draw(img)
#
# fnt = ImageFont.truetype(font_ttf, 3)
#
# w_text, h_text = d.textsize("A1", font=fnt)
#
# d.text(((w-w_text)/2, (h-h_text)/2), "A1", fill="black")
#
# qrcode = Image.open("A1_1.png")
#
# w_qrcode, h_qrcode = qrcode.size
#
# qrcode.paste(img, ((w_qrcode-w)//2, (h_qrcode-h)//2))
#
# qrcode.save("test.png")
#
#
