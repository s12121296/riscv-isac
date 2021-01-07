import time
import riscv_ctg.constants as const
from riscv_ctg.__init__ import __version__
import riscv_ctg.utils as utils_ctg
import riscv_isac.utils as utils_isac

def opcode_to_sign(opcode):							# Opcode -> Symbol present IBM Test Suite
	opcode_dict = {
		'fadd'    : '+2',
		'fsub'    : '-2',
		'fmul'    : '*2',
		'fdiv'    : '/2',
		'fmadd'   : '*+3',
		'fsqrt'   : 'V1',
		'fmin'    : '<C1',
		'fmax'    : '>C1',
		'fcvt.w.s': 'cfi1',
		'fcvt.s.w': 'cif1',
		'fmv.x.w' : 'cp1',
		'fmv.w.x' : 'cp1'
	}
	return(opcode_dict.get(opcode,"Invalid Opcode"))

def rounding_mode(rm):								# Rounding Mode -> Decimal Equivalent
	rm_dict = {
		'=0' : '0',
		'>'  : '3',
		'<'  : '2',
		'0'  : '1',
		'=^' : '4'
	}
	return(rm_dict.get(rm))
	
def flags_to_dec(flags):							# Flags -> Decimal Equivalent
	field_val=0
	for char in flags:
		if(char == 'x'): 
			field_val += 1
		elif(char == 'u'): 
			field_val += 2
		elif(char == 'o'): 
			field_val += 4
		elif(char == 'z'): 
			field_val += 8
		elif(char == 'i'): 
			field_val += 16
		else: 
			field_val += 0
	return(str(field_val));

def floatingPoint_tohex(float_no): 						# IEEE754 Floating point -> Hex representation
	if(float_no=="+Zero"):
		th = "0x00000000"
		res = th[2:10]
		return(str(int(res,16)))
	elif(float_no=="-Zero"):
		th = "0x80000000"
		res = th[2:10]
		return(str(int(res,16)))
	elif(float_no=="+Inf"):
		th = "0x7F800000"
		res = th[2:10]
		return(str(int(res,16)))
	elif(float_no=="-Inf"):
		th = "0xFF800000"
		res = th[2:10]
		return(str(int(res,16)))
	elif(float_no=="Q"):
		th = "0xFF800001"
		res = th[2:10]
		return(str(int(res,16)))
	elif(float_no=="S"):
		return "1000"
	elif(float_no=="#"):
		return "#"
		
	real_no=float.fromhex(float_no)
	sign_bit = 0
	if(real_no < 0): 
		sign_bit = 1
	real_no = abs(real_no)

	int_str = bin(int(real_no))[2 : ] 

	fraction=(real_no - int(real_no))
	
	binary = str() 
	while (fraction): 
		fraction *= 2
		if (fraction >= 1): 
			int_part = 1
			fraction -= 1
		else: 
			int_part = 0
		binary += str(int_part) 
		if(len(binary)>=23):
			break
	
	fraction_str = binary
	
	exp_str = bin((len(int_str) - 1) + 127)[2 : ] 

	exp_str = ('0' * (8 - len(exp_str))) + exp_str
	 
	mant_str = int_str[1 : ] + fraction_str 

	mant_str = mant_str + ('0' * (23 - len(mant_str)))

	tohex = hex(int(str(sign_bit) + exp_str + mant_str,2))
	
	b = tohex[2:10]
	
	return str(int(b,16))
	
def coverpoints_format(ops, rs1=None, rs2=None, rs3=None, rm=None):
	coverpoints = []
	if(ops==2):
		for i in range(len(rs1)):
			coverpoints.append('rs1_val=='+ rs1[i] + ' and ' + 'rs2_val==' + rs2[i] + ' and ' + 'rm_val==' + rm[i])
	elif(ops==1):
		for i in range(len(rs1)):
			coverpoints.append('rs1_val=='+ rs1[i] + ' and ' + 'rm_val==' + rm[i])
	elif(ops==3):
		for i in range(len(rs1)):
			coverpoints.append('rs1_val=='+ rs1[i] + ' and ' + 'rs2_val==' + rs2[i] + ' and ' + 'rs3_val==' + rs2[i] + ' and ' + 'rm_val==' + rm[i])
	return(coverpoints)

