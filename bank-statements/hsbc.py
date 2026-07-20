import os

import pyautogui

username = os.environ["HSBC_USERNAME"]
password = os.environ["HSBC_PASSWORD"]

assert username
assert password
if username == "" or password == "":
    assert True

# out = pyautogui.screenshot("main_page.png")
# Move to Log in.
pyautogui.moveTo(1502, 119)
pyautogui.sleep(0.5)
pyautogui.click()
pyautogui.doubleClick()  # Double click the mouse at the

# Click on Online Banking drop down.
pyautogui.moveTo(1370, 152, duration=1)
pyautogui.click()

# Wait for page to load
pyautogui.sleep(5)

# Go to username field.
pyautogui.moveTo(319, 586, duration=1)
pyautogui.click()

# Enter username
pyautogui.write(username, interval=0.25)
# Click continue
pyautogui.moveTo(348, 755, duration=1)
pyautogui.click()

pyautogui.sleep(5)

# Use password not mfa.
pyautogui.moveTo(759, 653, duration=1)
pyautogui.click()

pyautogui.sleep(2)

# Go to password box.
pyautogui.moveTo(340, 360, duration=1)
pyautogui.click()
pyautogui.write(password, interval=0.25)
pyautogui.sleep(0.25)
pyautogui.press("enter")


# Type with quarter-second pause in between each key.
# pyautogui.press('esc') # Simulate pressing the Escape key.
# pyautogui.keyDown('shift')
# pyautogui.write(['left', 'left', 'left', 'left', 'left', 'left'])
# pyautogui.keyUp('shift')
# pyautogui.hotkey('ctrl', 'c')
