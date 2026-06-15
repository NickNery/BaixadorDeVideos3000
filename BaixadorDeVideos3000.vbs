Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

appDir = fso.GetParentFolderName(WScript.ScriptFullName)
exeFile = fso.BuildPath(appDir, "BaixadorDeVideos3000.exe")
sourceFile = fso.BuildPath(appDir, "src\ytdlp_gui_downloader.py")

shell.CurrentDirectory = appDir

If fso.FileExists(exeFile) Then
    shell.Run """" & exeFile & """", 1, False
ElseIf fso.FileExists(sourceFile) Then
    shell.Run "pythonw """ & sourceFile & """", 0, False
Else
    MsgBox "Nao encontrei o executavel ou src\ytdlp_gui_downloader.py nesta pasta.", vbExclamation, "Baixador de Videos 3000"
End If