def gen_fp_cpts(flen, opcode):
	opcode=opcode.lower()
	rs1_dataset=[]								# Declaring empty datasets
	rs2_dataset=[]
	rs3_dataset=[]
	rm_dataset=[]
	rd_dataset=[]
	te_dataset=[]
	flags_dataset=[]
	
	f=open("Basic-Types-Inputs.fptest","r")
	for i in range(5):
		a=f.readline()
	
	i=0									# Initializing count of datapoints
	sign_ops=opcode_to_sign(opcode)
	if(sign_ops=="Invalid Opcode"):
		print("Invalid Opcode!!!")
		exit()
	sign=sign_ops[0:len(sign_ops)-1]
	ops=int(sign_ops[len(sign_ops)-1])
	if(flen!=32 and flen!=64):
		print("Invalid flen value!!!")
		exit()
	
	while a!="":
		l=a.split()							#['b32?f', '=0', 'i', '-1.7FFFFFP127', '->', '0x1']
		d_sign=l[0][3:]
		d_flen=int(l[0][1:3])
		d_rm=l[1]
		
		if(sign==d_sign and flen==d_flen):			
			rm_dataset.append(rounding_mode(d_rm))
			if(ops==2):					
				if(l[4]!='->'):				#b32+ =0 i +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127 x
					rs2_dataset.append(floatingPoint_tohex(l[4]))
					rs1_dataset.append(floatingPoint_tohex(l[3]))
					rd_dataset.append(floatingPoint_tohex(l[6]))
					te_dataset.append(l[2])
					if(len(l)-1==6):			#b32+ =0 i +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127
						flags_dataset.append('0')
					else:					#b32+ =0 i +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127 x
						flags_dataset.append(flags_to_dec(l[len(l)-1]))
				else:						#b32+ =0 +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127 x
					rs2_dataset.append(floatingPoint_tohex(l[3]))
					rs1_dataset.append(floatingPoint_tohex(l[2]))
					rd_dataset.append(floatingPoint_tohex(l[5]))
					te_dataset.append("")
					if(len(l)-1==5):			#b32+ =0 +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127
						flags_dataset.append('0')
					else:					#b32+ =0 +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127 x
						flags_dataset.append(flags_to_dec(l[len(l)-1]))
			elif(ops==1):
				if(l[3]!='->'):				#b32V =0 i +1.7FFFFFP127 -> +1.7FFFFFP63 x
					rs1_dataset.append(floatingPoint_tohex(l[3]))
					rd_dataset.append(floatingPoint_tohex(l[5]))
					te_dataset.append(l[2])
					if(len(l)-1==5):			#b32V =0 i +1.7FFFFFP127 -> +1.7FFFFFP63
						flags_dataset.append('0')
					else:					#b32V =0 i +1.7FFFFFP127 -> +1.7FFFFFP63 x
						flags_dataset.append(flags_to_dec(l[len(l)-1]))
				else:						#b32V =0 +0.7FFFFFP-126 -> +1.7FFFFFP-64 x
					rs1_dataset.append(floatingPoint_tohex(l[2]))
					rd_dataset.append(floatingPoint_tohex(l[4]))
					te_dataset.append("")
					if(len(l)-1==4):			#b32V =0 +1.7FFFFFP127 -> +1.7FFFFFP63
						flags_dataset.append('0')
					else:					#b32V =0 +1.7FFFFFP127 -> +1.7FFFFFP63 x
						flags_dataset.append(flags_to_dec(l[len(l)-1]))
			elif(ops==3): 
				if(l[5]!='->'):				#b32*+ =0 i -1.000000P-126 -1.19BD32P52 -Inf -> -Inf
	
					rs3_dataset.append(floatingPoint_tohex(l[5]))
					rs2_dataset.append(floatingPoint_tohex(l[4]))
					rs1_dataset.append(floatingPoint_tohex(l[3]))
					rd_dataset.append(floatingPoint_tohex(l[7]))
					te_dataset.append(l[2])
					if(len(l)-1==7):			#b32*+ =0 i -1.000000P-126 -1.19BD32P52 -Inf -> -Inf
						flags_dataset.append('0')
					else:					#b32*+ =0 i -1.000000P-126 -1.19BD32P52 -Inf -> -Inf x
						flags_dataset.append(flags_to_dec(l[len(l)-1]))
				else:						#b32*+ =0 -1.000000P-126 -1.19BD32P52 -Inf -> -Inf 
				
					rs3_dataset.append(floatingPoint_tohex(l[4]))
					rs2_dataset.append(floatingPoint_tohex(l[3]))
					rs1_dataset.append(floatingPoint_tohex(l[2]))
					rd_dataset.append(floatingPoint_tohex(l[6]))
					te_dataset.append("")
					if(len(l)-1==6):			#b32*+ =0 -1.000000P-126 -1.19BD32P52 -Inf -> -Inf
						flags_dataset.append('0')
					else:					#b32*+ =0 -1.000000P-126 -1.19BD32P52 -Inf -> -Inf x
						flags_dataset.append(flags_to_dec(l[len(l)-1]))
		i=i+1
		a=f.readline()
	
	if(ops==2):
		#return rs1_dataset,rs2_dataset,rd_dataset,rm_dataset,te_dataset,flags_dataset
		cpts = coverpoints_format(ops,rs1_dataset,rs2_dataset,'',rm_dataset)
	elif(ops==1):
		#return rs1_dataset,rd_dataset,rm_dataset,te_dataset,flags_dataset
		cpts = coverpoints_format(ops,rs1_dataset,'','',rm_dataset)
	elif(ops==3):
		#return rs1_dataset,rs2_dataset,rs3_dataset,rd_dataset,rm_dataset,te_dataset,flags_dataset
		cpts = coverpoints_format(ops,rs1_dataset,rs2_dataset,rs3_dataset,rm_dataset)
	return cpts

