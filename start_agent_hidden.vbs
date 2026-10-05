Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir

Dim nodePath, pythonPath
nodePath = ""
pythonPath = ""

' 1. Check Node.js
If fso.FileExists("C:\Program Files\nodejs\node.exe") Then
    nodePath = """C:\Program Files\nodejs\node.exe"""
ElseIf fso.FileExists("C:\Program Files (x86)\nodejs\node.exe") Then
    nodePath = """C:\Program Files (x86)\nodejs\node.exe"""
Else
    nodePath = "node"
End If

' 2. Check Python
If fso.FileExists("C:\Users\ntn78\AppData\Local\Programs\Python\Python311\python.exe") Then
    pythonPath = """C:\Users\ntn78\AppData\Local\Programs\Python\Python311\python.exe"""
Else
    pythonPath = "python"
End If

' Chay ngam khong hien cua so CMD (0 = Hidden, False = Async)
Dim cmdLine
cmdLine = "cmd.exe /c cd /d """ & currentDir & """ && (" & nodePath & " agent.js >> agent_data\agent.log 2>&1 || " & pythonPath & " agent.py >> agent_data\agent.log 2>&1)"
WshShell.Run cmdLine, 0, False
