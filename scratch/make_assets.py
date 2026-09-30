import base64
from PIL import Image

# 1. Full logo
logo = Image.open('static/logo.png')

# 2. Square mark 512x512
mark = Image.open('scratch/mark_full_512.png')
mark.save('static/mark.png')

# 3. Favicon sizes
fav32 = mark.resize((32, 32), Image.Resampling.LANCZOS)
fav32.save('static/favicon.png')
fav32.save('static/favicon.ico', format='ICO')

# 4. Generate static/mark.svg that embeds the transparent logo with viewBox
with open('static/mark.png', 'rb') as f:
    b64_mark = base64.b64encode(f.read()).decode('utf-8')

with open('static/logo.png', 'rb') as f:
    b64_logo = base64.b64encode(f.read()).decode('utf-8')

# mark.svg (square viewBox for icon usage)
svg_mark = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <image href="data:image/png;base64,{b64_mark}" x="0" y="0" width="512" height="512" preserveAspectRatio="xMidYMid meet"/>
</svg>
'''
with open('static/mark.svg', 'w', encoding='utf-8') as f:
    f.write(svg_mark)

# logo.svg (horizontal viewBox for wide usage)
svg_logo = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {logo.width} {logo.height}" width="100%" height="100%">
  <image href="data:image/png;base64,{b64_logo}" x="0" y="0" width="{logo.width}" height="{logo.height}" preserveAspectRatio="xMidYMid meet"/>
</svg>
'''
with open('static/logo.svg', 'w', encoding='utf-8') as f:
    f.write(svg_logo)

print('Generated mark.png, mark.svg, logo.svg, favicon.png, favicon.ico successfully!')
