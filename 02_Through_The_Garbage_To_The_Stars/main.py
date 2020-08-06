import asyncio
import curses
import glob
import random
import sys
import time
from curses_tools import draw_frame, read_controls, get_frame_size
from obstacles import Obstacle
from physics import update_speed


STAR_SYMBOLS = '+*.'
TIC_TIMEOUT = 0.1


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
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


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    global obstacles

    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 1

    rows_size, columns_size = get_frame_size(garbage_frame)
    obstacle = Obstacle(row, column, rows_size, columns_size)
    obstacles.append(obstacle)


    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        canvas.border()
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        obstacle.row += speed

    obstacles.remove(obstacle)


async def fill_orbit_with_garbage(canvas):
    global coroutines
    garbage_frames = get_garbage_frames()
    while True:
        garbage_frame = random.choice(garbage_frames)

        _, columns = canvas.getmaxyx()
        garbage_columns_frame_size = get_frame_size(garbage_frame)[1]
        
        columns_range = garbage_columns_frame_size, columns - garbage_columns_frame_size
        random_column = random.randint(*columns_range)

        fly_garbage_coroutine = fly_garbage(canvas, random_column, garbage_frame)
        coroutines.append(fly_garbage_coroutine)

        await sleep(random.randrange(50))


async def animate_spaceship(canvas, frame1, frame2):
    global coroutines
    row, column = curses.LINES//2, curses.COLS//2
    row_speed = column_speed = 0

    while True:
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)

        row += row_speed
        column += column_speed

        rows, columns = canvas.getmaxyx()
        frame_rows, frame_columns = get_frame_size(frame1)

        if row <= 1:
            row = 1

        if column <= 1:
            column = 1

        if row  >= rows - frame_rows:
            row = rows - frame_rows - 1

        if column >= columns - frame_columns:
            column = columns - frame_columns - 1

        if space_pressed:
            fire_coroutine = fire(canvas, row, column + 2)
            coroutines.append(fire_coroutine)

        draw_frame(canvas, row, column, frame1)
        await sleep(2)

        draw_frame(canvas, row, column, frame1, negative=True)
        draw_frame(canvas, row, column, frame2)
        await sleep(2)

        draw_frame(canvas, row, column, frame2, negative=True)


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
    rows, columns = canvas.getmaxyx()
    row = random.randrange(1, rows-1)
    column = random.randrange(1, columns-1)
    return row, column


def draw(canvas):
    global coroutines
    canvas.nodelay(True)
    curses.curs_set(False)
    canvas.border()

    rocket_frame1, rocket_frame2 = get_rocket_frames()
    
    animate_spaceship_coroutine = animate_spaceship(canvas, rocket_frame1, rocket_frame2)
    garbage_coroutine = fill_orbit_with_garbage(canvas)

    coroutines.append(animate_spaceship_coroutine)
    coroutines.append(garbage_coroutine)
    coroutines += [blink(canvas, *get_star_random_position(canvas)) for i in range(100)]

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    coroutines = []
    obstacles = []
    curses.update_lines_cols()
    try:
        curses.wrapper(draw)
    except KeyboardInterrupt:
        sys.exit()
