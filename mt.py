def init_mt():
	# layout: [index, state[0..623], ...padding (v51)..., magic_constant]
	mt = [0] * 1250
	mt[0] = 624  # index
	mt[1249] = 0xFFFFFFFF  # end

	# initial state
	mt[1] = 5489
	for i in range(1, 624):
		prev = mt[i]
		mt[i + 1] = (1812433253 * (prev ^ (prev >> 30)) + i) & 0xFFFFFFFF
	mt[0] = 624

	return mt

def prng_iter(mt, extract = False):
	idx = mt[0]

	if idx == 624:
		for i in range(624):
			mt[i + 625] = mt[i + 398] ^ twist_pair(mt[i + 1], mt[i + 2])
	elif idx >= 0x4E0:
		twist_extended(mt)

	idx = mt[0]

	if extract:
		MASK = 0xFFFFFFFF

		v12 = mt[idx + 1] & MASK
		mt[0] = (idx + 1) & MASK

		t = (v12 ^ (mt[1249] & (v12 >> 11))) & MASK
		t = (t ^ ((t & 0xFF3A58AD) << 7)) & MASK
		t = (t ^ ((t & 0xFFFFDF8C) << 15)) & MASK
		return (t ^ (t >> 18)) & MASK
	else:
		mt[0] += 1

def twist_extended(mt):
	for i in range(227):
		src = 626 + i
		t = twist_pair(mt[src - 1], mt[src])
		mt[i + 1] = mt[src + 396] ^ t

	for i in range(396):
		src = 853 + i
		t = twist_pair(mt[src - 1], mt[src])
		mt[i + 228] = mt[src - 852] ^ t

	t = twist_pair(mt[1248], mt[1])
	mt[624] = mt[397] ^ t

	mt[0] = 0 # reset

def twist_pair(a: int, b: int):
	x = (a & 0x80000000) | (b & 0x7FFFFFFF)
	x >>= 1
	if b & 1:
		x ^= 0x9908B0DF
	return x
