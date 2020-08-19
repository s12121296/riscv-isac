# See LICENSE.incore for details

import ruamel
from ruamel.yaml import YAML
import riscv_isac.parsers as helpers
from riscv_isac.log import logger
from collections import Counter
import sys
yaml = YAML(typ="safe")
yaml.default_flow_style = True
yaml.explicit_start = True
yaml.allow_unicode = True
yaml.allow_duplicate_keys = True
from riscv_isac.cgf_normalize import *
import struct

'''Histogram post-processing module'''

help_message = '{:<20s} {:<10s}'.format('coverage', 'Compliance Coverage')

def pretty_print_yaml(yaml):
    res = ''''''
    for line in ruamel.yaml.round_trip_dump(yaml, indent=5, block_seq_indent=3).splitlines(True):
        res += line
    return res

def pretty_print_regfile(regfile):
    res = ""
    for index in range(0, 32, 4):
        print('x'+str(index) +   ' : ' + regfile[index] + '\t' +\
              'x'+str(index+1) + ' : ' + regfile[index+1] + '\t' + \
              'x'+str(index+2) + ' : ' + regfile[index+2] + '\t' + \
              'x'+str(index+3) + ' : ' + regfile[index+3] + '\t' )
    print('\n\n')

def gen_report(cgf, detailed):
    rpt_str = ''
    for cov_labels, value in cgf.items():
        if cov_labels != 'datasets':
            rpt_str += cov_labels + ':\n'
            total_uncovered = 0
            total_categories = 0
            for categories in value:
                if categories != 'config' and categories != 'opcode':
                    for coverpoints, coverage in value[categories].items():
                        if coverage == 0:
                            total_uncovered += 1
                    total_categories += len(value[categories])
            rpt_str += '  coverage: '+str(total_categories -total_uncovered) + \
                    '/' + str(total_categories)+'\n'
            for categories in value:
                if categories != 'config' and categories != 'opcode':
                    uncovered = 0
                    for coverpoints, coverage in value[categories].items():
                        if coverage == 0:
                            uncovered += 1
                    percentage_covered = str((len(value[categories]) - uncovered)/len(value[categories]))
                    node_level_str =  '  ' + categories + ':\n'
                    node_level_str += '    coverage: ' + \
                            str(len(value[categories]) - uncovered) + \
                            '/' + str(len(value[categories]))
                    rpt_str += node_level_str + '\n'
                    if detailed:
                        rpt_str += '    detail:\n'
                        for coverpoints in value[categories]:
                            rpt_str += '      - '+str(coverpoints) + ': ' + str(value[categories][coverpoints]) + '\n'
    return rpt_str

def merge_coverage(files, cgf_file, detailed, xlen):
    with open(cgf_file, "r") as file:
        cgf = expand_cgf(yaml.load(file),xlen)
    for logs in files:
        with open(logs, "r") as file:
            logs_cov = yaml.load(file)
        for cov_labels, value in logs_cov.items():
            for categories in value:
                if categories != 'config' and categories != 'opcode':
                    for coverpoints, coverage in value[categories].items():
                        if coverpoints in cgf[cov_labels][categories]:
                            cgf[cov_labels][categories][coverpoints] += coverage
    return gen_report(cgf, detailed)

def twos_complement(val,bits):
    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)
    return val

