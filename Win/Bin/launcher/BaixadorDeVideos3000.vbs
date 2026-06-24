Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
appDir = fso.GetParentFolderName(scriptDir)
exeFile = fso.BuildPath(appDir, "release\BaixadorDeVideos3000.exe")
If Not fso.FileExists(exeFile) Then
    exeFile = fso.BuildPath(appDir, "BaixadorDeVideos3000.exe")
End If
sourceFile = fso.BuildPath(appDir, "python\src\ytdlp_gui_downloader.py")

shell.CurrentDirectory = appDir

If fso.FileExists(exeFile) Then
    shell.Run """" & exeFile & """", 1, False
ElseIf fso.FileExists(sourceFile) Then
    shell.Run "pythonw """ & sourceFile & """", 0, False
Else
    MsgBox "Nao encontrei o executavel ou python\src\ytdlp_gui_downloader.py nesta pasta.", vbExclamation, "Baixador de Videos 3000"
End If
