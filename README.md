backup-tools
============

These are scripts I use for performing backups.

backupRemote.py
--

This is a simple wrapper around rsync. It is intended to be used on the backup
server to copy files from a remote machine.

rsync does the heavy lifiting, this just:

- Breaks a single command into multiple rsync invocations (necessary on my NAS,
  as otherwise it would run out of memory when doing a backup).
- Replicates the ancestral part of the directory tree. For example, with rsync,
  if you tell it to copy client:/usr/local to /backups/ you'll end up with a
  directory called "local" in /backups. backupRemote.py will instead create
  /backups/usr/ and copy "local" into that directory.


incrementalBackup.py
--

Sort of like rsnapshot, but:

- Uses backupRemote.py

- Uses a different filename convention

- Not written in perl. (The fact that it's written in perl is why I didn't try
  to just adapt rsnapshot to my needs.)
