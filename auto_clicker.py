import threading
import time
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Listener as KeyboardListener

# Initialize mouse controller
mouse = MouseController()

# State variables
clicking = False
running = True

def clicker():
    """Continuously clicks when clicking is True"""
    while running:
        if clicking:
            mouse.click(Button.left)
            time.sleep(0.001)  # Small delay to maximize click speed
        else:
            time.sleep(0.01)  # Longer sleep when not clicking to save CPU

def on_press(key):
    """Handle key press events"""
    global clicking, running
    
    if key == Key.space:
        clicking = not clicking
        status = "ON" if clicking else "OFF"
        print(f"Auto-clicker: {status}")
    elif key == Key.esc:
        print("Exiting auto-clicker...")
        running = False
        return False  # Stop listener

def main():
    print("Auto-Clicker Started!")
    print("Press SPACE to toggle clicking ON/OFF")
    print("Press ESC to exit")
    print("Status: OFF")
    
    # Start clicking thread
    click_thread = threading.Thread(target=clicker, daemon=True)
    click_thread.start()
    
    # Start keyboard listener
    with KeyboardListener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    main()
