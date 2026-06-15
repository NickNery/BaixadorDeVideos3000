Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
appDir = fso.GetParentFolderName(scriptDir)
appFile = fso.BuildPath(appDir, "src\ytdlp_gui_downloader.py")

If fso.FileExists(appFile) Then
    shell.CurrentDirectory = appDir
    shell.Run "pythonw """ & appFile & """", 0, False
Else
    MsgBox "Nao encontrei src\ytdlp_gui_downloader.py nesta pasta.", vbExclamation, "Baixador de Videos 3000"
End If
