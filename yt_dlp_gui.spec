# PyInstaller spec file
# Run: pyinstaller yt_dlp_gui.spec

block_cipher = None

a = Analysis(['yt_dlp_gui/main.py'],
             pathex=['.'],
             binaries=[],
             datas=[('yt_dlp_gui/assets/icon.ico', 'assets')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(
		  pyz,
		  a.scripts,
		  [],
		  exclude_binaries=True,
		  name="yt-dlp-gui",
		  debug=False,
		  bootloader_ignore_signals=False,
		  strip=False,
		  upx=True,
		  console=False,
		  icon="yt_dlp_gui/assets/icon.ico",
 )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='yt-dlp-gui')
