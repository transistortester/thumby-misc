#to take a screenshot
with open("screenshot.bin", "wb") as file:
    file.write(thumby.display.display.buffer)

#to view a screenshot
with open("screenshot.bin", "rb") as file:
    file.readinto(thumby.display.display.buffer)
thumby.display.update()