from _load_settings import _settings
import pygame
from pathlib import Path
import sys
from collections import defaultdict
import json
import datetime
import calendar
import copy

class Mk_calendar():
    def __init__(self,
                 settings : dict = _settings):
        """
        self.screen に対して、run func で、 bg_surf -> preremdered_surf -> 他 の順に描画する。
        """
        calendar.setfirstweekday(calendar.SUNDAY)
        pygame.key.ScancodeWrapper
        pygame.init()
        pygame.key.set_repeat()
        # 押下され続ける状態を取得parse_keybind でない
        # pygame.key.set_repeat(200) # json 保存時にややこしくならないように、shchedule change でのみ使用を制限したいが
        pygame.display.set_caption("Main Menu")
        self.settings : dict = settings # 広く使用する 変更した時点で、インスタンス化からやり直し
        self.screen : pygame.Surface = pygame.display.set_mode(self.settings["screen_size"])
        self.screen_condition = "default"
        self.selected_bg : int = 0
        self.schedules : dict[str,defaultdict[str,list[str]]] = self.load_schedules() # event
        layout : dict[str,int] = self.calc_layout() # display のサイズを settings.json から変更したら Game のインスタンス化を再度し直す必要がある。
        prerendered_surf_with_pos : tuple[pygame.Surface,tuple[int,int]] = self.prerender_surface(layout)
        bg_surfs_with_pos : list[tuple[pygame.Surface,tuple[int,int]]] = self.load_bg()
        now : datetime.datetime = datetime.datetime.now()
        self.calendar_year :int = now.year
        self.calendar_month : int = now.month
        self.calendar_day : int = now.day
        button_descriptions = self.mk_button_descriptions()

        self.selected_schedule : list[int|list[str]] = [0,[i for i in self.schedules]]
        self.temp_schedules : dict[str,defaultdict[str,list[str]]]
        self.editing_text : str = ""
        self.running : bool = True

        self.layout = layout
        self.prerendered_surf_with_pos = prerendered_surf_with_pos
        self.bg_surfs_with_pos =  bg_surfs_with_pos
        self.button_descriptions = button_descriptions

    def load_schedules(self) -> dict[str,defaultdict[str,str]]:
        """
        surface.blit()の特性上、改行コードを操作する必要がでてくる。
        osによる改行コードの違いを吸収するのが面倒なので、
        schedule.json のvalue を array にすることで、要素ごとに改行するようにする。

        あとでjson schema と validation する

        color を string から array に変更した部分の修正
        string を array に変更した部分の修正
        """
        schedule_pathes : list[Path] = Path(self.settings["s_dir"]).glob("*.json")
        schedules : dict[str,defaultdict[str,list[str]]] = {}
        for path in schedule_pathes:
            with open(path,mode="r",encoding="utf-8") as f:
                schedule = json.load(f)
            # 当初は path.name をkey としていたが、カレンダーに表示する際に冗長になってしまうので、 path.stem とした。
            schedules[path.stem] = defaultdict(list, schedule)
        return schedules
    def save_schedules(self,
                       schedule_pathes : Path,
                       schedule : dict):
        with open(schedule_pathes, mode="w", encoding="utf-8") as f:
            json.dump(schedule, f, indent=2)


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
        dc_be_ratio = self.settings["dc_be_ratio"][0]/(self.settings["dc_be_ratio"][0] + self.settings["dc_be_ratio"][1])

        width_is_big = s_height <= s_width
        if width_is_big:
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
        be_x_pos : int
        be_y_pos : int
        dc_short_side_length : int = int((mc_length * mc_dc_ratio)//1)
        dc_long_side_length : int = int((mc_length * dc_be_ratio)//1)
        be_long_side_length : int = int((mc_length * (1 - dc_be_ratio))//1)
        if width_is_big:
            mc_x_pos, mc_y_pos = p_long_side_pos_on_s, p_short_side_pos_on_s
            dc_x_pos, dc_y_pos = dc_long_side_pos_on_s, dc_short_side_pos_on_s
            be_x_pos, be_y_pos = dc_x_pos, dc_y_pos + dc_long_side_length + margin
        else:
            mc_y_pos, mc_x_pos = p_long_side_pos_on_s, p_short_side_pos_on_s
            dc_y_pos, dc_x_pos = dc_long_side_pos_on_s, dc_short_side_pos_on_s
            be_x_pos, be_y_pos = dc_x_pos + dc_long_side_length + margin, dc_y_pos
        sum_ratio = calendar_component_ratio[0] + (calendar_component_ratio[1] + calendar_component_ratio[2]) * 6
        week_height, date_height, content_height = (mc_length * ratio // sum_ratio for ratio in calendar_component_ratio)
        week_height = mc_length - (date_height + content_height)*6
        date_width = int(mc_length // 7)

        return {"width_is_big" : width_is_big,
                "mc_length" : mc_length,
                "mc_x_pos" : mc_x_pos,
                "mc_y_pos" : mc_y_pos,
                "week_height" : week_height,
                "date_height" : date_height,
                "content_height" : content_height,
                "date_width" : date_width,
                "dc_x_pos" : dc_x_pos,
                "dc_y_pos" : dc_y_pos,
                "dc_short_side_length" : dc_short_side_length,
                "dc_long_side_length" : dc_long_side_length,
                "be_x_pos" : be_x_pos,
                "be_y_pos" : be_y_pos,
                "be_long_side_length" : be_long_side_length,}
        
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
        surface.fill((255,255,255)) # 背景を白に
        surface.set_colorkey((255,255,255)) # 白を透明に
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

    def mk_button_descriptions(self) -> defaultdict[str,list[str]]:
        button_descriptions : defaultdict[str,list[str]]
        button_descriptions = defaultdict(list)
        for key in self.settings["key"].keys():
            button_description : str = ""
            for i in self.settings["key"][key]["mod"]:
                button_description += i+"+"
            button_description = button_description + self.settings["key"][key]["key"] + " : " + key
            if key[:3] == "cs_":
                button_descriptions["change_schedule"].append(button_description)
            elif key[:3] == "ss_":
                button_descriptions["select_schedule"].append(button_description)
            else:
                button_descriptions["default"].append(button_description)
        return button_descriptions

    def run(self,
            layout : dict[str,int],
            prerendered_surf_with_pos : tuple[pygame.Surface,tuple[int,int]],
            bg_surfs_with_pos : list[tuple[pygame.Surface,tuple[int,int]]],
            button_descriptions : dict[str,list[str]]):
        while True:
            # self.screen の初期化
            self.screen.fill((255,255,255))
            # load_bg で読み込んだ画像の描画
            if bg_surfs_with_pos:
                self.screen.blit(bg_surfs_with_pos[self.selected_bg][0], bg_surfs_with_pos[self.selected_bg][1])
            # prerendered surface の描画
            self.screen.blit(prerendered_surf_with_pos[0], prerendered_surf_with_pos[1])
            # 全ての要素を描画
            self.draw_schedule(layout,button_descriptions)
            # # paused の描画
            # if self.paused == True:
            #     self.draw_text(self.screen, "paused", 100, 100, font=pygame.font.SysFont(self.settings["font"], 40))
            self.handle_events(pygame.event.get(), bg_surfs_with_pos, layout)
            # self.handle_key_pressed(pygame.key.get_pressed())
            pygame.display.update()

    def draw_schedule(self,
                      layout : dict[str,int],
                      button_descriptions : dict[str,list[str]]):
        width_is_big = layout["width_is_big"]
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
        dc_long_side_length = layout["dc_long_side_length"]
        be_x_pos = layout["be_x_pos"]
        be_y_pos = layout["be_y_pos"]
        be_long_side_length = layout["be_long_side_length"]
        mcw_font_size, mcw_font_name = self.settings["mcw_font"]
        mcc_font_size, mcc_font_name = self.settings["mcc_font"]
        dcm_font_size, dcm_font_name = self.settings["dcm_font"]
        dcc_font_size, dcc_font_name = self.settings["dcc_font"]
        be_font_size,  be_font_name  = self.settings["be_font"]

        if date_height < mcw_font_size:
            mcw_font_size = date_height
        mcw_font = pygame.font.SysFont(mcw_font_name,mcw_font_size)
        # if date_height < font_size:
        #     font_size = date_height*2
        mcc_font = pygame.font.SysFont(mcc_font_name,mcc_font_size)
        if width_is_big:
            if dcm_font_size > dc_short_side_length//8:
                dcm_font_size = dc_short_side_length//8
                dc_width,dc_height = dc_short_side_length, dc_long_side_length
                be_width,be_height = dc_short_side_length, be_long_side_length
        else:
            if dcm_font_size > mc_length//8:
                dcm_font_size = mc_length//8
                dc_height,dc_width = dc_short_side_length, dc_long_side_length
                be_height,be_width = dc_short_side_length, be_long_side_length
        dcm_font = pygame.font.SysFont(dcm_font_name,dcm_font_size)
        dcc_font = pygame.font.SysFont(dcc_font_name,dcc_font_size)
        be_font  = pygame.font.SysFont(be_font_name,be_font_size)

        color : tuple[int,int,int]
        monthcalendar = calendar.monthcalendar(self.calendar_year, self.calendar_month)
        today = "".join(str(datetime.date.today()).split("-"))

        # 各mcd を描画
        for i in range(len(monthcalendar)):
            for j in range(len(monthcalendar[i])):
                # self.calendar_year, month, day に合致する日付を囲う(mc)
                if str(self.calendar_year).zfill(4)+str(self.calendar_month).zfill(2)+str(self.calendar_day).zfill(2) == str(self.calendar_year).zfill(4)+str(self.calendar_month).zfill(2)+str(monthcalendar[i][j]).zfill(2):
                    color = (0,0,0)
                    line_width : int = 3
                    pygame.draw.line(self.screen, color, 
                                    (mc_x_pos+date_width*j,mc_y_pos+week_height+(date_height+content_height)*i),
                                    (mc_x_pos+date_width*(j+1),mc_y_pos+week_height+(date_height+content_height)*i),width=line_width)
                    pygame.draw.line(self.screen, color, 
                                    (mc_x_pos+date_width*j,mc_y_pos+week_height+(date_height+content_height)*(i+1)),
                                    (mc_x_pos+date_width*(j+1),mc_y_pos+week_height+(date_height+content_height)*(i+1)),width=line_width)
                    pygame.draw.line(self.screen, color, 
                                    (mc_x_pos+date_width*j,mc_y_pos+week_height+(date_height+content_height)*i),
                                    (mc_x_pos+date_width*j,mc_y_pos+week_height+(date_height+content_height)*(i+1)),width=line_width)
                    pygame.draw.line(self.screen, color, 
                                    (mc_x_pos+date_width*(j+1),mc_y_pos+week_height+(date_height+content_height)*i),
                                    (mc_x_pos+date_width*(j+1),mc_y_pos+week_height+(date_height+content_height)*(i+1)),width=line_width)
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
        # 各mcc にschedule の描画。
        mcc_lines : defaultdict[str,int] = defaultdict(int)
        for key, schedule in self.schedules.items():
            color = tuple([int(i) for i in schedule["color"]])
            for i in range(len(monthcalendar)):
                for j in range(len(monthcalendar[i])):
                    day : str = str(self.calendar_year).zfill(4)+str(self.calendar_month).zfill(2)+str(monthcalendar[i][j]).zfill(2)
                    mcc_lines[day] = self.place_text(self.screen,
                                               schedule[day],
                                               mc_x_pos+date_width*j+2,
                                               mc_y_pos+week_height+date_height+(date_height+content_height)*i,
                                               mcc_font,
                                               mcc_font_size,
                                               date_width,
                                               content_height,
                                               color,
                                               lines = mcc_lines[day])
        # dcm の yyyy年mm月dd日 を描画
        color = (0,0,0)
        self.draw_text(self.screen,
                       str(self.calendar_year)+"年"+str(self.calendar_month).zfill(2)+"月"+str(self.calendar_day).zfill(2)+"日",
                       dc_x_pos,
                       dc_y_pos,
                       dcm_font,
                       color)
        # dcc にschedule を描画する。
        color = (0,0,0)
        line_width : int = 3
        pygame.draw.line(self.screen, color, (dc_x_pos,dc_y_pos+dcm_font_size), (dc_x_pos+dc_width,dc_y_pos+dcm_font_size),width=line_width)
        pygame.draw.line(self.screen, color, (dc_x_pos,dc_y_pos+dcm_font_size), (dc_x_pos,dc_y_pos+dc_height),width=line_width)
        pygame.draw.line(self.screen, color, (dc_x_pos+dc_width,dc_y_pos+dc_height), (dc_x_pos+dc_width,dc_y_pos+dcm_font_size),width=line_width)
        pygame.draw.line(self.screen, color, (dc_x_pos+dc_width,dc_y_pos+dc_height), (dc_x_pos,dc_y_pos+dc_height),width=line_width)
        if self.screen_condition == "change_schedule":
            dcc_lines : defaultdict[str,int] = defaultdict(int)
            day : str = str(self.calendar_year).zfill(4)+str(self.calendar_month).zfill(2)+str(self.calendar_day).zfill(2)
            for key, schedule in self.temp_schedules.items():
                color = tuple([int(i) for i in schedule["color"]])
                first_line = [key + ":"]
                if schedule[day] == []:
                    schedule[day] = [""]
                last_line = [schedule[day][-1]]
                if key == self.selected_schedule[1][self.selected_schedule[0]]:
                    last_line = [last_line[0] + self.editing_text + "◀"]
                dcc_lines[day] = self.place_text(self.screen,
                                first_line + schedule[day][:-1],
                                dc_x_pos,
                                dc_y_pos+dcm_font_size,
                                dcc_font,
                                dcc_font_size,
                                dc_width,
                                dc_height,
                                color,
                                lines = dcc_lines[day])
                # editing_text の表示のみ気を遣う
                dcc_lines[day] = self.place_text(self.screen,
                                last_line,
                                dc_x_pos,
                                dc_y_pos+dcm_font_size,
                                dcc_font,
                                dcc_font_size,
                                dc_width,
                                dc_height,
                                color,
                                lines = dcc_lines[day],
                                extent = (len(last_line[0]),-1))
        elif self.screen_condition == "select_schedule":
            dcc_lines : defaultdict[str,int] = defaultdict(int)
            day : str = str(self.calendar_year).zfill(4)+str(self.calendar_month).zfill(2)+str(self.calendar_day).zfill(2)
            for key, schedule in self.schedules.items():
                color = tuple([int(i) for i in schedule["color"]])
                first_line = [key + ":"]
                if key == self.selected_schedule[1][self.selected_schedule[0]]:
                    first_line[0] += "◀"
                dcc_lines[day] = self.place_text(self.screen,
                                first_line + schedule[day],
                                dc_x_pos,
                                dc_y_pos+dcm_font_size,
                                dcc_font,
                                dcc_font_size,
                                dc_width,
                                dc_height,
                                color,
                                lines = dcc_lines[day])
        elif self.screen_condition == "default":
            dcc_lines : defaultdict[str,int] = defaultdict(int)
            day : str = str(self.calendar_year).zfill(4)+str(self.calendar_month).zfill(2)+str(self.calendar_day).zfill(2)
            for key, schedule in self.schedules.items():
                color = tuple([int(i) for i in schedule["color"]])
                first_line = [key + ":"]
                if (schedule[day] != [])  or (schedule[day] != [""]):
                    dcc_lines[day] = self.place_text(self.screen,
                                    first_line + schedule[day],
                                    dc_x_pos,
                                    dc_y_pos+dcm_font_size,
                                    dcc_font,
                                    dcc_font_size,
                                    dc_width,
                                    dc_height,
                                    color,
                                    lines = dcc_lines[day])
        # be の描画
        color = (0,0,0)
        button_description = button_descriptions[self.screen_condition]
        self.place_text(self.screen,
                        button_description,
                        be_x_pos,
                        be_y_pos,
                        be_font,
                        be_font_size,
                        be_width*2,
                        be_height,
                        color,
                        lines = 0)
            
    def draw_text(self, 
                  surface : pygame.Surface,
                  text : str, 
                  x : int, 
                  y : int,
                  font : pygame.font.Font,
                  color : tuple = (0,0,0)):
        """
        一行のみの記述
        """
        image = font.render(text, True, color)
        surface.blit(image, (x, y))

    def place_text(self,
                    surface : pygame.Surface,
                    texts : list[str],
                    x : int, 
                    y : int,
                    font : pygame.font.Font,
                    font_size : int,
                    pallet_width : int,
                    pallet_height : int,
                    color : tuple = (0,0,0),
                    lines : int = 0,
                    extent : tuple[int]|None = None):
        """
        2行以上の記述
            for i in range(NoC // C_num_in_line+1):
                   ~~~~^^~~~~~~~~~~~~~~
        ZeroDivisionError: integer division or modulo by zero
        """
        capable_c_num_in_line : int = pallet_width//font_size
        a = len(texts)
        for i, text in enumerate(texts,1):
            """
            どっかでreturn かえってるのが問題。
            """
            if text != "":
                text_len : int = len(text)
                for j in range(text_len // capable_c_num_in_line+1): # 1回回数足さないとダメ
                    start, end = capable_c_num_in_line*j, min(capable_c_num_in_line*(j+1),text_len)
                    over = (font_size * (lines+2)) > pallet_height
                    last = over and (font_size * (lines+1) < pallet_height)
                    if (not last) and (not over):
                        self.draw_text(surface, text[start:end], x, y+font_size*lines,font,color)
                        lines += 1
                        if end == text_len and a == i:
                            return lines
                    elif last:
                        self.draw_text(surface, "...", x, y+font_size*lines,font,color)
                        lines += 1
                        return lines
                    elif over:
                        return lines
        return lines

    def kill_calendar(self):
        # window を出して、終了していいか確認する処理を if else で。
        pygame.quit()
        sys.exit()

    def handle_events(self,
                      events : list[pygame.event.Event],
                      bg_surfs_with_pos : list[tuple[pygame.Surface,tuple[int,int]]],
                      layout : dict[str,int]):
        def parse_keybind(instructions : str) -> tuple[int, int]:
            MOD_MAP = {
                "LSHIFT": pygame.KMOD_LSHIFT,
                "LCTRL": pygame.KMOD_LCTRL,
                "ALT": pygame.KMOD_ALT,
                "META": pygame.KMOD_META
            }
            conf = self.settings["key"][instructions]
            key = pygame.key.key_code(conf["key"])
            mod = 0
            for m in conf.get("mod", []):
                mod |= MOD_MAP[m]
            return mod, key
        for event in events:
            if self.screen_condition == "default":
                if event.type == pygame.QUIT: # click x button
                    self.kill_calendar()
                elif event.type == pygame.KEYDOWN:
                    mod_key = (event.mod,event.key)
                    # 以下のようにkey をとるのが最善かわからない。
                    # settings.json にキーボード情報を保存さえできればよい。
                    # OSの違いを吸収できるように実装する。

                    # bg_surfs_with_pos つまり読み込んだ bg がない場合は change_upper/lower_bg の処理をしない。
                    if bg_surfs_with_pos:
                        if mod_key == parse_keybind("Change upper bg"):
                            self.selected_bg = (self.selected_bg + 1) % len(list(Path(self.settings["b_dir"]).glob('*.*')))
                        if mod_key == parse_keybind("Change lowwer bg"):
                            self.selected_bg = (self.selected_bg - 1) % len(list(Path(self.settings["b_dir"]).glob('*.*')))
                    if mod_key == parse_keybind("Kill game"): # or pygame.K_ESCAPE
                        self.kill_calendar()
                    if mod_key == parse_keybind("Change schedule"):
                        self.screen_condition = "select_schedule"
                    elif mod_key == parse_keybind("Stop game"): # or pygame.K_SPACE
                        if self.paused:
                            self.paused = False
                        else:
                            self.paused = True
                    elif mod_key == parse_keybind("Day + 1"): # 右
                        self.calendar_day += 1
                        _, last_day = calendar.monthrange(self.calendar_year, self.calendar_month)
                        if self.calendar_day > last_day:
                            self.calendar_day = 1
                            self.calendar_month += 1
                            if self.calendar_month > 12:
                                self.calendar_month = 1
                                self.calendar_year += 1
                    elif mod_key == parse_keybind("Day - 1"): # 左
                        self.calendar_day -= 1
                        if self.calendar_day == 0:
                            self.calendar_month -= 1
                            if self.calendar_month == 0:
                                self.calendar_year -= 1
                                self.calendar_month = 12
                            _, self.calendar_day = calendar.monthrange(self.calendar_year, self.calendar_month)
                    elif mod_key == parse_keybind("Month - 1"): # 下
                        self.calendar_month -= 1
                        if self.calendar_month == 0:
                            self.calendar_year -= 1
                            self.calendar_month = 12
                        _, self.calendar_day = calendar.monthrange(self.calendar_year, self.calendar_month)
                    elif mod_key == parse_keybind("Month + 1"): # 上
                        self.calendar_day = 1
                        self.calendar_month += 1
                        if self.calendar_month > 12:
                            self.calendar_month = 1
                            self.calendar_year += 1
            elif self.screen_condition == "select_schedule":
                if event.type == pygame.KEYDOWN:
                    mod_key = (event.mod,event.key)
                    if mod_key == parse_keybind("ss_Discard"):
                        self.screen_condition = "default"
                    elif mod_key == parse_keybind("ss_Select schedule"):
                        selected_schedule : str = self.selected_schedule[1][self.selected_schedule[0]]
                        day : str = str(self.calendar_year).zfill(4)+str(self.calendar_month).zfill(2)+str(self.calendar_day).zfill(2)
                        self.temp_schedules = copy.deepcopy(self.schedules)
                        pygame.key.start_text_input()
                        self.screen_condition = "change_schedule"
                    # elif 上下方向にカーソルを移動させる]
                    elif mod_key == parse_keybind("ss_Up"): # 下
                        self.selected_schedule = [(self.selected_schedule[0]-1)%len(self.selected_schedule[1]), self.selected_schedule[1]]
                    elif mod_key == parse_keybind("ss_Down"): # 上
                        self.selected_schedule = [(self.selected_schedule[0]+1)%len(self.selected_schedule[1]), self.selected_schedule[1]]     
            elif self.screen_condition == "change_schedule":
                selected_schedule : str = self.selected_schedule[1][self.selected_schedule[0]]
                day : str = str(self.calendar_year).zfill(4)+str(self.calendar_month).zfill(2)+str(self.calendar_day).zfill(2)
                temp_text = "\n".join(self.temp_schedules[selected_schedule][day])
                if temp_text == "":
                    self.temp_schedules[selected_schedule][day] = [""]
                # 変更
                if event.type == pygame.TEXTINPUT:
                    self.editing_text = ""
                    temp_text += event.text
                if event.type == pygame.TEXTEDITING: # 編集中の文字を表示するためのみに用いる
                    self.editing_text = event.text
                if event.type == pygame.KEYDOWN:
                    mod_key = (event.mod,event.key)
                    if mod_key == parse_keybind("cs_Change schedule"):
                        pygame.key.stop_text_input()
                        self.screen_condition = "default"
                        self.schedules = self.temp_schedules
                        self.save_schedules(schedule_pathes = Path("schedule") / (selected_schedule + ".json"),
                                            schedule = self.schedules[selected_schedule])
                    elif mod_key == parse_keybind("cs_Discard changes"): # or pygame.K_ESCAPE
                        pygame.key.stop_text_input()
                        self.screen_condition = "default"
                    elif mod_key == parse_keybind("cs_Delete"):
                        temp_text = temp_text[:-1]
                    elif mod_key == parse_keybind("cs_Line break"):
                        temp_text += "\n"
                self.temp_schedules[selected_schedule][day] = temp_text.split("\n")
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
    c = Mk_calendar(_settings)
    c.run(c.layout, c.prerendered_surf_with_pos, c.bg_surfs_with_pos, c.button_descriptions)