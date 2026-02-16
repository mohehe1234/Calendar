import calendar
import datetime
import json
from pathlib import Path
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont
from _load_settings import _settings

def return_pallet(img_path, pwidth, pheight, location = "c"):
    '''
    pwidth と pheight サイズに画像サイズを変更する
    '''
    pallet = Image.new(mode='RGB',size=(pwidth,pheight),color=(255,255,255))
    image = Image.open(img_path)
    iwidth, iheight = image.size[0], image.size[1]
    iw_pw, ih_ph =iwidth/pwidth, iheight/pheight
    if iw_pw>1:
        if ih_ph>1:
            if iw_pw>=ih_ph:
                if iheight//iw_pw<=pheight:
                    resize=(pwidth,iheight//iw_pw)
                else:
                    resize=(pwidth,iheight//iw_pw-1)
            else:
                if iwidth//ih_ph<=pwidth:
                    resize=(iwidth//ih_ph,pheight)
                else:
                    resize=(iwidth//ih_ph-1,pheight)
        else:
            resize=(pwidth,iheight//iw_pw)
    else:
        if ih_ph>1:
            resize=(iwidth//ih_ph,pheight)
        else:
            if iw_pw>=ih_ph:
                if iheight//iw_pw<=pheight:
                    resize=(pwidth,iheight//iw_pw)
                else:
                    resize=(pwidth,iheight//iw_pw-1)
            else:
                if iwidth//ih_ph<=pwidth:
                    resize=(iwidth//ih_ph,pheight)
                else:
                    resize=(iwidth//ih_ph-1,pheight)
    resize=(int(resize[0]),int(resize[1]))
    image=image.resize(resize,Image.LANCZOS)
    if location=='L':
        loc=(0,0)
    if location=='u':
        loc=(0,0)
    if location=='c':
        loc=(int((pwidth-resize[0])//2),int((pheight-resize[1])//2))
    if location=='r':
        loc(pwidth-resize[0],pheight-resize[1])
    if location=='d':
        loc(pwidth-resize[0],pheight-resize[1])
    pallet.paste(image,loc)
    return pallet

def return_precalendar(pallet, pwidth, pheight):
    scale_per_pallet = pwidth/2160
    l,r,u,d=0,pwidth,0,pheight
    sup=d//12
    inf=d-sup
    left=(r//15)*4
    right=(r//15)*14
    if (sup-inf)//6!=0:
        inf=inf-(inf-sup)%6
    if (right-left)%7!=0:
        right=right-(right-left)%7
    s_i=(inf-sup)//6
    l_r=(right-left)//7
    #month_calendar
    draw = ImageDraw.Draw(pallet)
    font = ImageFont.truetype('msgothic.ttc', int(24*scale_per_pallet))
    draw.rectangle((left-1,sup-s_i*0.2//1-1,right+2,sup), fill='White')
    #white
    draw.line([(left,sup),(right,sup)],fill='White',width=int(4*scale_per_pallet))
    for j in range(7):
        draw.line([(left,sup+s_i*j),(right,sup+s_i*j)],fill='White',width=int(4*scale_per_pallet))
    for j in range(6):
        draw.line([(left,sup+s_i*0.2//1+s_i*j),(right,sup+s_i*0.2//1+s_i*j)],fill='White',width=int(2*scale_per_pallet))
    for i in range(8):
        draw.line([(left+l_r*i,sup),(left+l_r*i,inf+2)],fill='white',width=int(4*scale_per_pallet))
    #black
    for j in range(7):
        draw.line([(left,sup+s_i*j),(right,sup+s_i*j)],fill='Black',width=int(2*scale_per_pallet))
    for i in range(8):
        draw.line([(left+l_r*i,sup-s_i*0.2//1),(left+l_r*i,inf+1)],fill='Black',width=int(2*scale_per_pallet))
    draw.line([(left,sup-s_i*0.2//1),(right,sup-s_i*0.2//1)],fill='Black',width=int(2*scale_per_pallet))
    #moji
    weekday = ['日','月','火','水','木','金','土']
    for i in range(7):
        draw.text((left+s_i//2+l_r*i,sup-s_i*0.2//2),weekday[i],'Black',font=font,anchor='mm')
    return(pallet)

def create_changable_widgets1(pallet, pwidth, pheight, schedule_dic, year, month):
    scale_per_pallet = pwidth/2160
    draw=ImageDraw.Draw(pallet)
    font = ImageFont.truetype('HGRGE.TTC',int(20*scale_per_pallet))
    l,r,u,d=0,pwidth,0,pheight
    sup=d//12
    inf=d-sup
    left=(r//15)*4
    right=(r//15)*14
    if (sup-inf)//6!=0:
        inf=inf-(inf-sup)%6
    if (right-left)%7!=0:
        right=right-(right-left)%7
    s_i=(inf-sup)//6
    l_r=(right-left)//7
    month_list=calendar.monthcalendar(year,month)
    draw.text((left//2,sup),text=f'{year}年 {month}月',font=ImageFont.truetype('HGRSGU.TTC',int(48*scale_per_pallet)),anchor='mm',fill='Black')
    for i in range(len(month_list)):
        for j in range(len(month_list[0])):
            if month_list[i][j]!=0:
                schedule=schedule_dic[str(year)+'{:0=2}'.format(int(month))+'{:0=2}'.format(month_list[i][j])]
                draw.text((left+l_r*0.03+l_r*j,sup+s_i*0.22//1+s_i*i),text=schedule,font=font,fill='Black')
                if month_list[i][j]==datetime.date.today().day:
                    draw.text((left+l_r*4//5+l_r*j,sup+s_i*i+s_i*0.03//1),text=str(month_list[i][j]),font=ImageFont.truetype('HGRSGU.TTC',int(28*scale_per_pallet)),fill='Yellow')
                elif j==0:
                    draw.text((left+l_r*4//5+l_r*j,sup+s_i*i+s_i*0.03//1),text=str(month_list[i][j]),font=ImageFont.truetype('HGRSGU.TTC',int(28*scale_per_pallet)),fill='Red')
                else:
                    draw.text((left+l_r*4//5+l_r*j,sup+s_i*i+s_i*0.03//1),text=str(month_list[i][j]),font=ImageFont.truetype('HGRSGU.TTC',int(28*scale_per_pallet)),fill='Black')
    return pallet

def kill_files(save_dir):
    for file in save_dir.iterdir():
        if file.is_file():
            file.unlink()

def save_calendar(bg_path : Path,
                  schedule_dic : dict[dict],
                  save_dir : Path,
                  pwidth : int,
                  pheight : int):
    calendar.setfirstweekday(6)
    pallet = return_pallet(bg_path, pwidth, pheight)
    pallet = return_precalendar(pallet, pwidth, pheight)
    year = datetime.date.today().year
    month = datetime.date.today().month
    # schedule file ごとに色を変える機能とかが欲しい。
    for key, value in schedule_dic.items():
        pallet = create_changable_widgets1(pallet, pwidth, pheight, value, year, month)
    YYYYMMDD =str(year)+'{:0=2}'.format(int(month))+'{:0=2}'.format(datetime.date.today().day)
    save_path = save_dir / f"{YYYYMMDD}_{bg_path.parts[-1]}"
    kill_files(save_dir)
    pallet.save((save_path), quality=95)

# 画像だけ生成したいとき実行
if __name__ == "__main__":
    # iterdirかワイルドカードか考える
    schedule_dic : dict[defaultdict] = {}
    for path in Path(_settings["s_dir"]).iterdir():
        with open(path, mode="r", encoding="utf-8") as f:
            schedule_dic[path.stem] = defaultdict(str,json.load(f))
    for b_path in Path(_settings["b_dir"]).iterdir():
        save_calendar(b_path, schedule_dic, Path(_settings["c_dir"]), 2160, 1440)