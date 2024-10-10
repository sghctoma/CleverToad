#!/usr/bin/env python3

import logging
import random
import time
import threading
import tomllib
import pygame
from RPi import GPIO
from espeakng import ESpeakNG


PIN_BOOK = 14
PIN_EYES = 17
PIN_LEVER = 27
PIN_COIN = 22

pwm = None
tune = None
speech_engine = None
coin_received = False
logger = logging.getLogger(__name__)


def generate_premonition(vocabulary):
    sentence = [
        random.choice(vocabulary['subjects']),
        random.choice(vocabulary['actions']),
        random.choice(vocabulary['objects']),
    ]

    pt = random.randint(0, 2)
    if pt == 0:
        sentence.append(random.choice(vocabulary['spatial_prepositions']))
        sentence.append(random.choice(vocabulary['places']))
    elif pt == 1:
        sentence.append(random.choice(vocabulary['temporal_prepositions']))
        sentence.append(random.choice(vocabulary['times']))
    else:
        sentence.append(random.choice(vocabulary['spatial_prepositions']))
        sentence.append(random.choice(vocabulary['places']))
        sentence.append(random.choice(vocabulary['temporal_prepositions']))
        sentence.append(random.choice(vocabulary['times']))

    logger.info(sentence)
    return ' ... '.join(sentence)


def blink():
    GPIO.output(PIN_EYES, 1)
    time.sleep(0.1)
    GPIO.output(PIN_EYES, 0)
    time.sleep(0.2)


def turn_book_pages():
    global pwm

    pwm.start(0)
    pwm.ChangeDutyCycle(50)
    time.sleep(0.1)
    pwm.ChangeDutyCycle(60)
    time.sleep(0.1)
    pwm.ChangeDutyCycle(70)
    time.sleep(1)
    pwm.ChangeDutyCycle(50)
    time.sleep(0.2)
    pwm.ChangeDutyCycle(30)
    time.sleep(0.2)
    pwm.stop()


def on_missing_coin():
    global speech_engine

    speech_engine.speed = 230
    speech_engine.say("Ah... ah... ah...", sync=False)
    blink()
    blink()
    blink()
    speech_engine.speed = 155
    speech_engine.say("You didn't say the magic word!", sync=True)


def on_premonition():
    global coin_received
    global tune

    coin_received = False

    channel = tune.play()
    threading.Thread(target=turn_book_pages).start()
    blink()
    GPIO.output(PIN_EYES, 1)
    while channel.get_busy():
        pygame.time.Clock().tick(10)
    speech_engine.say(generate_premonition(vocabulary), sync=True)
    GPIO.output(PIN_EYES, 0)


def coin_inserted(pin):
    global coin_received

    logger.info("coin inserted")
    coin_received = True


def lever_pulled(pin):
    global coin_received

    logger.info(f"lever pulled (coin: {coin_received})")
    if not coin_received:
        on_missing_coin()
    else:
        on_premonition()


def setup_gpio():
    global pwm

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # coin
    GPIO.setup(PIN_COIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(PIN_COIN, GPIO.RISING, bouncetime=100,
                          callback=coin_inserted)
    # lever
    GPIO.setup(PIN_LEVER, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(PIN_LEVER, GPIO.RISING, bouncetime=200,
                          callback=lever_pulled)
    # eyes
    GPIO.setup(PIN_EYES, GPIO.OUT)
    GPIO.output(PIN_EYES, 0)

    # book
    GPIO.setup(PIN_BOOK, GPIO.OUT, initial=GPIO.LOW)
    pwm = GPIO.PWM(PIN_BOOK, 50)


def setup_speech():
    global speech_engine

    speech_engine = ESpeakNG()
    speech_engine.speed = 155
    speech_engine.pitch = 25
    speech_engine.voice = 'en'


def setup_tune():
    global tune

    pygame.mixer.init()
    tune = pygame.mixer.Sound("tune.wav")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    with open('vocabulary.toml', 'rb') as f:
        vocabulary = tomllib.load(f)
    setup_speech()
    setup_gpio()
    setup_tune()

    input("Press enter to quit\n\n")
    GPIO.cleanup()
