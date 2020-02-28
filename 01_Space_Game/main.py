import asyncio
import curses
import random
import time


STAR_SYMBOLS = '+*.:'
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
    rows, cols = canvas.getmaxyx()
    row = random.randrange(1, rows-1)
    col = random.randrange(1, cols-1)
    return row, col

def draw(canvas):
    curses.curs_set(False)
    canvas.border()
    coroutines = [blink(canvas, *get_star_random_position(canvas)) for i in range(100)]
    fire_coroutine = fire(canvas, curses.LINES//2, curses.COLS//2)
    coroutines.insert(0, fire_coroutine)
    
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
                canvas.refresh()
            except StopIteration:
                coroutines.remove(coroutine)
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
