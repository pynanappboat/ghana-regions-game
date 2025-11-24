import turtle
import pandas as pd
from PIL import Image
import os
import sys

# --- File paths (change if your files are elsewhere) ---
image_path = "blank_regions_img.gif"  # must be a GIF for turtle bgpic
csv_path = "16_regions_ghana.csv"  # must contain columns: region,x,y

# --- Validate files ---
if not os.path.exists(image_path):
    print(f"ERROR: image file not found: {image_path}")
    print("Put the GIF in the same folder as the script or update image_path.")
    sys.exit(1)

if not os.path.exists(csv_path):
    print(f"ERROR: CSV file not found: {csv_path}")
    print("Put the CSV in the same folder as the script or update csv_path.")
    sys.exit(1)

# --- Load image to get size (Pillow) ---
image = Image.open(image_path)
image_width, image_height = image.width, image.height


# --- Setup screen ---
screen = turtle.Screen()
screen.title("Ghana Regions Game")

screen.setup(width=image_width, height=image_height)
screen.bgpic(image_path)

screen.tracer(0)

# --- Load CSV ---
data = pd.read_csv(csv_path)
# Normalize region names to Title() for matching
data['region'] = data['region'].astype(str).str.title()
list_regions = data['region'].to_list()

# --- Game state ---
already_guess = []
TIME_START = 3 * 60  # 3 minutes
time_left = TIME_START
timer_started = False
game_over = False
score = 0

# --- UI turtles ---
ui_turtle = turtle.Turtle()
ui_turtle.hideturtle()
ui_turtle.penup()
ui_turtle.speed(0)

message_turtle = turtle.Turtle()
message_turtle.hideturtle()
message_turtle.penup()
message_turtle.speed(0)

# For writing region names on map
def write_region_on_map(name: str):
    region_row = data[data['region'] == name].iloc[0]
    x_coord = int(region_row['x'])
    y_coord = int(region_row['y'])
    marker = turtle.Turtle()
    marker.hideturtle()
    marker.penup()
    marker.goto(x_coord, y_coord)
    marker.write(name, font=("Ariel", 12, "normal"))

# --- Drawing UI (top-right) ---
def draw_ui():
    ui_turtle.clear()
    # compute top-right coordinates (turtle origin is center)
    win_w = screen.window_width()
    win_h = screen.window_height()
    # padding from the window edge
    padding_x = -20
    padding_y = 20

    # top-right corner coordinate to start drawing text box
    box_right = win_w // 2 - padding_x
    box_top = win_h // 2 - padding_y
    # print(box_right, box_top)

    # rectangle size
    box_w = 220
    # box_h = 80

    # draw a semi-opaque-looking rectangle (solid color)
    left_x = box_right - box_w
    top_y = box_top

    # write Score and Time inside the box
    text_x = left_x + 10
    text_y = top_y - 24
    ui_turtle.goto(text_x, text_y)
    ui_turtle.color("light sea green")
    ui_turtle.write(f"Score: {score}", font=("Courier", 16, "bold"))
    ui_turtle.goto(text_x, text_y - 30)
    minutes = time_left // 60
    secs = time_left % 60
    ui_turtle.write(f"Time left: {minutes:02d}:{secs:02d}", font=("Courier", 14, "bold"))

    screen.update()

# --- Message helper ---
def show_temp_message(text: str, color="red", duration=1500):
    message_turtle.clear()
    message_turtle.goto(0, -image_height//2 + 40)  # slightly above bottom
    message_turtle.color(color)
    message_turtle.write(text, align="center", font=("Courier", 14, "bold"))
    screen.update()
    screen.ontimer(lambda: message_turtle.clear(), duration)

# --- End game handler ---
def end_game(reason: str = "Time's up"):
    global game_over
    if game_over:
        return
    game_over = True
    # Show big center message
    message_turtle.goto(0, 0)
    message_turtle.color("darkred")
    message_turtle.write(f"{reason}\nScore: {score}", align="center", font=("Ariel", 24, "bold"))
    screen.update()
    # Save missed
    missed = [region for region in list_regions if region not in already_guess]
    pd.DataFrame({'Missed guess': missed}).to_csv('Missed_learning_regions.csv', index=False)
    print("Missed saved to Missed_learning_regions.csv")
    print(pd.DataFrame({'Missed guess': missed}))

# --- Timer using ontimer ---
def format_time(seconds: int) -> str:
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"

def countdown_tick():
    global time_left, game_over
    if not timer_started or game_over:
        return
    if time_left <= 0:
        draw_ui()
        end_game("Time's up")
        return
    time_left -= 1
    draw_ui()
    screen.ontimer(countdown_tick, 1000)

# draw initial UI
draw_ui()

# --- Main guessing loop ---
while len(already_guess) < len(list_regions) and not game_over:
    # Start timer at first prompt
    if not timer_started:
        timer_started = True
        # schedule the first tick in 1 second (so UI shows full time first)
        screen.ontimer(countdown_tick, 1000)

    title_text = f"{len(already_guess)}/{len(list_regions)} Regions Correct"
    answer = screen.textinput(title=title_text, prompt="What's another region's name? (type 'Exit' to quit)")

    # textinput returns None when dialog closed -> treat as Exit
    if answer is None:
        answer = "Exit"

    answer = answer.strip().title()

    if answer == "Exit":
        end_game("Goodbye")
        break

    if game_over:
        break

    if answer in already_guess:
        show_temp_message("You have already guessed that. Try again.", color="orange", duration=1400)
        continue

    if answer in list_regions:
        # correct
        write_region_on_map(answer)
        already_guess.append(answer)
        score += 1
        draw_ui()
        if len(already_guess) == len(list_regions):
            end_game("All regions guessed! Well done.")
            break
    else:
        # incorrect
        show_temp_message("Incorrect. Try again.", color="red", duration=1200)
        continue

# Make sure we finalize if loop ends
if not game_over:
    end_game("Session ended")

# Keep window open
try:
    screen.mainloop()
except turtle.Terminator:
    pass
