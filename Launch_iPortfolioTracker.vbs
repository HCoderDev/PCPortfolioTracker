Set WshShell = CreateObject("WScript.Shell")
ExePath = WshShell.CurrentDirectory & "\dist\iPortfolioTracker.exe"
If Not CreateObject("Scripting.FileSystemObject").FileExists(ExePath) Then
    ExePath = WshShell.CurrentDirectory & "\iPortfolioTracker.exe"
End If

If CreateObject("Scripting.FileSystemObject").FileExists(ExePath) Then
    WshShell.Run """" & ExePath & """", 1, False
Else
    WshShell.Run """" & WshShell.CurrentDirectory & "\venv\Scripts\pythonw.exe"" """ & WshShell.CurrentDirectory & "\desktop_app.py""", 0, False
End If
