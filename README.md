# Framework
```
Calendar
|-- background : folder PC背景の元画像の格納場所。0枚以上の画像を入れる。
|-- calendar   : folder save_calendar.py の実行により保存される、PC背景の格納場所。
|-- schedule   : folder json 形式の予定を格納する。main.py により、もしくは直に編集する。
|-- settings.json     : file main.py で用いる設定を記述している。
|-- _load_settings.py : file settings.json を読み込む。
|-- save_calendar.py  : file schedule と background から背景画像を作成、calendar に格納する。
|-- main.py           : file 
|-- others
```
# About Game class
## self.screen
表示されるwindow. settings.json の screen_size の値でその大きさを決める。
## layout
screen : window 全体
pallet : 数値処理をほどこした後の描画していく区域。