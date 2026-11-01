import argparse,hashlib,json,os,pathlib,shutil,subprocess,sys,tempfile

tools=pathlib.Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description='Reproduce the partial Chinese localization of CompositorWindows 1.1.0')
parser.add_argument('--input',required=True,type=pathlib.Path)
parser.add_argument('--output',required=True,type=pathlib.Path)
args=parser.parse_args()
source=args.input.resolve();destination=args.output.resolve()
if destination.exists():parser.error('Output must not exist; nothing will be overwritten.')
if source==destination or source in destination.parents:parser.error('Output must be outside the input folder.')
expected={'Compositor.exe':'53c1076ab7ee64e966c52a85d315c6a15fb66f9848c4c8731bcd04ab51960de2',
          'Qt6Widgets.dll':'d34ef78b3d3b5506ee8279ce6efbfc263d773b74860af76e66b0715346897a3a'}
for name,digest in expected.items():
    path=source/name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        parser.error(f'Unsupported or modified input: {name}. Use the original 1.1.0 portable release.')
destination.parent.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='compositor-zh-',dir=destination.parent) as temp:
    scratch=pathlib.Path(temp)
    if scratch.resolve().parent!=destination.parent:raise RuntimeError('Unexpected temporary directory')
    stage=scratch/'CompositorWindows-1.1.0'/'CompositorWindows';stage.mkdir(parents=True)
    for name in expected:shutil.copy2(source/name,stage/name)
    shutil.copy2(tools/'zh-CN.tsv',scratch/'zh-CN.tsv')
    env=os.environ.copy();env['COMPOSITOR_LOCALIZATION_WORK']=str(scratch)
    for script in ['analyze_localization.py','localize_pe.py','localize_qt_buttons.py']:
        subprocess.run([sys.executable,str(tools/script)],env=env,check=True)
    shutil.copytree(source,destination)
    shutil.copy2(stage/'Compositor.zh-CN.exe',destination/'Compositor.exe')
    shutil.copy2(stage/'Qt6Widgets.dll',destination/'Qt6Widgets.dll')
    shutil.copy2(tools/'zh-CN.tsv',destination/'zh-CN.tsv')
    shutil.copy2(tools.parent/'README.md',destination/'README-zh-CN.md')
    shutil.copy2(scratch/'localization-report.json',destination/'localization-report.json')
    shutil.copy2(scratch/'qt-buttons-report.json',destination/'qt-buttons-report.json')
print('Localized portable folder created:',destination)
