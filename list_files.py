import pathlib
root = pathlib.Path('C:/Users/DIANA/bot-minecraft')
skip = {'node_modules','__pycache__','.pytest_cache','_backups','.git'}
for p in sorted(root.rglob('*')):
    if p.is_file():
        parts = set(p.relative_to(root).parts)
        if parts & skip:
            continue
        print(p.relative_to(root).as_posix())