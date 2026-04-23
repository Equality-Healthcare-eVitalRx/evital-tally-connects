**To generate build run command**

```
pyinstaller.exe --noconsole --onefile --windowed --icon=./lib/images/logo2.ico --add-data "lib/fonts/static/Manrope-Regular.ttf;lib/fonts/static/" --add-data "lib/fonts/breeze/breeze.tcl;lib/fonts/breeze" --add-data "lib/fonts/breeze/breeze/*.png;lib/fonts/breeze/breeze" --splash "./lib/images/login_panel.PNG" app.py
```

**To Generate buld using uvx**
```
uvx pyinstaller.exe --noconsole --onefile --windowed --icon=./lib/images/logo2.ico --add-data "lib/fonts/static/Manrope-Regular.ttf;lib/fonts/static/" --add-data "lib/fonts/breeze/breeze.tcl;lib/fonts/breeze" --add-data "lib/fonts/breeze/breeze/*.png;lib/fonts/breeze/breeze" --splash "./lib/images/login_panel.PNG" app.py
```

**To Generate Build Using UV**
```
 uv run pyinstaller.exe --noconsole --onefile --windowed --clean --icon=./lib/images/logo2.ico --add-data "lib/fonts/static/Manrope-Regular.ttf;lib/fonts/static/" --add-data "lib/fonts/breeze/breeze.tcl;lib/fonts/breeze" --add-data "lib/fonts/breeze/breeze/*.png;lib/fonts/breeze/breeze" --splash "./lib/images/login_panel.PNG" --collect-all babel  app.py
```
