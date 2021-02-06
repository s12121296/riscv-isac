# See LICENSE.iitm for details

from riscv_isac.constants import *
from riscv_isac.log import logger
import os

def opcode_to_sign(opcode):								# Opcode -> Symbol present IBM Test Suite
	opcode_dict = {
		'fadd'    : '+2',
		'fsub'    : '-2',
		'fmul'    : '*2',
		'fdiv'    : '/2',
		'fmadd'   : '*+3',
		'fsqrt'   : 'V1',
		'fmin'    : '<C2',
		'fmax'    : '>C2',
		'fcvt.w.s': 'cfi1',
		'fcvt.s.w': 'cif1',
		'fmv.x.w' : 'cp1',
		'fmv.w.x' : 'cp1'
	}
	return(opcode_dict.get(opcode,"Invalid Opcode"))

def rounding_mode(rm):									# Rounding Mode -> Decimal Equivalent
	rm_dict = {
		'=0' : '0',
		'>'  : '3',
		'<'  : '2',
		'0'  : '1',
		'=^' : '4'
	}
	return(rm_dict.get(rm))
	
def flags_to_dec(flags):								# Flags -> Decimal Equivalent
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

def floatingPoint_tohex(float_no): 							# IEEE754 Floating point -> Hex representation
	
	if(float_no=="+Zero"):
		th = "0x00000000"
		return th
	elif(float_no=="-Zero"):
		th = "0x80000000"
		return th
	elif(float_no=="+Inf"):
		th = "0x7f800000"
		return th
	elif(float_no=="-Inf"):
		th = "0xff800000"
		return th
	elif(float_no=="Q"):
		th = "0xff800001"
		return th
	elif(float_no=="S"):
		return "0xff8fffff"
	elif(float_no=="#"):
		return "#"
	num="N"
	
	a=float.fromhex(float_no)
	sign=0
	if(a<0):
		sign=1
	nor=float.hex(a)								# Normalized Number
	
	if(int(nor.split("p")[1])<-126):						# Checking Underflow of Exponent
			exp_bin=('0'*8)						# Exponent of Subnormal numbers
			num="SN"
	elif(int(nor.split("p")[1])>127):						# Checking Overflow of Exponent
		if(sign==0):
			return "0x7f7fffff"						# Most Positive Value
		else:
			return "0xff7fffff"						# Most Negative Value
	else:										# Converting Exponent to 8-Bit Binary
		exp=int(nor.split("p")[1])+127
		exp_bin=('0'*(8-(len(bin(exp))-2)))+bin(exp)[2:]
	
	if(num=="SN"):
		mant="0x"+float_no.split("P")[0][3:]
	else:
		if(sign==0):
			mant="0x"+nor.split("p")[0][4:]
		else:
			mant="0x"+nor.split("p")[0][5:]

	mant_bin=bin(int(mant,16))[2:]+('0'*(52-(len(bin(int(mant,16)))-2)))
	
	binary="0b"
	binary=binary+str(sign)+exp_bin+mant_bin[0:23]
	
	hex_tp=hex(int(binary,2))
	hex_tp=hex_tp.replace('0x','0x'+'0'*(10-len(hex_tp)))

	return(hex_tp)

		
def coverpoints_format(ops, rs1=None, rs2=None, rs3=None, rm=None):
	coverpoints = []
	if(ops==2):
		for i in range(len(rs1)):
			coverpoints.append('rs1_val=='+ rs1[i] + ' and ' + 'rs2_val==' + rs2[i] + ' and ' + 'rm_val==' + rm[i])
			#print(coverpoints[i])
	elif(ops==1):
		for i in range(len(rs1)):
			coverpoints.append('rs1_val=='+ rs1[i] + ' and ' + 'rm_val==' + rm[i])
	elif(ops==3):
		for i in range(len(rs1)):
			coverpoints.append('rs1_val=='+ rs1[i] + ' and ' + 'rs2_val==' + rs2[i] + ' and ' + 'rs3_val==' + rs2[i] + ' and ' + 'rm_val==' + rm[i])
	return(coverpoints)

def stats(x):
	d = {}
	for i in range(len(x)):
		if(d.get(x[i],"None") == "None"):
			d[x[i]] = 1
		else:
			d[x[i]]+=1
	#print(d)
	#print()
	return(len(d))

