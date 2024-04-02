from typing import List, Optional, Tuple
import pygame
import time
import os
import sys
from collections import OrderedDict
import numpy as np

from pygame.joystick import JoystickType
from pygame.surface import Surface
import pygame.freetype

# Read joystick commands in the background
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"


def init_game():
    # Initialize pygame
    pygame.init()

    # Initialize the joystick module
    pygame.joystick.init()


def check_for_joystick() -> Optional[JoystickType]:
    # Get the number of joysticks
    joystick_count = pygame.joystick.get_count()

    # Check if there is at least one joystick
    if joystick_count == 0:
        print("No joysticks found.")
        return None

    # Use the first joystick
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    return joystick


def collect_axis_data(
    joystick: JoystickType,
    axis_state: OrderedDict[str, List[float]],
    numaxes: int,
    limit: int = 100,
):
    # Read the clutch position
    for axes in range(numaxes):
        position = joystick.get_axis(axes)  # Assuming the clutch is mapped to axis 2
        # output = output + f"position {str(axes)}: {position:.2f} "
        key, _ = list(axis_state.items())[axes]
        if len(axis_state[key]) > limit:
            axis_state[key].pop(0)
        axis_state[key].append(position)


def collect_axis_data_event(
    axis: int,
    position: float,
    axis_state: OrderedDict[str, List[Tuple[float, int]]],
    limit: int = 100,
):
    # Read the clutch position
    key, _ = list(axis_state.items())[axis]
    if len(axis_state[key]) > limit:
        axis_state[key].pop(0)
    current_time = pygame.time.get_ticks()
    axis_state[key].append((position, current_time))


def calc_acceleration_timeseries(data: np.ndarray, eps=0.0001) -> np.ndarray:
    # if negative you are going down on the clutch, if positive you are going up on
    # the clutch
    position_diff = data[:, 0]
    # position_diff[position_diff == 0] = eps
    time_diff = data[:, 1]
    # time_diff[time_diff == 0] = eps
    acceleration = position_diff / time_diff
    # acceleration np.nan_to_num(acceleration, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
    return acceleration


def draw(output: str):
    # Print the new clutch position
    print(output, end="\r")
    # Erase the entire line by moving the cursor to the beginning and overwriting with spaces
    sys.stdout.write("\r")
    sys.stdout.flush()


APPMOUSEFOCUS = 1
APPINPUTFOCUS = 2
APPACTIVE = 4


def run_game_loop(joystick: JoystickType, screen: Surface):

    # Main loop to read the clutch position
    numaxes = joystick.get_numaxes()
    axis_state = OrderedDict()
    axis_names = ["wheel", "throttle", "break", "clutch"]
    for axis_name in axis_names:
        axis_state[axis_name] = [(0, 0)]
    limit = 100
    frame_time = 0.1
    epsilon = 0.00
    my_font = pygame.freetype.SysFont(pygame.freetype.get_default_font(), 36)
    clock = pygame.time.Clock()
    output = ""
    rect2 = None
    while True:
        pygame.event.pump()
        time_delta = clock.tick(20)
        has_axis_motion = False
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # if event.type == pygame.JOYAXISMOTION:
            #     # print("Joystick axis motion:", event.axis, event.value)
            #     has_axis_motion = True
            #     collect_axis_data_event(event.axis, event.value, axis_state, 100)
        last_axis_motion_event = [event for event in events if event.type == pygame.JOYAXISMOTION]
        if last_axis_motion_event:
            has_axis_motion = True
            collect_axis_data_event(event.axis, event.value, axis_state, 100)
        if not has_axis_motion:
            for axis_name in axis_names:
                if len(axis_state[axis_name]) > limit:
                    axis_state[axis_name].pop(0)
                last_position = axis_state[axis_name][-1][0]
                axis_state[axis_name].append((last_position, pygame.time.get_ticks()))
        clutch_positions_and_times = np.array(axis_state["clutch"])
        # clutch_positions = np.array(axis_state["clutch"])
        clutch_diff = np.diff(clutch_positions_and_times, axis=0)
        clutch_acceleration = calc_acceleration_timeseries(clutch_diff)
        if clutch_acceleration.size != 0:
            print(clutch_acceleration[-1])

        pygame.display.update()


def main():
    init_game()

    joystick = check_for_joystick()
    if joystick is None:
        return

    # Print the name of the joystick
    print("Joystick name:", joystick.get_name())
    pygame.event.set_allowed([pygame.JOYAXISMOTION])
    DISPLAYSURF = pygame.display.set_mode((500, 300))
    pygame.font.init()
    pygame.display.set_caption("Hello World!")
    run_game_loop(joystick, DISPLAYSURF)


if __name__ == "__main__":
    main()
