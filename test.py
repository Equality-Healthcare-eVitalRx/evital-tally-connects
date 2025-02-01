import tkinter as tk
from tkinter import font

root = tk.Tk()

# Register font using Tk's internal method
# root.tk.call('font', 'create', 'Manrope', '-family', 'Manrope', '-size', 14, '-weight', 'bold')

# Apply the registered font
custom_font = font.Font(family='Manrope')

# Test Label
label = tk.Label(root, text="Custom Font Loaded! y", font=custom_font)
label.pack(pady=20)

# root.mainloop()


with open("fonts_list.txt", "w") as file:
    for f in font.families():
        file.write(f + "\n")
root.mainloop()

# for f in font.families():
#     if "Manrope" in f:
#         print(f)


# root.mainloop()
