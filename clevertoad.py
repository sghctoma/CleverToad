#!/usr/bin/env python3

import logging
import random
import tomllib
from RPi import GPIO
from espeakng import ESpeakNG


PIN_LEVER = 22
PIN_COIN = 27
engine = None
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


def coin_inserted(pin):
    global coin_received

    logger.info("coin inserted")
    coin_received = True


def lever_pulled(pin):
    global coin_received
    global engine

    logger.info(f"lever pulled (coin: {coin_received})")
    if not coin_received:
        engine.speed = 230
        engine.say("Ah... ah... ah...", sync=True)
        engine.speed = 155
        engine.say("You didn't say the magic word!", sync=True)
    else:
        coin_received = False
        engine.say(generate_premonition(vocabulary), sync=True)


def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PIN_COIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(PIN_LEVER, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(PIN_COIN, GPIO.RISING, bouncetime=100,
                          callback=coin_inserted)
    GPIO.add_event_detect(PIN_LEVER, GPIO.RISING, bouncetime=100,
                          callback=lever_pulled)


def setup_speech():
    global engine
    engine = ESpeakNG()
    engine.speed = 155
    engine.pitch = 25
    engine.voice = 'en'


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    with open('vocabulary.toml', 'rb') as f:
        vocabulary = tomllib.load(f)
    setup_speech()
    setup_gpio()

    input("Press enter to quit\n\n")
    GPIO.cleanup()
