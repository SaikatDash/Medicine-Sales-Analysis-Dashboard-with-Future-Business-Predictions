import traceback
try:
    import main
    print('main imported, app=', getattr(main,'app', None))
except Exception:
    traceback.print_exc()
