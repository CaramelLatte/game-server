#import win32gui
import pyautogui as ag
import pygetwindow as gw

#window = win32gui.FindWindow("Notepad", None)
#win32gui.SetForegroundWindow(window)

#ag.typewrite(["a"])

cmd_window = gw.getWindowsWithTitle("Command Prompt")[0]
np_window = gw.getWindowsWithTitle("Untitled")[0]
# print(notepad_window)
#notepad_window.resizeTo(200, 300)
if cmd_window.isMinimized == False:
  cmd_window.minimize()
else:
  cmd_window.restore()
ag.hotkey("ctrl", "a")
ag.hotkey("ctrl", "c")
cmd_window.minimize()
np_window.restore()
ag.hotkey("ctrl", "v")