def compute_per_line(instr, commitvalue, cgf, mode, xlen, regfile, addr_pairs):
    rs1 = 0
    rs2 = 0
    rd = 0

    if xlen == 32:
        unsgn_sz = '>I'
        sgn_sz = '>i'
    else:
        unsgn_sz = '>Q'
        sgn_sz = '>q'

    if instr is None:
        return cgf,regfile

    if addr_pairs:
        if any([instr.instr_addr >= saddr and instr.instr_addr < eaddr for saddr,eaddr in addr_pairs]):
            enable = True
        else:
            enable = False
    else:
        enable=True
    if instr is not None and enable:
        if instr.rs1 is not None:
            rs1 = instr.rs1[0]
        if instr.rs2 is not None:
            rs2 = instr.rs2[0]
        if instr.rd is not None:
            rd = instr.rd[0]
        if instr.imm is not None:
            imm_val = instr.imm
        if instr.shamt is not None:
            imm_val = instr.shamt
        if instr.instr_name in ['bgeu', 'bltu', 'sltiu', 'sltu']:
            rs1_val = struct.unpack(unsgn_sz, bytes.fromhex(regfile[rs1]))[0]
        else:
            rs1_val = struct.unpack('>i', bytes.fromhex(regfile[rs1]))[0]

        if instr.instr_name in ['bgeu', 'bltu', 'sltiu', 'sltu', 'sll', 'srl', 'sra']:
            rs2_val = struct.unpack(unsgn_sz, bytes.fromhex(regfile[rs2]))[0]
        else:
            rs2_val = struct.unpack(sgn_sz, bytes.fromhex(regfile[rs2]))[0]

        if instr.instr_name in ['sw','sh','sb','lw','lhu','lh','lb','lbu']:
            ea_align = (rs1_val + imm_val) %4

        logger.debug(instr)

        for cov_labels,value in cgf.items():
            if cov_labels != 'datasets':
                if instr.instr_name == value['opcode']:
                    if 'rs1' in value and 'x'+str(rs1) in value['rs1']:
                        value['rs1']['x'+str(rs1)] += 1
                    if 'rs2' in value and 'x'+str(rs2) in value['rs2']:
                        value['rs2']['x'+str(rs2)] += 1
                    if 'rd' in value and 'x'+str(rd) in value['rd']:
                        value['rd']['x'+str(rd)] += 1
                    if 'op_comb' in value and len(value['op_comb']) != 0 :
                        for coverpoints in value['op_comb']:
                            if eval(coverpoints):
                                cgf[cov_labels]['op_comb'][coverpoints] += 1
                    if 'val_comb' in value and len(value['val_comb']) != 0 :
                        for coverpoints in value['val_comb']:
                            if eval(coverpoints):
                                cgf[cov_labels]['val_comb'][coverpoints] += 1
                    if 'abstract_comb' in value and len(value['abstract_comb']) != 0 :
                        for coverpoints in value['abstract_comb']:
                            if eval(coverpoints):
                                cgf[cov_labels]['abstract_comb'][coverpoints] += 1

        if commitvalue is not None:
            regfile[int(commitvalue[1])] =  str(commitvalue[2][2:])

    return cgf, regfile

def compute(trace_file, cgf_file, mode, detailed, xlen, addr_pairs
        , dump, cov_labels):
    '''Compute the Coverage'''
    with open(cgf_file, "r") as file:
            cgf = expand_cgf(yaml.load(file), xlen)

    if cov_labels:
        temp = {}
        for label in cov_labels:
            if label in cgf:
                temp[label] = cgf[label]
            else:
                logger.warn(label + ": Label not found in cgf file.")
        cgf = temp

    if dump is not None:
        dump_f = open(dump, 'w')
        dump_f.write(ruamel.yaml.round_trip_dump(cgf, indent=5, block_seq_indent=3))
        dump_f.close()
        sys.exit(0)

    if xlen == 32:
        regfile = ['00000000']*32
    else:
        regfile = ['0000000000000000']*32

    if mode == 'c_sail':
        with open(trace_file) as fp:
            content = fp.read()
        instructions = content.split('\n\n')
        print(len(instructions))
        for x in instructions:
            instr = helpers.parseInstruction(x, mode)
            commitvalue = helpers.extractRegisterCommitVal(x, mode)
            cgf, regfile = compute_per_line(instr, commitvalue, cgf, mode, xlen, regfile,
                    addr_pairs)
    elif mode == 'spike':
        with open(trace_file) as fp:
            for line in fp:
                instr = helpers.parseInstruction(line, mode)
                commitvalue = helpers.extractRegisterCommitVal(line, mode)
                cgf, regfile = compute_per_line(instr, commitvalue, cgf, mode, xlen, regfile,
                        addr_pairs)
    rpt_str = gen_report(cgf, detailed)
    dump_file = open(trace_file+'.cgf', 'w')
    dump_file.write(ruamel.yaml.round_trip_dump(cgf, indent=5, block_seq_indent=3))
    dump_file.close()


    return rpt_str
