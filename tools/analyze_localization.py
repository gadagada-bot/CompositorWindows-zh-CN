import os,pathlib,pickle
import pefile,capstone
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP

root=pathlib.Path(os.environ['COMPOSITOR_LOCALIZATION_WORK'])
binary=root/'CompositorWindows-1.1.0'/'CompositorWindows'/'Compositor.exe'
pe=pefile.PE(str(binary));base=pe.OPTIONAL_HEADER.ImageBase
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
md.detail=True;md.skipdata=True
instructions=[];references={}
for section in pe.sections:
    if not section.Characteristics&0x20000000:continue
    for ins in md.disasm(section.get_data(),base+section.VirtualAddress):
        index=len(instructions)
        instructions.append((ins.address,ins.size,ins.mnemonic,ins.op_str,ins.bytes,
                             ins.disp_offset if ins.id else 0,ins.disp_size if ins.id else 0))
        if not ins.id:continue
        for op in ins.operands:
            if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
                references.setdefault(ins.address+ins.size+op.mem.disp,[]).append(index)
with (root/'disassembly.pickle').open('wb') as output:
    pickle.dump((instructions,references),output)
