import threading
import tkinter
import sys
import time
from PIL import ImageSequence, ImageTk, Image

root = tkinter.Tk()
# frames = [tkinter.PhotoImage(file='lib\images\GIF.gif', format='gif -index %i'%(i)) for i in range(10)]

gif_path = "lib\images\GIF.gif"  # Update with your gif path


def process_frame(frame, size):
        # Convert the frame to RGBA
    frame = frame.convert("RGBA")
    data = frame.getdata()

    # Make black background transparent
    new_data = []
    for item in data:
        # If the pixel is black, make it transparent
        if item[:3] == (0, 0, 0):
            new_data.append((0, 0, 0, 0))  # Transparent
        else:
            new_data.append(item)
    frame.putdata(new_data)

    # Resize the frame
    frame = frame.resize(size, Image.Resampling.LANCZOS)
    return frame

frames = []

try:
    gif = Image.open(gif_path)
    # frames = []
    size = (350, 350)  # Set your desired size (width, height)
    for frame in ImageSequence.Iterator(gif):
        processed_frame = process_frame(frame, size)
        tk_frame = ImageTk.PhotoImage(processed_frame)
        frames.append(tk_frame)
    # animate_gif(sync_frame, frames)
except Exception as e:
    print(f"Error loading GIF: {e}")

def center_window(win):
    win.wait_visibility() # make sure the window is ready
    x = (win.winfo_screenwidth() - win.winfo_width()) // 2
    y = (win.winfo_screenheight() - win.winfo_height()) // 2
    win.geometry(f'+{x}+{y}')
print(frames)
def M_95(n=0, top=None, lbl=None):
    # Play GIF (file name = m95.gif) in a 320x320 tkinter window
    # Play GIF concurrently with the loading animation below
    # Close tkinter window after play
    global process_is_alive
    num_cycles = 2
    count = len(frames) * num_cycles
    # delay = 4000 // count # make required cycles of animation in around 4 secs
    if n == 0:
        root.withdraw()
        top = tkinter.Toplevel()
        lbl = tkinter.Label(top, image=frames[0])
        lbl.pack()
        center_window(top)
        process_is_alive = True
        lbl.after(100, M_95, n+1, top, lbl)
        # frame = frames[index]
        # sync_label.configure(image=frame)
        # next_index = (index + 3) % len(frames)
        # if not constants.STOP_THREAD:
        #     self.after(100, animate_gif, sync_label, frames, next_index)
    elif n < count-1:
        lbl.config(image=frames[n%len(frames)])
        lbl.after(100, M_95, n+1, top, lbl)
    else:
        top.destroy()
        root.destroy()
        process_is_alive = False

def loadingAnimation():
    animation = ["[■□□□□□□□□□]","[■■□□□□□□□□]", "[■■■□□□□□□□]", "[■■■■□□□□□□]", "[■■■■■□□□□□]", "[■■■■■■□□□□]", "[■■■■■■■□□□]", "[■■■■■■■■□□]", "[■■■■■■■■■□]", "[■■■■■■■■■■]"]
    i = 0
    while process_is_alive:
        sys.stdout.write("\r | Loading..." + animation[i % len(animation)])
        sys.stdout.flush()
        time.sleep(0.4)
        i += 1

M_95() # start GIF animation
threading.Thread(target=loadingAnimation).start()

root.mainloop()