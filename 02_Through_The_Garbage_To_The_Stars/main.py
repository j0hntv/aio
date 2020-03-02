import asyncio
import curses
import random
import sys
import time
from curses_tools import draw_frame, read_controls, get_frame_size
from space_garbage import fly_garbage


STAR_SYMBOLS = '+*.'
TIC_TIMEOUT = 0.1


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 1 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def get_garbage_frames():
    garbage_files = (
        'animations/duck.txt',
        'animations/hubble.txt',
        'animations/lamp.txt',
        'animations/trash_large.txt',
        'animations/trash_small.txt',
        'animations/trash_xl.txt'
        )
    garbage_frames = []
    for garbage_file in garbage_files:
        with open(garbage_file) as file:
            garbage_frames.append(file.read())

    return garbage_frames


def get_rocket_animation():
    with open('animations/rocket_frame_1.txt') as file:
        rocket_frame1 = file.read()
    with open('animations/rocket_frame_2.txt') as file:
        rocket_frame2 = file.read()
    return rocket_frame1, rocket_frame2
    

async def animate_spaceship(canvas, frame1, frame2):
    row, column = curses.LINES//2, curses.COLS//2
    while True:
        rows_direction, columns_direction, _ = read_controls(canvas)
        row += rows_direction
        column += columns_direction

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

        draw_frame(canvas, row, column, frame1)
        await asyncio.sleep(0)

        draw_frame(canvas, row, column, frame1, negative=True)
        draw_frame(canvas, row, column, frame2)
        await asyncio.sleep(0)

        draw_frame(canvas, row, column, frame2, negative=True)


async def blink(canvas, row, column):
    symbol = random.choice(STAR_SYMBOLS)
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(random.randrange(20)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(random.randrange(5)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(random.randrange(10)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(random.randrange(5)):
            await asyncio.sleep(0)

def get_star_random_position(canvas):
    rows, columns = canvas.getmaxyx()
    row = random.randrange(1, rows-1)
    column = random.randrange(1, columns-1)
    return row, column

def draw(canvas):
    canvas.nodelay(True)
    rocket_frame1, rocket_frame2 = get_rocket_animation()
    curses.curs_set(False)
    canvas.border()
    coroutines = [blink(canvas, *get_star_random_position(canvas)) for i in range(100)]
    fire_coroutine = fire(canvas, curses.LINES//2, curses.COLS//2)
    animate_spaceship_coroutine = animate_spaceship(canvas, rocket_frame1, rocket_frame2)
    coroutines.insert(0, fire_coroutine)
    coroutines.insert(1, animate_spaceship_coroutine)

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    try:
        curses.wrapper(draw)
    except KeyboardInterrupt:
        sys.exit()
