import asyncio
import curses
import random
import time


STAR_SYMBOLS = '+*.:'
TIC_TIMEOUT = 0.1

async def blink(canvas, row, column):
    symbol = random.choice(STAR_SYMBOLS)
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(10):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

def get_star_random_position(curses):
    row = random.randrange(1, curses.LINES-1)
    col = random.randrange(2, curses.COLS-2)
    return row, col

def draw(canvas):
    curses.curs_set(False)
    canvas.border()
    coroutines = [blink(canvas, *get_star_random_position(curses)) for i in range(5)]
    while True:
        for coroutine in coroutines:
            coroutine.send(None)
            canvas.refresh()
        time.sleep(TIC_TIMEOUT)

  
if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
