Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptPosition)
WshShell.Run chr(34) & strPath & "\venv\Scripts\pythonw.exe" & chr(34) & " " & chr(34) & strPath & "\main.py" & chr(34), 0
Set WshShell = Nothing