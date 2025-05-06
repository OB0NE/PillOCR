# Build on Windows
## Create  virtual environment
```
python -m venv venv
```
## Activate virtual environment
### On CMD
```
venv\Scripts\activate.bat
```
### On PowerShell
```
venv\Scripts\Activate.ps1
```

### Install requirements
```
pip install -r requirements.txt
```
### Build .exe file using .spec file
```powershell
pyinstaller GPTOCRGUI.spec
```
### Use Inno Setup Compiler to build setup
Use Inno Setup Compiler to run `.\setup\PillOCR.iss`.