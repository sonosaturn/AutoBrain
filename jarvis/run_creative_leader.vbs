Set WshShell = CreateObject("WScript.Shell")
' Ottiene la cartella dello script
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
' Esegue l'agente creativo in modo invisibile
WshShell.Run chr(34) & strPath & "\venv\Scripts\python.exe" & chr(34) & " " & chr(34) & strPath & "\creative_leader.py" & chr(34), 0
Set WshShell = Nothing