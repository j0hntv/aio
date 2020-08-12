import asyncio
import curses
import glob
import itertools
import random
import sys
import time

from curses_tools import draw_frame, read_controls, get_frame_size
from explosion import explode
from game_scenario import get_garbage_delay_tics, PHRASES
from obstacles import Obstacle
from physics import update_speed


STAR_SYMBOLS = '+*.'
TIC_TIMEOUT = 0.1
YEAR_OF_WEAPON_APPEARED = 2000
FIRE_OFFSET_FOR_SPACESHIP_DIMENSIONS = 2
SPACESHIP_BORDER_OFFSET = 1
year = 1957
coroutines = []
obstacles = []
obstacles_in_last_collisions = []


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    global obstacles_in_last_collisions

    if year < YEAR_OF_WEAPON_APPEARED:
        return

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await sleep()

    canvas.addstr(round(row), round(column), 'O')
    await sleep()
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 1 < row < max_row and 0 < column < max_column:
        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                obstacles_in_last_collisions.append(obstacle)
                return
        canvas.addstr(round(row), round(column), symbol)
        await sleep()
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def get_garbage_frames():
    garbage_files = glob.glob(f'frames/garbage/*.txt')
    garbage_frames = []
    for garbage_file in garbage_files:
        with open(garbage_file) as file:
            garbage_frames.append(file.read())

    return garbage_frames


def get_rocket_frames():
    with open('frames/rocket_frame_1.txt') as file:
        rocket_frame1 = file.read()
    with open('frames/rocket_frame_2.txt') as file:
        rocket_frame2 = file.read()

    return rocket_frame1, rocket_frame2


def get_game_over_frame():
    with open('frames/game_over.txt') as file:
        game_over_frame = file.read()
    
    return game_over_frame


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    global obstacles

    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 1

    rows_size, columns_size = get_frame_size(garbage_frame)
    obstacle = Obstacle(row, column, rows_size, columns_size)
    obstacles.append(obstacle)

    try:
        while row < rows_number:
            if obstacle in obstacles_in_last_collisions:
                obstacles_in_last_collisions.remove(obstacle)
                curses.beep()

                obstacle_center_row = obstacle.row + rows_size // 2
                obstacle_center_column = obstacle.column + columns_size // 2

                await explode(canvas, obstacle_center_row, obstacle_center_column)
                return

            draw_frame(canvas, row, column, garbage_frame)
            canvas.border()
            await sleep()
            draw_frame(canvas, row, column, garbage_frame, negative=True)
            row += speed
            obstacle.row += speed
    finally:
        obstacles.remove(obstacle)


async def fill_orbit_with_garbage(canvas, garbage_frames):
    global coroutines
    while True:
        garbage_delay_tics = get_garbage_delay_tics(year)
        
        if not garbage_delay_tics:
            await sleep()
            continue

        garbage_frame = random.choice(garbage_frames)
        _, columns = canvas.getmaxyx()
        garbage_columns_frame_size = get_frame_size(garbage_frame)[1]
        
        columns_range = garbage_columns_frame_size, columns - garbage_columns_frame_size
        random_column = random.randint(*columns_range)

        fly_garbage_coroutine = fly_garbage(canvas, random_column, garbage_frame)
        coroutines.append(fly_garbage_coroutine)
        await sleep(garbage_delay_tics)


async def show_gameover(canvas, frame):
    row, column = curses.LINES//2, curses.COLS//2
    frame_size = get_frame_size(frame)
    row -= frame_size[0] // 2
    column -= frame_size[1] // 2

    while True:
        draw_frame(canvas, row, column, frame)
        await sleep(10)
        draw_frame(canvas, row, column, frame, negative=True)
        await sleep(4)


def get_current_event(year):
    return PHRASES.get(year, '')


async def show_current_year(canvas):
    global year
    event_window = canvas.derwin(1, 50, 1, 2)

    while True:
        current_event = get_current_event(year)
        event_text = f'Year: {year} {current_event}'
        draw_frame(event_window, 0, 0, event_text)
        event_window.refresh()
        await sleep(15)
        draw_frame(event_window, 0, 0, event_text, negative=True)
        year += 1


async def animate_spaceship(canvas, rocket_frame1, rocket_frame2, game_over_frame):
    global coroutines
    row, column = curses.LINES//2, curses.COLS//2
    rows, columns = canvas.getmaxyx()
    row_speed = column_speed = 0

    for frame in itertools.cycle([rocket_frame1, rocket_frame2]):
        frame_rows, frame_columns = get_frame_size(frame)
        for obstacle in obstacles:
            if obstacle.has_collision(row, column, frame_rows, frame_columns):
                await show_gameover(canvas, game_over_frame)
                return

        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)

        row += row_speed
        column += column_speed

        row = max(row, SPACESHIP_BORDER_OFFSET)
        row = min(row, rows - frame_rows - SPACESHIP_BORDER_OFFSET)
        column = max(column, SPACESHIP_BORDER_OFFSET)
        column = min(column, columns - frame_columns - SPACESHIP_BORDER_OFFSET)

        if space_pressed:
            fire_coroutine = fire(canvas, row, column + FIRE_OFFSET_FOR_SPACESHIP_DIMENSIONS)
            coroutines.append(fire_coroutine)

        draw_frame(canvas, row, column, frame)
        await sleep()

        draw_frame(canvas, row, column, frame, negative=True)


async def blink(canvas, row, column):
    symbol = random.choice(STAR_SYMBOLS)
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(random.randrange(20))

        canvas.addstr(row, column, symbol)
        await sleep(random.randrange(5))

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(random.randrange(10))

        canvas.addstr(row, column, symbol)
        await sleep(random.randrange(5))


def get_star_random_position(canvas):
    offset = 1 # for border
    up_offset = 2 # for event window
    rows, columns = canvas.getmaxyx()
    row = random.randrange(up_offset, rows - offset)
    column = random.randrange(offset, columns - offset)
    return row, column


def draw(canvas):
    global coroutines
    canvas.nodelay(True)
    curses.curs_set(False)
    canvas.border()

    rocket_frame1, rocket_frame2 = get_rocket_frames()
    game_over_frame = get_game_over_frame()
    garbage_frames = get_garbage_frames()

    coroutines.extend([
        animate_spaceship(canvas, rocket_frame1, rocket_frame2, game_over_frame),
        fill_orbit_with_garbage(canvas, garbage_frames),
        show_current_year(canvas),
        *(blink(canvas, *get_star_random_position(canvas)) for i in range(100))
    ])


    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


def main():
    curses.update_lines_cols()
    try:
        curses.wrapper(draw)
    except KeyboardInterrupt:
        sys.exit()


if __name__ == '__main__':
    main()