def gen_fp_dataset(flen, opcode):
	opcode=opcode.lower()
	rs1_dataset=[]									# Declaring empty datasets
	rs2_dataset=[]
	rs3_dataset=[]
	rm_dataset=[]
	rd_dataset=[]
	te_dataset=[]
	flags_dataset=[]
	count=0									# Initializing count of datapoints
	path_parent = os.path.dirname(os.getcwd())
	os.chdir(path_parent)
	opcode=opcode.split(".")[0]
	for filename in os.listdir(root+'/test_suite'):
		f=open(os.path.join(root+'/test_suite', filename), "r")
		for i in range(5):
			a=f.readline()
			
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
			l=a.split()						#['b32?f', '=0', 'i', '-1.7FFFFFP127', '->', '0x1']
			d_sign=l[0][3:]
			d_flen=int(l[0][1:3])
			d_rm=l[1]
			
			if(sign==d_sign and flen==d_flen):			
				rm_dataset.append(rounding_mode(d_rm))
				if(ops==2):						
					if(l[4]!='->'):			#b32+ =0 i +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127 x
						rs2_dataset.append(floatingPoint_tohex(l[4]))
						rs1_dataset.append(floatingPoint_tohex(l[3]))
						rd_dataset.append(floatingPoint_tohex(l[6]))
						te_dataset.append(l[2])
						if(len(l)-1==6):		#b32+ =0 i +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127
							flags_dataset.append('0')
						else:				#b32+ =0 i +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127 x
							flags_dataset.append(flags_to_dec(l[len(l)-1]))
					else:					#b32+ =0 +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127 x
						rs2_dataset.append(floatingPoint_tohex(l[3]))
						rs1_dataset.append(floatingPoint_tohex(l[2]))
						rd_dataset.append(floatingPoint_tohex(l[5]))
						te_dataset.append("")
						if(len(l)-1==5):		#b32+ =0 +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127
							flags_dataset.append('0')
						else:				#b32+ =0 +0.000001P-126 -1.7FFFFFP127 -> -1.7FFFFFP127 x
							flags_dataset.append(flags_to_dec(l[len(l)-1]))
				elif(ops==1):
					if(l[3]!='->'):			#b32V =0 i +1.7FFFFFP127 -> +1.7FFFFFP63 x
						rs1_dataset.append(floatingPoint_tohex(l[3]))
						rd_dataset.append(floatingPoint_tohex(l[5]))
						te_dataset.append(l[2])
						if(len(l)-1==5):		#b32V =0 i +1.7FFFFFP127 -> +1.7FFFFFP63
							flags_dataset.append('0')
						else:				#b32V =0 i +1.7FFFFFP127 -> +1.7FFFFFP63 x
							flags_dataset.append(flags_to_dec(l[len(l)-1]))
					else:					#b32V =0 +0.7FFFFFP-126 -> +1.7FFFFFP-64 x
						rs1_dataset.append(floatingPoint_tohex(l[2]))
						rd_dataset.append(floatingPoint_tohex(l[4]))
						te_dataset.append("")
						if(len(l)-1==4):		#b32V =0 +1.7FFFFFP127 -> +1.7FFFFFP63
							flags_dataset.append('0')
						else:				#b32V =0 +1.7FFFFFP127 -> +1.7FFFFFP63 x
							flags_dataset.append(flags_to_dec(l[len(l)-1]))
				elif(ops==3): 
					if(l[5]!='->'):			#b32*+ =0 i -1.000000P-126 -1.19BD32P52 -Inf -> -Inf
		
						rs3_dataset.append(floatingPoint_tohex(l[5]))
						rs2_dataset.append(floatingPoint_tohex(l[4]))
						rs1_dataset.append(floatingPoint_tohex(l[3]))
						rd_dataset.append(floatingPoint_tohex(l[7]))
						te_dataset.append(l[2])
						if(len(l)-1==7):		#b32*+ =0 i -1.000000P-126 -1.19BD32P52 -Inf -> -Inf
							flags_dataset.append('0')
						else:				#b32*+ =0 i -1.000000P-126 -1.19BD32P52 -Inf -> -Inf x	
							flags_dataset.append(flags_to_dec(l[len(l)-1]))
					else:					#b32*+ =0 -1.000000P-126 -1.19BD32P52 -Inf -> -Inf 
					
						rs3_dataset.append(floatingPoint_tohex(l[4]))
						rs2_dataset.append(floatingPoint_tohex(l[3]))
						rs1_dataset.append(floatingPoint_tohex(l[2]))
						rd_dataset.append(floatingPoint_tohex(l[6]))
						te_dataset.append("")
						if(len(l)-1==6):		#b32*+ =0 -1.000000P-126 -1.19BD32P52 -Inf -> -Inf
							flags_dataset.append('0')
						else:				#b32*+ =0 -1.000000P-126 -1.19BD32P52 -Inf -> -Inf x
							flags_dataset.append(flags_to_dec(l[len(l)-1]))
			count=count+1
			a=f.readline()
	mess='Iterated through '+ str(count) + ' lines of Test-cases in IBM Test Suite for '+ str(opcode) +' opcode to extract '+str(len(rs1_dataset))+' Test-points!'
	logger.info(mess)
	if(ops==2):
		cpts = coverpoints_format(ops,rs1_dataset,rs2_dataset,'',rm_dataset)
	elif(ops==1):
		cpts = coverpoints_format(ops,rs1_dataset,'','',rm_dataset)
	elif(ops==3):
		cpts = coverpoints_format(ops,rs1_dataset,rs2_dataset,rs3_dataset,rm_dataset)
	return cpts

