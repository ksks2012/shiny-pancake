# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['ui/skill_query_desktop.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('db', 'db'),
        ('ui', 'ui'),
        ('ui/tabs', 'ui/tabs'),
        ('utils', 'utils')
    ],
    hiddenimports=[
        'beautifulsoup4',
        'PyYAML',
        'tkcalendar'
        'sqlalchemy'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BazaarDataManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False
)

