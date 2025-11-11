# The MIT License (MIT)

# Copyright (c) 2021-2024 Krux contributors

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# from . import Page
from math import floor
from random import randint
from ..display import FONT_WIDTH, SPLASH, FONT_HEIGHT, SPLASH_CHAR, TOTAL_LINES
from ..themes import theme


SCREENSAVER_ANIMATION_WAIT = 100  # milliseconds

class ScreenSaver:
    """Screensaver animation method"""

    def __init__(self, ctx):
        self.ctx = ctx

    def start(self):
        """Displays a screensaver until user presses a button or touch"""
        anim_frame = 0
        initial_offset = (TOTAL_LINES - len(SPLASH)) // 2
        fg_color = theme.fg_color
        bg_color = theme.bg_color
        final_color = theme.fg_color
        self.ctx.display.clear()
        button_press = None

        min_distance = 5  # fixed chars or rows
        max_distance_x = int(self.ctx.display.width()/FONT_WIDTH / 2)
        max_distance_y = int(self.ctx.display.height()/FONT_HEIGHT / 2)
        max_multiplier = 2
        max_distance = max(max_distance_x, max_distance_y)  # fixed chars or rows
        max_anim_frame = int(max_distance * max_multiplier / 2)

        hold_at_completion = 1500  # millseconds

        def initialize_deltas(deltas):
            max_offset_x = int((self.ctx.display.width() - max([len(row) for row in SPLASH]) * FONT_WIDTH) / 2)
            x_start_offset = randint(0, max_offset_x) * (-1 if randint(0, 1) == 1 else 1)

            max_offset_y = int((self.ctx.display.height() - len(SPLASH) * FONT_HEIGHT) / 2)
            y_start = self.ctx.display.get_center_offset_y(len(SPLASH)) + randint(0, max_offset_y) * (-1 if randint(0, 1) == 1 else 1)

            for row in SPLASH:
                x_start = self.ctx.display.get_center_offset_x(row) + x_start_offset

                for i, char in enumerate(row):
                    if char == SPLASH_CHAR:
                        char_x = x_start + i*FONT_WIDTH

                        # Final target location is:
                        final_pt = (char_x, y_start)

                        # Randomized starting location:
                        offset_direction_x = -1 if randint(0, 1) == 1 else 1
                        offset_direction_y = -1 if randint(0, 1) == 1 else 1

                        # Scale one axis to a multiple of the other
                        multiplier = randint(1, max_multiplier)
                        multiplier_is_x = randint(0, 1) == 1
                        if multiplier_is_x:
                            # Horizontal will be a multiple of the y-delta
                            offset_blocks_y = randint(min_distance, max(min_distance + 1, floor(max_distance_y / multiplier))) * offset_direction_y
                            offset_blocks_x = abs(offset_blocks_y) * multiplier * offset_direction_x
                        else:
                            offset_blocks_x = randint(min_distance, max(min_distance + 1, floor(max_distance_x / multiplier))) * offset_direction_x
                            offset_blocks_y = abs(offset_blocks_x) * multiplier * offset_direction_y

                        start_pt = (
                            char_x + offset_blocks_x * FONT_WIDTH,
                            y_start + offset_blocks_y * FONT_HEIGHT
                        )

                        deltas.append((start_pt, final_pt, offset_direction_x, offset_direction_y, multiplier, multiplier_is_x))

                # Advance to the next line
                y_start += FONT_HEIGHT
        
        deltas = []
        initialize_deltas(deltas)

        erase_list = set()

        while button_press is None:
            # show animation on the screeen
            # offset_y = anim_frame * FONT_HEIGHT
            # self.ctx.display.fill_rectangle(
            #     0,
            #     offset_y,
            #     self.ctx.display.width(),
            #     FONT_HEIGHT,
            #     bg_color,
            # )
            # if initial_offset <= anim_frame < len(SPLASH) + initial_offset:
            #     self.ctx.display.draw_hcentered_text(
            #         SPLASH[anim_frame - initial_offset], offset_y, fg_color, bg_color
            #     )
            # anim_frame += 1
            # if anim_frame > len(SPLASH) + 2 * initial_offset:
            #     anim_frame = 0
            #     bg_color, fg_color = fg_color, bg_color

            if anim_frame > max_anim_frame:
                # Reset to a new random sequence
                anim_frame = 0
                bg_color = randint(0x0000, 0xFFFF)
                fg_color = randint(0x0000, 0xFFFF)
                final_color = randint(0x0000, 0xFFFF)

                deltas = []
                initialize_deltas(deltas)
                button_press = self.ctx.input.wait_for_button(block=False, wait_duration=hold_at_completion)
                self.ctx.display.fill_rectangle(0, 0, width=self.ctx.display.width(), height=self.ctx.display.height(), color=bg_color)
                continue

            moving_blocks_set = set()
            finished_blocks_set = set()
            for start_pt, final_pt, offset_direction_x, offset_direction_y, multiplier, multiplier_is_x in deltas:
                cur_x = start_pt[0] - offset_direction_x * FONT_WIDTH * int(anim_frame / (multiplier if not multiplier_is_x else 1))
                cur_y = start_pt[1] - offset_direction_y * FONT_HEIGHT * int(anim_frame / (multiplier if multiplier_is_x else 1))

                if offset_direction_x > 0:
                    cur_x = max(final_pt[0], cur_x)
                else:
                    cur_x = min(final_pt[0], cur_x)

                if offset_direction_y > 0:
                    cur_y = max(final_pt[1], cur_y)
                else:
                    cur_y = min(final_pt[1], cur_y)

                if min(cur_x, cur_y) < 0 or cur_x > self.ctx.display.width() or cur_y > self.ctx.display.height():
                    continue

                if cur_x == final_pt[0] and cur_y == final_pt[1]:
                    finished_blocks_set.add((cur_x, cur_y))
                else:
                    moving_blocks_set.add((cur_x, cur_y))

            # Render the finished blocks
            for x, y in finished_blocks_set - moving_blocks_set:
                self.ctx.display.fill_rectangle(x=x, y=y, width=FONT_WIDTH, height=FONT_HEIGHT, color=final_color)

            # Render the moving blocks
            for x, y in moving_blocks_set:
                self.ctx.display.fill_rectangle(x=x, y=y, width=FONT_WIDTH, height=FONT_HEIGHT, color=fg_color)

            # Erase only the now-vacated blocks
            for x, y in erase_list.difference(moving_blocks_set).difference(finished_blocks_set):
                self.ctx.display.fill_rectangle(x=x, y=y, width=FONT_WIDTH, height=FONT_HEIGHT, color=bg_color)

            # Prep the next loop
            anim_frame += 1
            erase_list = moving_blocks_set.copy()
            erase_list.update(finished_blocks_set.copy())

            # wait_duration(animation period) can be modified here
            button_press = self.ctx.input.wait_for_button(block=False, wait_duration=SCREENSAVER_ANIMATION_WAIT)
