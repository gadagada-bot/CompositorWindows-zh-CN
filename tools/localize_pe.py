import os
"""Reversible text localization for the unsigned 1.1.0 portable build.

Existing strings are retained when shared with suffixes or too small. New UTF-8
strings then go in a read-only PE section. Only decoded LEA string-address
operands and existing base-relocated string pointers are redirected. Function
boundaries, instruction sizes, assets, imports, and project schemas are unchanged.
"""
import pathlib,sys,struct,json,pickle,hashlib
root=pathlib.Path(os.environ.get('COMPOSITOR_LOCALIZATION_WORK',str(pathlib.Path(__file__).resolve().parent)))
sys.path.insert(0,str(root/'pydeps'))
import pefile
original=root/'CompositorWindows-1.1.0'/'CompositorWindows'/'Compositor.exe'
raw=original.read_bytes();data=bytearray(raw);pe=pefile.PE(data=raw)
base=pe.OPTIONAL_HEADER.ImageBase
instructions,references=pickle.load(open(root/'disassembly.pickle','rb'))
ref_offsets=set();relocs={}
for va in references:
    if base<=va<base+pe.OPTIONAL_HEADER.SizeOfImage:
        try:ref_offsets.add(pe.get_offset_from_rva(va-base))
        except:pass
for block in pe.DIRECTORY_ENTRY_BASERELOC:
    for reloc in block.entries:
        if reloc.type!=10:continue
        offset=pe.get_offset_from_rva(reloc.rva);value=struct.unpack_from('<Q',raw,offset)[0]
        relocs.setdefault(value,[]).append(offset)
        if base<=value<base+pe.OPTIONAL_HEADER.SizeOfImage:
            try:ref_offsets.add(pe.get_offset_from_rva(value-base))
            except:pass
translations={}
for line in (root/'zh-CN.tsv').read_text(encoding='utf8').splitlines():
    if not line or line.startswith('#'):continue
    en,zh=line.split('\t',1)
    if en in translations and translations[en]!=zh:raise ValueError('Conflicting translation '+en)
    translations[en]=zh
# Some English labels double as persisted enum values, PSD descriptor keys, or
# font identifiers. Preserve these globally to retain format interoperability.
protected={'Regular','Bold','Italic','Bold Italic','Light','Normal','High quality',
 'Hue/Saturation','Levels','Curves','Exposure','Gradient Map','Grain','Invert',
 'Black & White','Color Balance','Gaussian Blur','Motion Blur','Add Noise',
 'Master','Reds','Yellows','Greens','Cyans','Blues','Magentas','Red','Green','Blue',
 'Hue','Saturation','Color','Subtract','Rectangle','Ellipse','Line',
 'Left','Right','Leading','Tracking','Name','Text'}
for s in protected:
    translations.pop(s,None)
applied=[];skipped=[];redirected=[];changes=[];claims=[]
rdata=next(s for s in pe.sections if s.Name.startswith(b'.rdata'))
begin=rdata.PointerToRawData;end=begin+rdata.SizeOfRawData
align=lambda x,a:(x+a-1)//a*a
new_rva=align(max(s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData) for s in pe.sections),pe.OPTIONAL_HEADER.SectionAlignment)
new_raw=align(len(raw),pe.OPTIONAL_HEADER.FileAlignment)
new_text=bytearray()
def write(off,b,why):
    for x,y in claims:
        if off<y and x<off+len(b):raise ValueError('Overlapping patch '+why)
    claims.append((off,off+len(b)));changes.append({'offset':off,'size':len(b),'why':why});data[off:off+len(b)]=b
for en,zh in translations.items():
    b=en.encode('utf8');z=zh.encode('utf8');start=begin;found=False
    while (pos:=raw.find(b+b'\0',start,end))!=-1:
        start=pos+len(b)+1
        va=base+pe.get_rva_from_offset(pos)
        if (pos>begin and raw[pos-1]!=0) and pos not in ref_offsets:continue
        found=True
        cap=len(b)+1;limit=align(pos+cap,4)
        while pos+cap<limit and raw[pos+cap]==0 and pos+cap not in ref_offsets:cap+=1
        interior=any(pos<x<pos+len(b) for x in ref_offsets)
        suffix=pos>begin and raw[pos-1]!=0
        if not interior and not suffix and len(z)+1<=cap:
            write(pos,z+b'\0'*(cap-len(z)),en)
            applied.append({'en':en,'zh':zh,'offset':pos,'mode':'in-place'});continue
        candidates=[i for i in references.get(va,[]) if instructions[i][2]=='lea' and instructions[i][6]==4]
        ptrs=relocs.get(va,[])
        if not candidates and not ptrs:
            skipped.append({'en':en,'zh':zh,'reason':'no address references','offset':pos});continue
        new_va=base+new_rva+len(new_text)
        new_text.extend(z+b'\0')
        refs=[]
        for i in candidates:
            address,size,mnemonic,operands,ibytes,disp_offset,disp_size=instructions[i]
            offset=pe.get_offset_from_rva(address-base)+disp_offset
            write(offset,struct.pack('<i',new_va-address-size),'text address '+en)
            refs.append({'address':hex(address),'context':[[hex(r[0]),r[2],r[3]] for r in instructions[max(0,i-2):i+5]]})
        for offset in ptrs:write(offset,struct.pack('<Q',new_va),'table pointer '+en)
        applied.append({'en':en,'zh':zh,'offset':pos,'mode':'relocated','code_refs':len(candidates),'table_refs':len(ptrs)})
        redirected.append({'en':en,'zh':zh,'refs':refs,'table_refs':ptrs})
    if not found:skipped.append({'en':en,'zh':zh,'reason':'not present'})
if new_text:
    header=pe.sections[-1].get_file_offset()+40
    assert header+40<=min(s.PointerToRawData for s in pe.sections)
    size_raw=align(len(new_text),pe.OPTIONAL_HEADER.FileAlignment)
    section=struct.pack('<8sIIIIIIHHI',b'.zhCN\0\0\0',len(new_text),new_rva,size_raw,new_raw,0,0,0,0,0x40000040)
    write(header,section,'read-only translation section')
    write(pe.FILE_HEADER.get_field_absolute_offset('NumberOfSections'),struct.pack('<H',pe.FILE_HEADER.NumberOfSections+1),'section count')
    write(pe.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfImage'),struct.pack('<I',align(new_rva+len(new_text),pe.OPTIONAL_HEADER.SectionAlignment)),'image size')
    write(pe.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfInitializedData'),struct.pack('<I',pe.OPTIONAL_HEADER.SizeOfInitializedData+size_raw),'initialized data size')
    data.extend(b'\0'*(new_raw-len(data)));data.extend(new_text);data.extend(b'\0'*(size_raw-len(new_text)))
final_pe=pefile.PE(data=bytes(data))
checkoff=final_pe.OPTIONAL_HEADER.get_field_absolute_offset('CheckSum')
struct.pack_into('<I',data,checkoff,final_pe.generate_checksum())
out=original.with_name('Compositor.zh-CN.exe');out.write_bytes(data)
report={'original_sha256':hashlib.sha256(raw).hexdigest(),'localized_sha256':hashlib.sha256(data).hexdigest(),'applied':applied,'protected':sorted(protected),'skipped':skipped,'redirected':redirected,'changes':changes}
(root/'localization-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'applied':len(applied),'relocated':len(redirected),'skipped':skipped},ensure_ascii=False))