def gen_fp_dataset(flen, opcode,n):
	opcode=opcode.lower()
	rs1_dataset=[]								# Declaring empty datasets
	rs2_dataset=[]
	rs3_dataset=[]
	rm_dataset=[]
	rd_dataset=[]
	te_dataset=[]
	flags_dataset=[]
	
	f=open("Basic-Types-Inputs.fptest","r")
	for i in range(5):
		a=f.readline()
	
	i=0									# Initializing count of datapoints
	sign_ops=opcode_to_sign(opcode)
	if(sign_ops=="Invalid Opcode"):
		print("Invalid Opcode!!!")
		exit()
	sign=sign_ops[0:len(sign_ops)-1]
	ops=int(sign_ops[len(sign_ops)-1])
	if(flen!=32 and flen!=64):
		print("Invalid flen value!!!")
		exit()
	
	while a!="":
		l=a.split()							#['b32?f', '=0', 'i', '-1.7FFFFFP127', '->', '0x1']
		d_sign=l[0][3:]
		d_flen=int(l[0][1:3])
		d_rm=l[1]
		
		if(sign==d_sign and flen==d_flen):			
			rm_dataset.append(rounding_mode(d_rm))
			if(ops==2):					
				if(l[4]!='->'):				#b32+ =0 i +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127 x
					rs2_dataset.append(floatingPoint_tohex(l[4]))
					rs1_dataset.append(floatingPoint_tohex(l[3]))
					rd_dataset.append(floatingPoint_tohex(l[6]))
					te_dataset.append(l[2])
					if(len(l)-1==6):			#b32+ =0 i +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127
						flags_dataset.append('0')
					else:					#b32+ =0 i +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127 x
						flags_dataset.append(flags_to_dec(l[len(l)-1]))
				else:						#b32+ =0 +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127 x
					rs2_dataset.append(floatingPoint_tohex(l[3]))
					rs1_dataset.append(floatingPoint_tohex(l[2]))
					rd_dataset.append(floatingPoint_tohex(l[5]))
					te_dataset.append("")
					if(len(l)-1==5):			#b32+ =0 +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127
						flags_dataset.append('0')
					else:					#b32+ =0 +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127 x
						flags_dataset.append(flags_to_dec(l[len(l)-1]))
			elif(ops==1):
				if(l[3]!='->'):				#b32V =0 i +1.7FFFFFP127 -> +1.7FFFFFP63 x
					rs1_dataset.append(floatingPoint_tohex(l[3]))
					rd_dataset.append(floatingPoint_tohex(l[5]))
					te_dataset.append(l[2])
					if(len(l)-1==5):			#b32V =0 i +1.7FFFFFP127 -> +1.7FFFFFP63
						flags_dataset.append('0')
					else:					#b32V =0 i +1.7FFFFFP127 -> +1.7FFFFFP63 x
						flags_dataset.append(flags_to_dec(l[len(l)-1]))
				else:						#b32V =0 +0.7FFFFFP-126 -> +1.7FFFFFP-64 x
					rs1_dataset.append(floatingPoint_tohex(l[2]))
					rd_dataset.append(floatingPoint_tohex(l[4]))
					te_dataset.append("")
					if(len(l)-1==4):			#b32V =0 +1.7FFFFFP127 -> +1.7FFFFFP63
						flags_dataset.append('0')
					else:					#b32V =0 +1.7FFFFFP127 -> +1.7FFFFFP63 x
						flags_dataset.append(flags_to_dec(l[len(l)-1]))
			elif(ops==3): 
				if(l[5]!='->'):				#b32*+ =0 i -1.000000P-126 -1.19BD32P52 -Inf -> -Inf
	
					rs3_dataset.append(floatingPoint_tohex(l[5]))
					rs2_dataset.append(floatingPoint_tohex(l[4]))
					rs1_dataset.append(floatingPoint_tohex(l[3]))
					rd_dataset.append(floatingPoint_tohex(l[7]))
					te_dataset.append(l[2])
					if(len(l)-1==7):			#b32*+ =0 i -1.000000P-126 -1.19BD32P52 -Inf -> -Inf
						flags_dataset.append('0')
					else:					#b32*+ =0 i -1.000000P-126 -1.19BD32P52 -Inf -> -Inf x
						flags_dataset.append(flags_to_dec(l[len(l)-1]))
				else:						#b32*+ =0 -1.000000P-126 -1.19BD32P52 -Inf -> -Inf 
				
					rs3_dataset.append(floatingPoint_tohex(l[4]))
					rs2_dataset.append(floatingPoint_tohex(l[3]))
					rs1_dataset.append(floatingPoint_tohex(l[2]))
					rd_dataset.append(floatingPoint_tohex(l[6]))
					te_dataset.append("")
					if(len(l)-1==6):			#b32*+ =0 -1.000000P-126 -1.19BD32P52 -Inf -> -Inf
						flags_dataset.append('0')
					else:					#b32*+ =0 -1.000000P-126 -1.19BD32P52 -Inf -> -Inf x
						flags_dataset.append(flags_to_dec(l[len(l)-1]))
		i=i+1
		a=f.readline()

	if(n==1):
		return rs1_dataset
	elif(n==2):
		return rs2_dataset
	elif(n==3):
		return rm_dataset

def expand_cgf(cgf_files, flen):
    '''
    This function will replace all the abstract functions with their unrolled
    coverpoints

    :param cgf_files: list of yaml file paths which together define the coverpoints
    :param xlen: XLEN of the riscv-trace

    :type cgf: list
    :type xlen: int
    '''
    
    cgf = utils_isac.load_cgf(cgf_files)
    for labels, cats in tuple(cgf.items()):
        if labels!='datasets':
            for label,node in cats.items():
                if isinstance(node,dict):
                    if 'abstract_comb' in node:
                        temp = cgf[labels][label]['abstract_comb']
                        del cgf[labels][label]['abstract_comb']
                        coverpoints, coverage = tuple(temp.items())[0]
                        exp_cp = eval(coverpoints)
                        
                        for e in exp_cp:
                            cgf[labels][label][e] = coverage
    return cgf

