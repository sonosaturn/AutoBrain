Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run chr(34) & strPath & "\venv\Scripts\python.exe" & chr(34) & " " & chr(34) & strPath & "\autobrain_core\brain.py" & chr(34), 0
Set WshShell = Nothing
