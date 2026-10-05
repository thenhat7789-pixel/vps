Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir

' Chay ngam Node.js hoac Python ma KHONG hien cua so CMD (windowStyle = 0)
WshShell.Run "cmd.exe /c cd /d """ & currentDir & """ && (node agent.js 2>> agent_data\agent_err.log || python agent.py 2>> agent_data\agent_err.log)", 0, False
