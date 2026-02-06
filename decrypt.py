import math
import hmac
import json
import hashlib
import lz4.block
from mt import init_mt, prng_iter
from common import crc, compute_rounds, array_cipher

def decryptSave(saveData):
	# Offset		Size 		Name
	# ---------------------------------------------- 
	# 0x0			4 			CRC32
	# 0x4 			255 		ChaCha Key Material
	# 0x103			4 			Payload size
	# 0x107			64 			HMAC Key
	# 0x147 		12 			ChaCha Nonce seed
	# 0x153 		32 			ChaCha Key
	# 0x173			4 			Decompressed size
	# 0x177 		4 			Compressed size N
	# 0x17b 		N			LZ4 Compressed JSON
	# 0x17b+N		32 			HMAC Hex Digest

	### CRC ###
	file_crc = int.from_bytes(saveData[0:4], "little", signed=False)
	data_crc = crc(saveData[4:])

	print(f"* file crc : {hex(file_crc)}")
	print(f"* computed crc : {hex(data_crc)} | {data_crc}")

	if file_crc != data_crc:
		raise Exception("> crc mismatch !")
	print("> crc match !")

	### HEADER ###
	key_material = saveData[4:259]
	payload_size = int.from_bytes(saveData[259:263], "little")
	print(f"* payload size : {payload_size}")

	if len(saveData) - 263 != payload_size:
		raise Exception("> payload size mismatch !")

	payload = saveData[263:263+payload_size]

	### HMAC ###
	hmac_key = payload[0:64]
	hmac_res = payload[payload_size-32:payload_size]
	nonce = payload[64:76]
	chacha_key = payload[76:108]

	enc = payload[108:payload_size-32]

	print(f"* hmac key : {hmac_key.hex()}")
	hmac_check = hmac.new(hmac_key, payload[:-32], hashlib.sha256).hexdigest()
	print(f"* hmac check : {hmac_check}")

	if hmac_check != hmac_res.hex():
		raise Exception("> invalid hmac !")
	print("> hmac match !")

	### DECRYPT ###
	# key material
	idx = [1,3,6,10, 15,21,28,36, 45,55,66,78, 91,105,120,136] # 4x4
	chacha_const = bytes(key_material[i] for i in idx)

	print(f"\n* nonce : {nonce.hex()}")
	print(f"* chacha const : {chacha_const.hex()}")
	print(f"* chacha key : {chacha_key.hex()}")

	mt = init_mt()
	print("> generating mt table...")
	warmup_rounds = compute_rounds(nonce)
	print(f"* warmup rounds {hex(warmup_rounds)}")

	for _ in range(warmup_rounds):
		prng_iter(mt)

	dec = bytearray()
	dec += enc

	print(f"* lz4 payload size : {len(dec)}")

	n_blocks = math.ceil(len(enc) / 64)
	print(f"{n_blocks} blocks")

	array_cipher(dec, chacha_const, chacha_key, nonce, mt)

	### LZ4 ###
	dst_size = int.from_bytes(dec[0:4], "little")
	src_size = int.from_bytes(dec[4:8], "little")

	print(f"* src size : {src_size} | dst size : {dst_size}")

	dec = dec[8:8+src_size]
	decompressed = lz4.block.decompress(dec, uncompressed_size=dst_size)

	save = json.loads(decompressed.decode("utf-8"))

	return save
