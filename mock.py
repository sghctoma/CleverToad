#!/usr/bin/env -S GPIOZERO_PIN_FACTORY=mock GPIOZERO_MOCK_PIN_CLASS=mockpwmpin python3

import logging
import time
import curses
import tomlkit
import clevertoad


class CursesHandler(logging.Handler):
    def __init__(self, screen):
        logging.Handler.__init__(self)
        self.screen = screen

    def emit(self, record):
        try:
            msg = self.format(record)
            screen = self.screen
            fs = "\n%s"
            screen.addstr(fs % msg)
            screen.refresh()
        except (KeyboardInterrupt, SystemExit):
            raise
        except (Exception):
            self.handleError(record)


def press(pin):
    pin.drive_low()
    time.sleep(0.05)
    pin.drive_high()


def longpress(pin):
    pin.drive_low()
    time.sleep(1)
    pin.drive_high()


def main(stdscr):
    stdscr.clear()
    stdscr.scrollok(True)
    stdscr.addstr("insert coin: press c\n")
    stdscr.addstr("pull lever:  press l\n")
    stdscr.addstr("dice mode:   press d\n")
    stdscr.addstr("quit:        press q\n")
    stdscr.addstr("====================\n")

    handler = CursesHandler(stdscr)
    clevertoad.logger.propagate = False
    clevertoad.logger.addHandler(handler)

    with open("config.toml", "r") as file:
        config = tomlkit.load(file)
    toad = clevertoad.CleverToad(config)
    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == ord('c'):
            press(toad.coin_button.pin)
        elif key == ord('l'):
            press(toad.lever_button.pin)
        elif key == ord('d'):
            longpress(toad.lever_button.pin)


curses.wrapper(main)
