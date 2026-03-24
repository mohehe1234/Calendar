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
        """
        self.screen に対して、run func で、 bg_surf -> preremdered_surf -> 他 の順に描画する。
        """
        pygame.init()
        # 押下され続ける状態を取得parse_keybind でない
        pygame.key.set_repeat(200)
        pygame.display.set_caption("Main Menu")
        self.settings : dict = settings # 広く使用する 変更した時点で、インスタンス化からやり直し
        self.screen : pygame.Surface = pygame.display.set_mode(self.settings["screen_size"])
        self.selected_bg : int = 0
        self.schedules : dict[str,defaultdict[str,str]] = self.load_schedules() # event
        layout : dict[str,int] = self.calc_layout() # display のサイズを settings.json から変更したら Game のインスタンス化を再度し直す必要がある。
        prerendered_surf_with_pos : tuple[pygame.Surface,tuple[int,int]] = self.prerender_surface(layout)
        bg_surfs_with_pos : list[tuple[pygame.Surface,tuple[int,int]]] = self.load_bg()
        now : datetime.datetime = datetime.datetime.now()
        self.calendar_year :int = now.year
        self.calendar_month : int = now.month
        self.calendar_day : int = now.day
        self.run(layout, prerendered_surf_with_pos, bg_surfs_with_pos)

    def load_schedules(self) -> dict[str,defaultdict[str,str]]:
        schedule_pathes : list[Path] = Path(self.settings["s_dir"]).glob("*.json")
        schedules : dict = {}
        for path in schedule_pathes:
            with open(path,mode="r",encoding="utf-8") as f:
                schedule = json.load(f)
            # 当初は path.name をkey としていたが、カレンダーに表示する際に冗長になってしまうので、 path.stem とした。
            schedules[path.stem] = defaultdict(str, schedule)
        return schedules

    def calc_layout(self) -> dict[str,int]:
        """
        s  : screen
        p  : pallet
        mc : month calendar
        dc : daily calendar
        """
        s_width, s_height = self.screen.get_size()
        margin : int = self.settings["margin"]
        mc_dc_ratio = self.settings["mc_dc_ratio"][1]/self.settings["mc_dc_ratio"][0]
        calendar_component_ratio : list[int,int,int] = self.settings["calendar_component_ratio"]

        if s_height <= s_width:
            s_long_side_length = s_width
            s_short_side_length = s_height
        else:
            s_long_side_length = s_height
            s_short_side_length = s_width
        if s_short_side_length - 2*margin <= int((s_long_side_length - 3*margin)//(1 + mc_dc_ratio)):
            mc_length = int(((s_short_side_length - 2*margin)//7)*7)
        else:
            mc_length = int((((s_long_side_length - 3*margin)//(1 + mc_dc_ratio))//7)*7)
        p_long_side_length = int((mc_length*(1 + mc_dc_ratio) + 3*margin)//1)
        p_short_side_length = mc_length + 2*margin
        p_long_side_pos_on_s = (s_long_side_length - p_long_side_length)//2
        p_short_side_pos_on_s = (s_short_side_length - p_short_side_length)//2
        dc_long_side_pos_on_s = p_long_side_pos_on_s + mc_length + margin*2
        dc_short_side_pos_on_s = p_short_side_pos_on_s + margin
        mc_x_pos : int
        mc_y_pos : int
        dc_x_pos : int
        dc_y_pos : int
        dc_short_side_length : int = int(mc_length * mc_dc_ratio)
        if s_height <= s_width:
            mc_x_pos, mc_y_pos = p_long_side_pos_on_s, p_short_side_pos_on_s
            dc_x_pos, dc_y_pos = dc_long_side_pos_on_s, dc_short_side_pos_on_s
        else:
            mc_y_pos, mc_x_pos = p_long_side_pos_on_s, p_short_side_pos_on_s
            dc_y_pos, dc_x_pos = dc_long_side_pos_on_s, dc_short_side_pos_on_s
        sum_ratio = calendar_component_ratio[0] + (calendar_component_ratio[1] + calendar_component_ratio[2]) * 6
        week_height, date_height, content_height = (mc_length * ratio // sum_ratio for ratio in calendar_component_ratio)
        week_height = mc_length - (date_height + content_height)*6
        date_width = int(mc_length // 7)
        return {"mc_length" : mc_length,
                "mc_x_pos" : mc_x_pos,
                "mc_y_pos" : mc_y_pos,
                "week_height" : week_height,
                "date_height" : date_height,
                "content_height" : content_height,
                "date_width" : date_width,
                "dc_x_pos" : dc_x_pos,
                "dc_y_pos" : dc_y_pos,
                "dc_short_side_length" : dc_short_side_length}
        
    def prerender_surface(self,
                       layout : dict[str,int]) -> tuple[pygame.Surface,tuple[int,int]]:
        """
        透過surface に、
        month calendar の縦横の線を引き、
        week 部分に曜日を格納し、
        そのsurface を返す。
        """
        # 曜日の font_size を枠に合わせて変更してもよい。
        mc_length = layout["mc_length"]
        mc_x_pos = layout["mc_x_pos"]
        mc_y_pos = layout["mc_y_pos"]
        week_height = layout["week_height"]
        date_height = layout["date_height"]
        content_height = layout["content_height"]
        date_width = layout["date_width"]
        mcw_font_size, mcw_font_name = self.settings["mcw_font"]

        if date_height < mcw_font_size:
            mcw_font_size = date_height
        mcw_font = pygame.font.SysFont(mcw_font_name,mcw_font_size)

        # 透過surface を作りそこに線を描いていく。
        surface = pygame.Surface(self.screen.get_size())
        surface.fill((255,255,255))
        surface.set_colorkey((255,255,255))
        pygame.draw.line(surface, (0,0,0), (mc_x_pos,mc_y_pos), (mc_x_pos+mc_length,mc_y_pos))
        for i in range(7):
            pygame.draw.line(surface, (0,0,0), 
                             (mc_x_pos,mc_y_pos+week_height+(date_height+content_height)*i),
                             (mc_x_pos+date_width*7,mc_y_pos+week_height+(date_height+content_height)*i))
        for i in range(8):
            pygame.draw.line(surface, (0,0,0), 
                             (mc_x_pos+date_width*i,mc_y_pos),
                             (mc_x_pos+date_width*i,mc_y_pos+week_height+(date_height+content_height)*6))

        for i, day_of_week in enumerate(["日","月","火","水","木","金","土"]):
            self.draw_text(surface, day_of_week, mc_x_pos+(date_width-mcw_font_size)//2+date_width*i, mc_y_pos+(week_height-mcw_font_size)//2, font=mcw_font)     
        return (surface, (0,0))

    def load_bg(self) -> list[tuple[pygame.Surface,tuple[int,int]]]:
        """
        画像の読み込みとSurfaceの作成は先にしておく。
        描画は while 文の中で行うので、初期化時にできる作業は先にしておく。
        """
        bg_pathes : list[Path] = list(Path(self.settings["b_dir"]).glob('*.*'))
        bg_surfs_with_pos : list[tuple[pygame.Surface,tuple[int,int]]] = []
        for path in bg_pathes:
            s_width, s_height = self.screen.get_size()
            bg_surf : pygame.Surface = pygame.image.load(path).convert()
            img_width, img_height = bg_surf.get_size()
            scale = min(s_width / img_width, s_height / img_height)
            new_size = (int(img_width * scale), int(img_height * scale))
            bg_surf = pygame.transform.smoothscale(bg_surf, new_size)
            x = (s_width - new_size[0]) // 2
            y = (s_height - new_size[1]) // 2
            bg_surfs_with_pos.append((bg_surf,(x,y)))
        return bg_surfs_with_pos

    def run(self,
            layout : dict[str,int],
            prerendered_surf_with_pos : tuple[pygame.Surface,tuple[int,int]],
            bg_surfs_with_pos : list[tuple[pygame.Surface,tuple[int,int]]]):
        while True:
            # self.screen の初期化
            self.screen.fill((255,255,255))
            # load_bg で読み込んだ画像の描画
            if bg_surfs_with_pos:
                self.screen.blit(bg_surfs_with_pos[self.selected_bg][0], bg_surfs_with_pos[self.selected_bg][1])
            # prerendered surface の描画
            self.screen.blit(prerendered_surf_with_pos[0], prerendered_surf_with_pos[1])
            # 全ての要素を描画
            self.draw_schedule(layout)
            # # paused の描画
            # if self.paused == True:
            #     self.draw_text(self.screen, "paused", 100, 100, font=pygame.font.SysFont(self.settings["font"], 40))
            self.handle_events(pygame.event.get(), bg_surfs_with_pos)
            # self.handle_key_pressed(pygame.key.get_pressed())
            pygame.display.update()

    def draw_schedule(self,
                      layout : dict[str,int]):
        mc_length = layout["mc_length"]
        mc_x_pos = layout["mc_x_pos"]
        mc_y_pos = layout["mc_y_pos"]
        week_height = layout["week_height"]
        date_height = layout["date_height"]
        content_height = layout["content_height"]
        date_width = layout["date_width"]
        dc_x_pos = layout["dc_x_pos"]
        dc_y_pos = layout["dc_y_pos"]
        dc_short_side_length = layout["dc_short_side_length"]
        mcw_font_size, mcw_font_name = self.settings["mcw_font"]
        mcc_font_size, mcc_font_name = self.settings["mcc_font"]
        dcm_font_size, dcm_font_name = self.settings["dcm_font"]
        dcc_font_size, dcc_font_name = self.settings["dcc_font"]

        if date_height < mcw_font_size:
            mcw_font_size = date_height
        mcw_font = pygame.font.SysFont(mcw_font_name,mcw_font_size)
        # if date_height < font_size:
        #     font_size = date_height*2
        mcc_font = pygame.font.SysFont(mcc_font_name,mcc_font_size)
        if dcm_font_size > dc_short_side_length//7:
            dcm_font_size = dc_short_side_length//7
        dcm_font = pygame.font.SysFont(dcm_font_name,dcm_font_size)
        mcd_font = pygame.font.SysFont(dcc_font_name,dcc_font_size)

        color : tuple[int,int,int]
        monthcalendar = calendar.monthcalendar(self.calendar_year, self.calendar_month)
        today = "".join(str(datetime.date.today()).split("-"))

        # 各mcd を描画
        for i in range(len(monthcalendar)):
            for j in range(len(monthcalendar[i])):
                if today == str(self.calendar_year).zfill(4)+str(self.calendar_month).zfill(2)+str(monthcalendar[i][j]).zfill(2):
                    color = (255,0,255)
                elif j == 0:
                    color = (255,0,0)
                else:
                    color = (0,0,0)
                if monthcalendar[i][j] != 0:
                    self.draw_text(self.screen,
                                   str(monthcalendar[i][j]),
                                   mc_x_pos+date_width*(j+1)-mcw_font_size,
                                   mc_y_pos+week_height+(date_height-mcw_font_size)//2+(date_height+content_height)*i,
                                   mcw_font,
                                   color)
        # 各mcc にschedule の描画。ただし、2file 以上のschedule に対応していない。
        for key, schedule in self.schedules.items():
            color = tuple([int(i) for i in schedule["color"].split(",")])
            for i in range(len(monthcalendar)):
                for j in range(len(monthcalendar[i])):
                    day : str = str(self.calendar_year).zfill(4)+str(self.calendar_month).zfill(2)+str(monthcalendar[i][j]).zfill(2)
                    self.place_text(self.screen,
                                    schedule[day],
                                    mc_x_pos+date_width*j+2,
                                    mc_y_pos+week_height+date_height+(date_height+content_height)*i,
                                    mcc_font,
                                    mcc_font_size,
                                    date_width,
                                    content_height,
                                    color)
        # dcm の yyyy年mm月dd日 を描画
        color = (0,0,0)
        self.draw_text(self.screen,
                       str(self.calendar_year)+"年"+str(self.calendar_month).zfill(2)+"月"+str(self.calendar_day).zfill(2)+"日",
                       dc_x_pos,
                       dc_y_pos,
                       dcm_font,
                       color)
        # dcc にschedule を描画する。ただし、2file 以上のschedule に対応していない。
        day : str = str(self.calendar_year).zfill(4)+str(self.calendar_month).zfill(2)+str(self.calendar_day).zfill(2)
        for key, schedule in self.schedules.items():
            color = tuple([int(i) for i in schedule["color"].split(",")])
            self.place_text_by_tuple(self.screen,
                            (key + ": ", schedule[day]),
                            dc_x_pos,
                            dc_y_pos+dcm_font_size,
                            mcd_font,
                            dcc_font_size,
                            dc_short_side_length,
                            mc_length,
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
        """
            for i in range(NoC // C_num_in_line+1):
                   ~~~~^^~~~~~~~~~~~~~~
        ZeroDivisionError: integer division or modulo by zero
        """
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

    def place_text_by_tuple(self,
                   surface : pygame.Surface,
                   texts : tuple[str],
                   x : int, 
                   y : int,
                   font : pygame.font.Font,
                   font_size : int,
                   pallet_width : int,
                   pallet_height : int,
                   color : tuple):
        """
            for i in range(NoC // C_num_in_line+1):
                   ~~~~^^~~~~~~~~~~~~~~
        ZeroDivisionError: integer division or modulo by zero
        """
        # tuple の要素ごとに行を変える。
        lines = 0
        for text in texts:
            print(lines)
            print(text)
            lines = self._place_text_by_tuple(surface,
                                      text,
                                      x,
                                      y,
                                      font,
                                      font_size,
                                      pallet_width,
                                      pallet_height,
                                      color,
                                      lines)

    def _place_text_by_tuple(self,
                   surface : pygame.Surface,
                   text : str,
                   x : int, 
                   y : int,
                   font : pygame.font.Font,
                   font_size : int,
                   pallet_width : int,
                   pallet_height : int,
                   color : tuple,
                   lines : int):
        """
            for i in range(NoC // C_num_in_line+1):
                   ~~~~^^~~~~~~~~~~~~~~
        ZeroDivisionError: integer division or modulo by zero
        """
        # 全角のwidth(半角widthの2倍)に合わせて、一行に表示する文字の最大数を決める。
        NoC = len(text)
        C_num_in_line = pallet_width // font_size
        for i in range(lines, NoC // C_num_in_line+1):
            if i == NoC // C_num_in_line:
                lines += 1
                self.draw_text(surface, text[C_num_in_line*i:], x, y+font_size*i+1, font, color)
                return lines+i+1
            else:
                # pallet_height をこえる文章は "..."で省略とする。
                if pallet_height <= font_size*i+1 + font_size*2:
                    self.draw_text(surface, "...",  x, y+font_size*i+1, font, color)
                    return lines+i+1
                else:
                    lines += 1
                    self.draw_text(surface, text[C_num_in_line*i:C_num_in_line*(i+1)], x, y+font_size*i+1, font, color)
    
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
                    # self.calendar_year
                    # self.calendar_month
                    # self.calendar_day

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