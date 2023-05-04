# ZMM
Z--, a C-like transpiled to and compiled from C (its just different syntax but dw about it)

## Compilation

```shell
pyinstaller --onefile main.py
cd dist
mv main.exe zc.exe
```

then add the dist folder to path

## Usage
```shell
zc --help | -h
zc <source.zs> <destination_name> --p | [GCCFLAGS] | [GCCFLAGS & --p]
```