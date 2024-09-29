#!/usr/bin/env python3

import random
import tomllib
from espeakng import ESpeakNG


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

    print(sentence)
    return ' ... '.join(sentence)


if __name__ == '__main__':
    with open('vocabulary.toml', 'rb') as f:
        vocabulary = tomllib.load(f)

    engine = ESpeakNG()
    engine.speed = 155
    engine.pitch = 25
    engine.voice = 'en'
    engine.say(generate_premonition(vocabulary), sync=True)
