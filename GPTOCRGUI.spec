block_cipher = None

a = Analysis(
    ['GPTOCRGUI.py'],
    pathex=['D:/MyFiles/AImodels/OCR-with-GPT - 打包'],  
    binaries=[],
    datas=[
        ('ocrgui.ico', '.'),
        ('utils/*.py', 'utils'),
        ('processors/*.py', 'processors'),
    ],
    hiddenimports=[
        'PIL',
        'openai',
        'pystray',
        'httpx',
        'utils.path_tools',
        'utils.config_manager',
        'processors.image_encoder',
        'processors.markdown_processor',
        'keyboard'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False  # 修改为False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PillOCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ocrgui.ico'
)