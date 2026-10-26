from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, random
random.seed(7)
B="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; R="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
V=(124,92,255); T=(0,224,198); BG=(7,7,15)

def glow_layer(size, draw_fn, blur):
    l=Image.new("RGBA",size,(0,0,0,0)); draw_fn(ImageDraw.Draw(l)); return l.filter(ImageFilter.GaussianBlur(blur))

def background(W,H):
    img=Image.new("RGB",(W,H),BG)
    for (cx,cy,r,col,a) in [(W*0.12,H*0.15,H*0.9,V,90),(W*0.9,H*0.95,H*0.95,T,70),(W*0.55,H*0.4,H*0.5,V,35)]:
        l=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(l)
        d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=col+(a,)); l=l.filter(ImageFilter.GaussianBlur(r*0.45))
        img=Image.alpha_composite(img.convert("RGBA"),l).convert("RGB")
    # сетка
    d=ImageDraw.Draw(img,"RGBA")
    for x in range(0,W,60): d.line([(x,0),(x,H)],fill=(255,255,255,8))
    for y in range(0,H,60): d.line([(0,y),(W,y)],fill=(255,255,255,8))
    return img

def chart(img, x0,y0,x1,y1, n=40):
    W,H=img.size; pts=[]; v=0.5
    for i in range(n):
        v+=random.uniform(-0.09,0.12)+0.012; v=min(max(v,0.08),0.95)
        pts.append((x0+(x1-x0)*i/(n-1), y1-(y1-y0)*v))
    def fill(d):
        poly=pts+[(x1,y1),(x0,y1)]; d.polygon(poly,fill=V+(70,))
    img_rgba=img.convert("RGBA"); img_rgba=Image.alpha_composite(img_rgba,glow_layer(img.size,fill,0))
    gl=glow_layer(img.size,lambda d:d.line(pts,fill=T+(255,),width=10,joint="curve"),14)
    img_rgba=Image.alpha_composite(img_rgba,gl)
    d=ImageDraw.Draw(img_rgba); d.line(pts,fill=(160,255,240,255),width=4,joint="curve")
    ex,ey=pts[-1]; d.ellipse([ex-9,ey-9,ex+9,ey+9],fill=(255,255,255,255))
    return img_rgba.convert("RGB")

def coin(img, cx,cy,r,sym,col):
    W,H=img.size; base=img.convert("RGBA")
    base=Image.alpha_composite(base,glow_layer(img.size,lambda d:d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=col+(190,)),r*0.5))
    d=ImageDraw.Draw(base)
    d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=(18,18,38,255),outline=col+(255,),width=max(3,r//14))
    d.ellipse([cx-r*0.82,cy-r*0.82,cx+r*0.82,cy+r*0.82],outline=col+(120,),width=2)
    f=ImageFont.truetype(B,int(r*(1.0 if len(sym)==1 else 0.62)))
    d.text((cx,cy),sym,font=f,fill=(255,255,255,255),anchor="mm")
    return base.convert("RGB")

def text_glow(img,xy,txt,size,anchor="lm"):
    f=ImageFont.truetype(B,size)
    l=glow_layer(img.size,lambda d:d.text(xy,txt,font=f,fill=V+(255,),anchor=anchor),22)
    base=Image.alpha_composite(img.convert("RGBA"),l); d=ImageDraw.Draw(base)
    d.text(xy,txt,font=f,fill=(255,255,255,255),anchor=anchor); return base.convert("RGB")

# ---------- БАННЕР 1280x640 ----------
W,H=1280,640
img=background(W,H); img=chart(img,700,250,1250,610,30)
for sym,cx,cy,r,col in [("$",1010,120,62,T),("₽",1170,190,46,V),("₿",830,110,46,(255,170,60)),("TON",1175,70,34,(60,170,255)),("€",760,215,34,(120,255,170))]:
    img=coin(img,cx,cy,r,sym,col)
img=text_glow(img,(70,200),"CIS Rates",96)
d=ImageDraw.Draw(img)
d.text((74,285),"Курсы валют и крипто СНГ",font=ImageFont.truetype(B,32),fill=(225,228,255),anchor="lm")
d.text((74,335),"Каждые 5 минут · 12 стран · ТОП-20 монет",font=ImageFont.truetype(R,25),fill=(139,143,176),anchor="lm")
rows=["UZ RU KZ UA BY AM".split(),"AZ GE KG TJ MD TM".split()]
for ri,row in enumerate(rows):
    x=74; y=395+ri*58
    for c in row:
        w=d.textlength(c,font=ImageFont.truetype(B,22))+34
        d.rounded_rectangle([x,y,x+w,y+44],radius=22,fill=(255,255,255,18),outline=(255,255,255,60))
        d.text((x+w/2,y+22),c,font=ImageFont.truetype(B,22),fill=(238,240,255),anchor="mm"); x+=w+10
d.rounded_rectangle([74,535,404,597],radius=31,fill=T)
d.text((239,566),"@Well_Currency_bot",font=ImageFont.truetype(B,28),fill=(5,10,20),anchor="mm")
img.save("docs/assets/banner.png")

# ---------- АВАТАР 640x640 ----------
S=640; a=background(S,S); a=chart(a,60,300,S-60,560,24)
a=coin(a,S//2,250,150,"$",T); a=coin(a,150,150,58,"₽",V); a=coin(a,500,140,58,"₿",(255,170,60))
a=text_glow(a,(S//2,560),"CIS Rates",72,"mm")
# круглая маска не нужна — Telegram обрежет сам
a.save("docs/assets/avatar_old_generated.png")  # логотип проекта: круглая планета (avatar.png), этот файл его не трогает
print("done")
