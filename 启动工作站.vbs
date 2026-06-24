Set s = CreateObject("WScript.Shell")
s.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
Dim exitCode
exitCode = s.Run("cmd /c python launcher.py & if errorlevel 1 pause", 1, True)
