import traceback

try:
    with open('main.py','rb') as f:
        src = f.read()
    compile(src, 'main.py', 'exec')
    print('compiled OK')
except Exception:
    traceback.print_exc()
