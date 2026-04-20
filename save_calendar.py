import sys
from pathlib import Path
import datetime
import pygame
from _load_settings import _settings
from main import Mk_calendar

class Mk_png(Mk_calendar):
    def run(self,
            layout : dict[str,int],
            prerendered_surf_with_pos : tuple[pygame.Surface,tuple[int,int]],
            bg_surfs_with_pos : list[tuple[pygame.Surface,tuple[int,int]]],
            button_descriptions : dict[str,list[str]]):
        self.screen.fill((255,255,255))
        if bg_surfs_with_pos:
            self.screen.blit(bg_surfs_with_pos[self.selected_bg][0], bg_surfs_with_pos[self.selected_bg][1])
        self.screen.blit(prerendered_surf_with_pos[0], prerendered_surf_with_pos[1])
        self.draw_schedule(layout,button_descriptions)
        self.handle_events(pygame.event.get(), bg_surfs_with_pos, layout)
        pygame.display.update()
        self.kill_calendar()

    def kill_calendar(self):
        today = "".join(str(datetime.date.today()).split("-"))
        pygame.image.save(self.screen, Path(self.settings["c_dir"])/(today+"_01.png"))
        pygame.image.save(self.screen, Path(self.settings["c_dir"])/(today+"_02.png"))
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    c = Mk_png(_settings)
    c.run(c.layout, c.prerendered_surf_with_pos, c.bg_surfs_with_pos, c.button_descriptions)