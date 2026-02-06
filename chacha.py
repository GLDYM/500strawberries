import struct

rotl32 = lambda v, c: ((v << c) & 0xFFFFFFFF) | (v >> (32 - c))

def chacha_block(state):
	x = state[:]
	
	for _ in range(10):
		# quarter round on columns
		x[0], x[4], x[8], x[12] = quarter_round(x[0], x[4], x[8], x[12])
		x[1], x[5], x[9], x[13] = quarter_round(x[1], x[5], x[9], x[13])
		x[2], x[6], x[10], x[14] = quarter_round(x[2], x[6], x[10], x[14])
		x[3], x[7], x[11], x[15] = quarter_round(x[3], x[7], x[11], x[15])
		
		# diagonal
		x[0], x[5], x[10], x[15] = quarter_round(x[0], x[5], x[10], x[15])
		x[1], x[6], x[11], x[12] = quarter_round(x[1], x[6], x[11], x[12])
		x[2], x[7], x[8], x[13] = quarter_round(x[2], x[7], x[8], x[13])
		x[3], x[4], x[9], x[14] = quarter_round(x[3], x[4], x[9], x[14])
	
	for i in range(16):
		x[i] = (x[i] + state[i]) & 0xFFFFFFFF
	
	return x

def quarter_round(a, b, c, d):
	a = (a + b) & 0xFFFFFFFF
	d = rotl32(d ^ a, 16)
	c = (c + d) & 0xFFFFFFFF
	b = rotl32(b ^ c, 12)
	a = (a + b) & 0xFFFFFFFF
	d = rotl32(d ^ a, 8)
	c = (c + d) & 0xFFFFFFFF
	b = rotl32(b ^ c, 7)
	
	return a, b, c, d

def chacha20(constant, key, nonce, counter):
	# initial state
	state = [0] * 16
	
	# constants
	state[0] = struct.unpack('<I', constant[0:4])[0]
	state[1] = struct.unpack('<I', constant[4:8])[0]
	state[2] = struct.unpack('<I', constant[8:12])[0]
	state[3] = struct.unpack('<I', constant[12:16])[0]
	
	# key
	for i in range(8):
		state[4 + i] = struct.unpack('<I', key[i*4:(i+1)*4])[0]
	
	state[12] = counter & 0xFFFFFFFF # counter
	
	# nonce
	state[13] = struct.unpack('<I', nonce[0:4])[0]
	state[14] = struct.unpack('<I', nonce[4:8])[0]
	state[15] = struct.unpack('<I', nonce[8:12])[0]
	
	output_state = chacha_block(state)
	
	output = b''
	for word in output_state:
		output += struct.pack('<I', word)
	
	return output
