# Build on MacOS
## Create  virtual environment
```
python -m venv venv
```
## Activate virtual environment

```
source venv/bin/activate
```

### Install requirements
```
pip install -r requirements.txt
```
### Build .exe file using .spec file
```
pyinstaller GPTOCRGUI.spec
```
### Use create-dmg to build dmg file
Install create-dmg
```
brew install create-dmg
```
create dmg

```
create-dmg \
  --volname "PillOCR setup" \
  --volicon "ocrgui.icns" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "PillOCR.app" 200 190 \
  --hide-extension "PillOCR.app" \
  --app-drop-link 600 185 \
  "PillOCR.dmg" \
  "dist/PillOCR.app"
```