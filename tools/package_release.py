import argparse,hashlib,pathlib,subprocess,zipfile

parser=argparse.ArgumentParser(description='Verify reproduced binaries and package the zh.1 release')
parser.add_argument('--portable',required=True,type=pathlib.Path)
parser.add_argument('--output',required=True,type=pathlib.Path)
args=parser.parse_args()
expected={'Compositor.exe':'389d2c7ca310ca88d8e0b45fd7623975170dbafc0580cd4412741b4b8f6785a0',
          'Qt6Widgets.dll':'f98063218df3cea2a85f982da91c7f723a49d9fe6bc444377b919dcd786ec132'}
for name,digest in expected.items():
    actual=hashlib.sha256((args.portable/name).read_bytes()).hexdigest()
    if actual!=digest:raise RuntimeError('Reproduced binary mismatch: '+name)
args.output.mkdir(parents=True,exist_ok=True)
portable=args.output/'CompositorWindows-1.1.0-zh-CN-portable.zip'
with zipfile.ZipFile(portable,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for file in sorted(args.portable.rglob('*')):
        if file.is_file():archive.write(file,str(pathlib.Path('CompositorWindows-zh-CN')/file.relative_to(args.portable)))
source=args.output/'CompositorWindows-1.1.0-zh-CN-localization-source.zip'
subprocess.run(['git','archive','--format=zip','--prefix=CompositorWindows-zh-CN-source/',
                '--output='+str(source.resolve()),'HEAD'],check=True)
checks=[]
for file in [portable,source]:
    with zipfile.ZipFile(file) as archive:
        failed=archive.testzip()
        if failed:raise RuntimeError('Invalid ZIP entry: '+failed)
    checks.append(hashlib.sha256(file.read_bytes()).hexdigest()+'  '+file.name)
(args.output/'SHA256SUMS.txt').write_text('\n'.join(checks)+'\n',encoding='ascii')
print('Binary hashes and archive integrity verified.')
