import os
import pathlib,sys,json
root=pathlib.Path(os.environ.get('COMPOSITOR_LOCALIZATION_WORK',str(pathlib.Path(__file__).resolve().parent)))
sys.path.insert(0,str(root/'pydeps'))
import pefile
folder=root/'CompositorWindows-1.1.0'/'CompositorWindows'
original=folder/'Qt6Widgets.original.dll'
if not original.exists():original.write_bytes((folder/'Qt6Widgets.dll').read_bytes())
raw=original.read_bytes();data=bytearray(raw);pe=pefile.PE(data=raw)
section=next(s for s in pe.sections if s.Name.startswith(b'.rdata'))
begin=section.PointerToRawData;end=begin+section.SizeOfRawData
labels={'Save':'保存','Cancel':'取消','Discard':'舍弃','Apply':'应用','Close':'关闭',
        'Open':'打开','Reset':'重置','Yes':'是','No':'否','Abort':'中止',
        'Retry':'重试','Ignore':'忽略','Help':'帮助','Save All':'全部保存',
        'Yes to All':'全部选是','No to All':'全部选否','Restore Defaults':'恢复默认',
        'Show Details...':'显示详情…','Hide Details...':'隐藏详情…',
        'Basic colors':'基本颜色','Custom colors':'自定颜色',
        'Add to Custom Colors':'添加到自定颜色',
        'Select Color':'选择颜色','Pick Screen Color':'屏幕取色'}
applied=[];skipped=[]
for en,zh in list(labels.items()):
    labels['&'+en]=zh
for en,zh in labels.items():
    b=en.encode();z=zh.encode('utf8');start=begin
    while (pos:=raw.find(b+b'\0',start,end))!=-1:
        start=pos+len(b)+1
        if raw[pos-1]!=0:continue
        cap=len(b)+1;limit=(pos+cap+3)//4*4
        while pos+cap<limit and raw[pos+cap]==0:cap+=1
        if len(z)+1>cap:skipped.append(en);continue
        data[pos:pos+cap]=z+b'\0'*(cap-len(z));applied.append(en)
(folder/'Qt6Widgets.dll').write_bytes(data)
(root/'qt-buttons-report.json').write_text(json.dumps({'applied':applied,'skipped':skipped},ensure_ascii=False,indent=2),encoding='utf8')
print('Standard labels translated:',len(applied),'Skipped:',skipped)
