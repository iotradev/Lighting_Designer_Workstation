import sys, pathlib

tools_dir = pathlib.Path('Tools')
ok, fail = [], []

for cat_dir in sorted(tools_dir.iterdir()):
    if not cat_dir.is_dir():
        continue
    for tool_dir in sorted(cat_dir.iterdir()):
        if not tool_dir.is_dir():
            continue
        main_py = tool_dir / 'main.py'
        if not main_py.exists():
            fail.append(f'{cat_dir.name}/{tool_dir.name}: main.py missing')
            continue
        try:
            with open(main_py, encoding='utf-8') as f:
                compile(f.read(), str(main_py), 'exec')
            ok.append(f'{cat_dir.name}/{tool_dir.name}')
        except SyntaxError as e:
            fail.append(f'{cat_dir.name}/{tool_dir.name}: SyntaxError line {e.lineno}: {e.msg}')
        except Exception as e:
            fail.append(f'{cat_dir.name}/{tool_dir.name}: {type(e).__name__}: {e}')

print(f'Syntax check: {len(ok)} OK, {len(fail)} FAIL')
if fail:
    print()
    print('FAILURES:')
    for f in fail:
        print(f'  {f}')
