Dim shell, cmd
cmd = "python ""D:\Projects\ai-photo-template-miniapp\scripts\watch_face.py"" --sync-onedrive"
Set shell = CreateObject("Wscript.Shell")
shell.Run cmd, 0, False
