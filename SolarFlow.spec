import os
from pathlib import Path

block_cipher = None

# Sammle Frontend-Dateien (HTML, CSS, JS)
frontend_path = Path('frontend')
frontend_files = []
if frontend_path.exists():
    for root, dirs, files in os.walk(frontend_path):
        for file in files:
            if file.endswith(('.html', '.css', '.js', '.json', '.png', '.jpg', '.ico', '.svg')):
                file_path = Path(root) / file
                relative_path = file_path.relative_to(frontend_path.parent)
                frontend_files.append((str(file_path), str(relative_path.parent)))

# Weitere Daten-Dateien
datas = frontend_files + [
    ('devices.json', '.') if os.path.exists('devices.json') else ('devices.json.example', '.') if os.path.exists('devices.json.example') else None,
]
# Filtere None-Werte
datas = [d for d in datas if d is not None]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'starlette',
        'pydantic',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SolarFlow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Auf False setzen für Windows ohne Konsolenfenster
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)