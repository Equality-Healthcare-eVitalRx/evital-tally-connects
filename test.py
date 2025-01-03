import sys
import time

def spinner_animation(duration=5):
    spinner = ['|', '/', '-', '\\']  # Symbols for the spinner
    end_time = time.time() + duration  # End time for the animation

    while time.time() < end_time:
        for symbol in spinner:
            sys.stdout.write(f'\rLoading... {symbol}')  # Write the spinner
            sys.stdout.flush()  # Flush the output buffer
            time.sleep(0.2)  # Wait a bit before updating
    # sys.stdout.write('\rDone!        \n')  # Clear spinner and print done

spinner_animation()
