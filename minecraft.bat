cd C:/"MinecraftServer"/
echo %cd% 

java -Xmx2G -jar server.jar >> C:\Users\jared\OneDrive\Desktop\personalsite\game-test\logs\%DATE:~-4%-%DATE:~4,2%-%DATE:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
pause