import sys, os, pathlib

base = pathlib.Path('.')
tools_dir = base / 'Tools'
common_dir = base / 'Common'
ok, fail = [], []

for cat_dir in sorted(tools_dir.iterdir()):
    if not cat_dir.is_dir():
        continue
    for tool_dir in sorted(cat_dir.iterdir()):
        if not tool_dir.is_dir():
            continue
        main_py = tool_dir / 'main.py'
        if not main_py.exists():
            continue
        name = f'{cat_dir.name}/{tool_dir.name}'
        try:
            # Simulate what the tool does: add Common to sys.path, then exec
            old_path = sys.path.copy()
            sys.path.insert(0, str(common_dir))
            sys.path.insert(0, str(tool_dir))
            
            # Read and compile to check imports
            with open(main_py, encoding='utf-8') as f:
                code = f.read()
            
            # Check if it imports BaseToolWindow properly
            if 'BaseToolWindow' in code and 'from ui.base_window import BaseToolWindow' not in code and 'from Common.ui.base_window' not in code:
                fail.append(f'{name}: BaseToolWindow import pattern wrong')
            elif 'BaseToolWindow' not in code:
                fail.append(f'{name}: does not inherit BaseToolWindow')
            else:
                ok.append(name)
            
            sys.path = old_path
        except Exception as e:
            fail.append(f'{name}: {type(e).__name__}: {e}')
            sys.path = old_path

print(f'Import check: {len(ok)} OK, {len(fail)} FAIL')
if fail:
    print()
    print('ISSUES:')
    for f in fail:
        print(f'  {f}')
