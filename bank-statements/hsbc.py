import os

import pyautogui

username = os.environ["HSBC_USERNAME"]
password = os.environ["HSBC_PASSWORD"]
file = os.environ["DOWNLOAD_PNG_PATH"]

assert username
assert password
assert file
if username == "" or password == "" or file == "" or not os.path.isfile(file):
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
pyautogui.sleep(7)

# We are now logged in.

# Navigate to credit card account
pyautogui.moveTo(652, 414, duration=1)
pyautogui.click()
# Hack... measured by me pressing keypresses 😭
for _ in range(15):
    pyautogui.press("down")
    pyautogui.sleep(0.25)
pyautogui.moveTo(599, 560, duration=1)
pyautogui.click()


# Click on search icon
pyautogui.moveTo(1248, 405, duration=1)
pyautogui.click()
pyautogui.sleep(0.5)
print("clicked on search icon")

# Click last 30 days of history
pyautogui.moveTo(1010, 523, duration=1)
pyautogui.click()
pyautogui.sleep(0.5)
print("clicked on last 30 days")

# Click "View results"
pyautogui.moveTo(1010, 723, duration=1)
pyautogui.click()
pyautogui.sleep(1)
print("clicked on view results")

# Hack to scroll down until we can see the download button...
download_location = None
i = 0
while not download_location and i < 100:
    pyautogui.press("down")
    pyautogui.sleep(0.25)
    download_location = pyautogui.locateCenterOnScreen(
        file, grayscale=True, confidence=0.8
    )
    print(
        f"could not find download button, scolling down download: {download_location}"
    )
    i += 1

assert download_location

print(f"found download button: {download_location}")
pyautogui.moveTo(download_location.x, download_location.y, duration=2)
pyautogui.click()
pyautogui.sleep(2)


pyautogui.moveTo(859, 696, duration=1)
pyautogui.doubleClick()
print("downloading")
