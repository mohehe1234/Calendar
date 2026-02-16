from _load_settings import _settings
import pygame
from pathlib import Path
import sys
import itertools
from collections import defaultdict
import json
import datetime
import calendar
calendar.setfirstweekday(calendar.SUNDAY)
pygame.key.ScancodeWrapper

class Game():
    def __init__(self,
                 settings : dict = _settings):
        pygame.init()
        # # 押下され続ける状態を取得
        pygame.key.set_repeat(200)
        pygame.display.set_caption("Main Menu")
        self.settings : dict = settings # 広く使用する
        self.screen : pygame.Surface = pygame.display.set_mode(self.settings["screen_size"]) # 広く使用する
        self.paused : bool = False # event
        self.selected_bg : int = 0 # event と run
        self.schedules : dict[str,defaultdict[str,str]] = self.load_schedules() # event
        layout : tuple[int,int,int,int,int,int,int,int,int,int,int] = self.calc_layout() # display のサイズを settings.json から変更したら Game のインスタンス化を再度し直す必要がある。
        layout_surf_with_pos : tuple[pygame.Surface,tuple[int,int]] = self.mk_layout_surf(layout)
        bg_surfs_with_pos : list[tuple[pygame.Surface,tuple[int,int]]] = self.load_bg()
        now : datetime.datetime = datetime.datetime.now()
        self.calendar_year :int = now.year
        self.calendar_month : int = now.month
        self.calendar_day : int = now.day
        self.run(layout, layout_surf_with_pos, bg_surfs_with_pos)

    def load_schedules(self) -> dict[str,defaultdict[str,str]]:
        schedule_pathes : list[Path] = Path(self.settings["s_dir"]).glob("*.json")
        schedules : dict = {}
        for path in schedule_pathes:
            with open(path,mode="r",encoding="utf-8") as f:
                schedule = json.load(f)
            schedules[path.name] = defaultdict(str, schedule)
        return schedules

    def load_bg(self) -> list[tuple[pygame.Surface,tuple[int,int]]]:
        """
        画像の読み込みとSurfaceの作成は先にしておく。
        描画は while 文の中で行うので、初期化時にできる作業は先にしておく。
        """
        bg_pathes : list[Path] = list(Path(self.settings["b_dir"]).glob('*.*'))
        bg_surfs : list[tuple[pygame.Surface,tuple[int,int]]] = []
        for path in bg_pathes:
            screen_w, screen_h = self.screen.get_size()
            bg_surf : pygame.Surface = pygame.image.load(path).convert()
            img_w, img_h = bg_surf.get_size()
            scale = min(screen_w / img_w, screen_h / img_h)
            new_size = (int(img_w * scale), int(img_h * scale))
            bg_surf = pygame.transform.smoothscale(bg_surf, new_size)
            x = (screen_w - new_size[0]) // 2
            y = (screen_h - new_size[1]) // 2
            bg_surfs.append((bg_surf,(x,y)))
        return bg_surfs

    def calc_layout(self) -> dict[str, int]:
        screen_width, screen_height = self.screen.get_size()
        margin : int = self.settings["margin"]
        pallet_ratio = self.settings["pallet_ratio"][1]/self.settings["pallet_ratio"][0]
        if screen_height <= screen_width:
            long_side = screen_width
            short_side = screen_height
        else:
            long_side = screen_height
            short_side = screen_width
        if short_side - 2*margin <= int((long_side - 3*margin)//(1 + pallet_ratio)):
            calendar_length = short_side - 2*margin
        else:
            calendar_length = int((long_side - 3*margin)//(1 + pallet_ratio))
        long_side_pallet = int(calendar_length*(1 + pallet_ratio) + 3*margin)
        short_side_pallet = calendar_length + 2*margin
        long_side_pos = (long_side - long_side_pallet)//2
        short_side_pos = (short_side - short_side_pallet)//2
        focused_long_side_pos = long_side_pos + calendar_length + margin
        focused_short_side_pos = short_side_pos + margin
        x_pos : int
        y_pos : int
        focused_x_pos : int
        focused_y_pos : int
        focused_length : int = int(calendar_length * pallet_ratio)
        if screen_height <= screen_width:
            x_pos, y_pos = long_side_pos, short_side_pos
            focused_x_pos, focused_y_pos = focused_long_side_pos, focused_short_side_pos
        else:
            y_pos, x_pos = long_side_pos, short_side_pos
            focused_y_pos, focused_x_pos = focused_long_side_pos, focused_short_side_pos
        calendar_ratio : list[int,int,int] = self.settings["calendar_ratio"]
        sum_ratio = calendar_ratio[0] + (calendar_ratio[1] + calendar_ratio[2]) * 6
        week_height, date_height, content_height = (calendar_length * ratio // sum_ratio for ratio in calendar_ratio)
        date_width = calendar_length // 7
        return (calendar_length,
                x_pos,
                y_pos,
                week_height,
                date_height,
                content_height,
                date_width,
                margin,
                focused_x_pos,
                focused_y_pos,
                focused_length)
        
    def mk_layout_surf(self,
                       layout : tuple[int,int,int,int,int,int,int,int,int,int,int]) -> tuple[pygame.Surface,tuple[int,int]]:
        # 曜日の font_size を枠に合わせて変更してもよい。
        calendar_length, x_pos, y_pos, week_height, date_height, content_height, date_width, margin, focused_x_pos, focused_y_pos, focused_length = layout
        # 透過surface を作りそこに線を描いていく。
        sub_screen_surface = pygame.Surface(self.screen.get_size())
        sub_screen_surface.fill((255,255,255))
        sub_screen_surface.set_colorkey((255,255,255))
        pygame.draw.line(sub_screen_surface, (0,0,0), (x_pos,y_pos), (x_pos+date_width*7,y_pos))
        for i in range(7):
            pygame.draw.line(sub_screen_surface, (0,0,0), 
                             (x_pos,y_pos+week_height+(date_height+content_height)*i),
                             (x_pos+date_width*7,y_pos+week_height+(date_height+content_height)*i))
        for i in range(8):
            pygame.draw.line(sub_screen_surface, (0,0,0), 
                             (x_pos+date_width*i,y_pos),
                             (x_pos+date_width*i,y_pos+week_height+(date_height+content_height)*6))
        DoW_font_size = self.settings["DoW_font_size"]
        # 縦幅にFoW_font が収まりきらない場合、date_heightに合わせる
        if date_height < DoW_font_size:
            DoW_font_size = date_height
        DoW_font = pygame.font.SysFont(self.settings["DoW_font"],DoW_font_size)
        for i, day_of_week in enumerate(["日","月","火","水","木","金","土"]):
            self.draw_text(sub_screen_surface, day_of_week, x_pos+(date_width-DoW_font_size)//2+date_width*i, y_pos+(week_height-DoW_font_size)//2, font=DoW_font)     
        return (sub_screen_surface, (0,0))

    def run(self,
            layout : tuple[int,int,int,int,int,int,int,int,int,int,int],
            layout_surf_with_pos : tuple[pygame.Surface,tuple[int,int]],
            bg_surfs_with_pos : list[tuple[pygame.Surface,tuple[int,int]]]):
        while True:
            # self.screen の初期化
            self.screen.fill((255,255,255))
            # load_bg で読み込んだ画像の描画
            if bg_surfs_with_pos:
                self.screen.blit(bg_surfs_with_pos[self.selected_bg][0], bg_surfs_with_pos[self.selected_bg][1])
            else:
                self.screen.fill((255,255,255))
            # layout surface の描画
            self.screen.blit(layout_surf_with_pos[0], layout_surf_with_pos[1])
            # schedule の描画
            self.draw_schedule(layout)
            # # paused の描画
            # if self.paused == True:
            #     self.draw_text(self.screen, "paused", 100, 100, font=pygame.font.SysFont(self.settings["font"], 40))
            self.handle_events(pygame.event.get(), bg_surfs_with_pos)
            # self.handle_key_pressed(pygame.key.get_pressed())
            pygame.display.update()

    def draw_schedule(self,
                      layout : tuple[int,int,int,int,int,int,int,int,int,int,int]):
        calendar_length, x_pos, y_pos, week_height, date_height, content_height, date_width, margin, focused_x_pos, focused_y_pos, focused_length = layout
        color : tuple[int,int,int]
        monthcalendar = calendar.monthcalendar(self.calendar_year, self.calendar_month)
        DoW_font_size = self.settings["DoW_font_size"]
        # 縦幅にFoW_font が収まりきらない場合、date_heightに合わせる
        if date_height < DoW_font_size:
            DoW_font_size = date_height
        DoW_font = pygame.font.SysFont(self.settings["DoW_font"],DoW_font_size)
        font_size = self.settings["font_size"]
        # if date_height < font_size:
        #     font_size = date_height*2
        font = pygame.font.SysFont(self.settings["font"],font_size)
        month_font_size = self.settings["Month_font_size"]
        if month_font_size > focused_length//7:
            month_font_size = focused_length//7
        month_font = pygame.font.SysFont(self.settings["Month_font"],month_font_size)
        today = "".join(str(datetime.date.today()).split("-"))
        for i in range(len(monthcalendar)):
            for j in range(len(monthcalendar[i])):
                if j == 0:
                    color = (255,0,0)
                elif today == str(self.calendar_year).zfill(4)+str(self.calendar_month).zfill(2)+str(monthcalendar[i][j]).zfill(2):
                    color = (255,0,255)
                else:
                    color = (0,0,0)
                if monthcalendar[i][j] != 0:
                    self.draw_text(self.screen,
                                   str(monthcalendar[i][j]),
                                   x_pos+date_width*(j+1)-DoW_font_size,
                                   y_pos+week_height+(date_height-DoW_font_size)//2+(date_height+content_height)*i,
                                   DoW_font,
                                   color
                                   )
        for key, schedule in self.schedules.items():
            color = tuple([int(i) for i in schedule["color"].split(",")])
            for i in range(len(monthcalendar)):
                for j in range(len(monthcalendar[i])):
                    day = str(self.calendar_year).zfill(4)+str(self.calendar_month).zfill(2)+str(monthcalendar[i][j]).zfill(2)
                    self.place_text(self.screen,
                                    schedule[day],
                                    x_pos+date_width*j+2,
                                    y_pos+week_height+date_height+(date_height+content_height)*i,
                                    font,
                                    font_size,
                                    date_width,
                                    content_height,
                                    color
                                    )
        color = (0,0,0)
        self.draw_text(self.screen,
                       str(self.calendar_year)+"年"+str(self.calendar_month).zfill(2)+"月"+str(self.calendar_day).zfill(2)+"日",
                       focused_x_pos,focused_y_pos,month_font,color)
            # 今表示している年月を取得したうえで、そのschedule を描画する。
        date = str(self.calendar_year).zfill(4)+str(self.calendar_month).zfill(2)+str(self.calendar_day).zfill(2)
        self.place_text(self.screen,
                        schedule[date],
                        focused_x_pos,
                        focused_y_pos+month_font_size,
                        month_font,
                        month_font_size,
                        focused_length,
                        calendar_length,
                        color
                        )

    def place_text(self,
                   surface : pygame.Surface,
                   text : str,
                   x : int, 
                   y : int,
                   font : pygame.font.Font,
                   font_size : int,
                   pallet_width : int,
                   pallet_height : int,
                   color : tuple):
        # 全角のwidth(半角widthの2倍)に合わせて、一行に表示する文字の最大数を決める。
        NoC = len(text)
        C_num_in_line = pallet_width // font_size
        for i in range(NoC // C_num_in_line+1):
            if i == NoC // C_num_in_line:
                self.draw_text(surface, text[C_num_in_line*i:], x, y+font_size*i+1, font, color)
            else:
                # pallet_height をこえる文章は "..."で省略とする。
                if pallet_height <= font_size*i+1 + font_size*2:
                    self.draw_text(surface, "...",  x, y+font_size*i+1, font, color)
                    break
                else:
                    self.draw_text(surface, text[C_num_in_line*i:C_num_in_line*(i+1)], x, y+font_size*i+1, font, color)

    def draw_text(self, 
                  surface : pygame.Surface,
                  text : str, 
                  x : int, 
                  y : int,
                  font : pygame.font.Font,
                  color : tuple = (0,0,0)):
        
        image = font.render(text, True, color)
        surface.blit(image, (x, y))
    
    def handle_events(self,
                      events : list[pygame.event.Event],
                      bg_surfs_with_pos : list[tuple[pygame.Surface,tuple[int,int]]]):
        def parse_keybind(instructions : str) -> tuple[int, int]:
            MOD_MAP = {
                "SHIFT": pygame.KMOD_LSHIFT,
                "CTRL": pygame.KMOD_CTRL,
                "ALT": pygame.KMOD_ALT,
                "META": pygame.KMOD_META
            }
            conf = self.settings["key"][instructions]
            key = pygame.key.key_code(conf["key"])
            mod = 0
            for m in conf.get("mod", []):
                mod |= MOD_MAP[m]
            return mod, key
        def kill_game():
            # window を出して、終了していいか確認する処理を if else で。
            sys.exit()
        for event in events:
            if event.type == pygame.QUIT: # click x button
                kill_game()
            elif event.type == pygame.KEYDOWN:
                mod_key = (event.mod,event.key)
                # 以下のようにkey をとるのが最善かわからない。
                # settings.json にキーボード情報を保存さえできればよい。
                # OSの違いを吸収できるように実装する。

                # bg_surfs_with_pos つまり読み込んだ bg がない場合は change_upper/lower_bg の処理をしない。
                if bg_surfs_with_pos:
                    if mod_key == parse_keybind("change_upper_bg"):
                        self.selected_bg = (self.selected_bg + 1) % len(list(Path(self.settings["b_dir"]).glob('*.*')))
                    if mod_key == parse_keybind("change_lowwer_bg"):
                        self.selected_bg = (self.selected_bg - 1) % len(list(Path(self.settings["b_dir"]).glob('*.*')))
                if mod_key == parse_keybind("kill_game"): # or pygame.K_ESCAPE
                    kill_game()
                if mod_key == parse_keybind("change_schedule"):
                    pass
                elif mod_key == parse_keybind("stop_game"): # or pygame.K_SPACE
                    if self.paused:
                        self.paused = False
                    else:
                        self.paused = True
                elif mod_key == parse_keybind("right"): # 右
                    self.calendar_day += 1
                    _, last_day = calendar.monthrange(self.calendar_year, self.calendar_month)
                    if self.calendar_day >= last_day:
                        self.calendar_day = 1
                        self.calendar_month += 1
                        if self.calendar_month > 12:
                            self.calendar_month = 1
                            self.calendar_year += 1
                elif mod_key == parse_keybind("left"): # 左
                    self.calendar_day -= 1
                    if self.calendar_day == 0:
                        self.calendar_month -= 1
                        if self.calendar_month == 0:
                            self.calendar_year -= 1
                            self.calendar_month = 12
                        _, self.calendar_day = calendar.monthrange(self.calendar_year, self.calendar_month)
                elif mod_key == parse_keybind("down"): # 下
                    self.calendar_month -= 1
                    if self.calendar_month == 0:
                        self.calendar_year -= 1
                        self.calendar_month = 12
                    _, self.calendar_day = calendar.monthrange(self.calendar_year, self.calendar_month)
                elif mod_key == parse_keybind("up"): # 上
                    self.calendar_day = 1
                    self.calendar_month += 1
                    if self.calendar_month > 12:
                        self.calendar_month = 1
                        self.calendar_year += 1
    # def handle_key_pressed(self,
    #                        pressed_key):
    #     def parse_keybind(instructions : str) -> tuple[int, int]:
    #         MOD_MAP = {
    #             "SHIFT": pygame.KMOD_LSHIFT,
    #             "CTRL": pygame.KMOD_CTRL,
    #             "ALT": pygame.KMOD_ALT,
    #             "META": pygame.KMOD_META
    #         }
    #         conf = self.settings["key"][instructions]
    #         key = pygame.key.key_code(conf["key"])
    #         mod = 0
    #         for m in conf.get("mod", []):
    #             mod |= MOD_MAP[m]
    #         return mod, key
    #     if pressed_key[parse_keybind("right")[1]]:
    #         self.calendar_month += 1
    #         if self.calendar_month > 12:
    #             self.calendar_month = 1
    #             self.calendar_year += 1
    #     elif pressed_key[parse_keybind("left")[1]]:
    #         self.calendar_month -= 1
    #         if self.calendar_month == 0:
    #             self.calendar_year -= 1
    #             self.calendar_month = 12

if __name__ == "__main__":
    Game(_settings)