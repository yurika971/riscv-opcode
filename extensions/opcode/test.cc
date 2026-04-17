#include "iostream"
#include "riscv.h"
#include "cstdio"

void build32(struct riscv_opcode op){
   
    std::string name(op.name);
    for (auto &w : name) {
        if (w == '.') w = '_';
    }
    std::cout << "class " << name + "_32" << "(BaseInstMeta):\n";
    std::cout << "NAME = \"" << name << "\"" << std::endl;
    std::cout << "ASM = \"" << name << "  " << op.args  << "\"\n";

    
    // Call Python script to get binary pattern
    std::string cmd = "python3 ../find_op.py " + std::string(op.name);
    system(cmd.c_str());

    std::cout << std::endl;
    
}

void build64(struct riscv_opcode op){

}

int main(){
    int i = 10;
    int t = 0;
    while (t < 29 && riscv_opcodes[++i].name != 0){     //19-29可能比较熟悉一些
        
        auto op = riscv_opcodes[i];
        if (op.pinfo != 0) continue;    //alias不要
        
        unsigned xlen = op.xlen_requirement;
        switch (xlen) {
            case 0: build64(op);build32(op);break;
            case 32:build32(op);break;
            case 64:build64(op);break;
        }
        
        t++;
    }
    std::cout << "t = " << t << std::endl;
    return 0;
}
