import logging
import random
import time
import threading
import pygame
from gpiozero import Button, LED, Servo
from espeakng import ESpeakNG


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class CleverToad:
    def __init__(self, config):
        self.update_config(config)

        pygame.mixer.init()
        self.tune = pygame.mixer.Sound("tune.wav")
        self.diceroll = pygame.mixer.Sound("diceroll.wav")

        Button.was_held = False
        self.lever_button = Button(11, bounce_time=0.05, hold_time=0.5)
        self.lever_button.when_held = self.lever_held
        self.lever_button.when_released = self.lever_released
        self.coin_button = Button(22, bounce_time=0.1)
        self.coin_button.when_released = self.coin_inserted
        self.eyes_led = LED(16)
        self.book_servo = Servo(pin=14,
                                min_pulse_width=0.8/1000,
                                max_pulse_width=2.2/1000,
                                initial_value=-1,
                                frame_width=10/1000)
        self.speech_engine = ESpeakNG()
        self.speech_engine.speed = 155
        self.speech_engine.pitch = 25
        self.speech_engine.voice = 'en'
        self.coin_received = False
        self.dice_mode = False
        self.blink()
        self.speech_engine.say("The Toad... is ready.", sync=True)

    def update_config(self, config):
        self.vocabulary = config["prophecy_parts"]
        self.dice_type = config["dice_type"]
        self.critical_fail = config["critical_fail"]
        self.critical_success = config["critical_success"]
        logger.info("config updated")

    def generate_prophecy(self):
        sentence = [
            random.choice(self.vocabulary['subjects']),
            random.choice(self.vocabulary['actions']),
            random.choice(self.vocabulary['objects']),
        ]

        pt = random.randint(0, 2)
        if pt == 0:
            sentence.append(random.choice(
                self.vocabulary['spatial_prepositions']))
            sentence.append(random.choice(self.vocabulary['places']))
        elif pt == 1:
            sentence.append(random.choice(
                self.vocabulary['temporal_prepositions']))
            sentence.append(random.choice(self.vocabulary['times']))
        else:
            sentence.append(random.choice(
                self.vocabulary['spatial_prepositions']))
            sentence.append(random.choice(self.vocabulary['places']))
            sentence.append(random.choice(
                self.vocabulary['temporal_prepositions']))
            sentence.append(random.choice(self.vocabulary['times']))

        logger.info(sentence)
        return ' ... '.join(sentence)

    def blink(self):
        self.eyes_led.on()
        time.sleep(0.1)
        self.eyes_led.off()
        time.sleep(0.2)

    def turn_pages(self):
        for s in range(-90, -40, 2):
            self.book_servo.value = (s / 90)
            time.sleep(0.01)
        time.sleep(0.1)
        for s in range(-40, -30, 2):
            self.book_servo.value = (s / 90)
            time.sleep(0.01)
        time.sleep(0.1)
        for s in range(-30, 0, 1):
            self.book_servo.value = (s / 90)
            time.sleep(0.02)
        time.sleep(0.1)
        for s in range(0, 20, 1):
            self.book_servo.value = (s / 90)
            time.sleep(0.02)

    def on_missing_coin(self):
        self.speech_engine.speed = 230
        self.speech_engine.say("Ah... ah... ah...", sync=False)
        self.blink()
        self.blink()
        self.blink()
        self.speech_engine.speed = 155
        self.speech_engine.say("You didn't say the magic word!", sync=True)

    def on_prophecy(self):
        self.coin_received = False

        channel = self.tune.play()
        threading.Thread(target=self.turn_pages).start()
        self.blink()
        self.eyes_led.on()
        while channel.get_busy():
            pygame.time.Clock().tick(10)
        self.speech_engine.say(self.generate_prophecy(), sync=True)
        self.eyes_led.off()
        self.book_servo.value = -1

    def coin_inserted(self):
        logger.info("coin inserted")
        self.coin_received = True

    def lever_released(self):
        if not self.lever_button.was_held:
            self.roll_dice() if self.dice_mode else self.lever_pulled()
        self.lever_button.was_held = False

    def lever_held(self):
        self.lever_button.was_held = True
        self.dice_mode = not self.dice_mode
        if self.dice_mode:
            logger.info("dice mode activated")
            self.eyes_led.on()
            self.book_servo.value = 2 / 9  # max book value (line 96, 97)
            self.speech_engine.say(
               "You wish... to waste my talents... on dice rolling?... So shall it be.")
        else:
            logger.info("prophecy mode activated")
            self.speech_engine.say("Back to the prophecies... Thank you!", sync=True)
            self.book_servo.value = -1
            self.eyes_led.off()

    def roll_dice(self):
        n = random.randint(1, self.dice_type)
        logger.info(f"rolled {n}")
        if n == 1:
            message = self.critical_fail
        elif n == 20:
            message = self.critical_success
        else:
            message = str(n)
        channel = self.diceroll.play()
        while channel.get_busy():
            pygame.time.Clock().tick(10)
        self.speech_engine.say(message, sync=True)

    def lever_pulled(self):
        logger.info(f"lever pulled (coin: {self.coin_received})")
        if not self.coin_received:
            self.on_missing_coin()
        else:
            self.on_prophecy()
