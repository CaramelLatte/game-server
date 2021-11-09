import pyautogui as ag
import pygetwindow as gw
import os, winshell, win32com.client, pythoncom, sys
from subprocess import Popen, CREATE_NEW_CONSOLE

#clean env
def clean():
  window_list = gw.getAllWindows()
  for window in window_list:
    window.minimize()

#try to launch game, if not already launched. If err, log err
def normalize(game_server):
  try:
    game_server = gw.getWindowsWithTitle(game_server)[0]
  except:
    launch = input("Game server not running. Would you like to launch? Enter 'y' or 'n' ")
    if launch == "y":
      print("this prints")
      os.startfile("minecraft.bat", 'open') # THIS LINE DOESN'T FUCKING WORK WHY
      print("so does this")
      #f = open(file_to_launch, 'r') THIS LINE WORKS
      #print(f.read()) THIS LINE WORKS

cwd = os.getcwd()
# print(cwd)
shortcut_path = os.path.join(cwd, "demoshortcut.lnk")
target = os.path.abspath("C:/MinecraftServer/eula.txt")

shell = win32com.client.Dispatch("WScript.Shell")
shortcut = shell.CreateShortCut(shortcut_path)
shortcut.Targetpath = target
shortcut.save()


#normalize("test")
# os.startfile("demoshortcut.lnk", "open")
# test = input("aaaa")
p = Popen(["notepad.exe", "demoshortcut.lnk"], creationflags=CREATE_NEW_CONSOLE)