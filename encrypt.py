import os
import math
import hmac
import json
import hashlib
import lz4.block
from mt import init_mt, prng_iter
from common import crc, compute_rounds, array_cipher
from decrypt import FORMATS, DEFAULT_FORMAT, triangleIndices, extractConst

def encryptSave(jsonData, crypto=None):
	lz4_payload = bytearray()

	### LZ4 ###
	# must match the game's serializer exactly, otherwise bytes (and file size) differ
	save = json.dumps(jsonData, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

	# must follow this config to respect game's lz4
	compressed = lz4.block.compress(save, store_size=False, mode='default', compression=0)

	decompressed_size = len(save)
	compressed_size = len(compressed)

	print(f"* decompressed size : {decompressed_size} | compressed size : {compressed_size}")

	lz4_payload += decompressed_size.to_bytes(4, "little")
	lz4_payload += compressed_size.to_bytes(4, "little")
	lz4_payload += compressed

	### FORMAT ###
	format_name = crypto["format"] if crypto else DEFAULT_FORMAT
	if format_name not in FORMATS:
		raise Exception(f"> unknown save format : {format_name}")

	format = FORMATS[format_name]
	km_size = format["key_material_size"]
	idx = triangleIndices(format["step"], 16)

	print(f"* format : {format_name} (key material {km_size} bytes)")

	### ENCRYPT ###
	if crypto is None:
		nonce = os.urandom(12)
		chacha_const = format["const"]
		chacha_key = os.urandom(32)
	else:
		# reuse the original file's material : it must stay consistent with it
		nonce = bytes(crypto["nonce"])
		chacha_const = bytes(crypto["chacha_const"])
		chacha_key = bytes(crypto["chacha_key"])

	original_nonce = nonce

	print(f"\n* nonce : {nonce.hex()}")
	print(f"* chacha const : {chacha_const.hex()}")
	print(f"* chacha key : {chacha_key.hex()}")

	mt = init_mt()

	print("> generating mt table...")
	warmup_rounds = compute_rounds(nonce)
	print(f"* warmup rounds {hex(warmup_rounds)}")

	for _ in range(warmup_rounds):
		prng_iter(mt)

	enc = bytearray()
	enc += lz4_payload

	print(f"* lz4 payload size : {len(enc)}")

	n_blocks = math.ceil(len(enc) / 64)
	print(f"{n_blocks} blocks")

	array_cipher(enc, chacha_const, chacha_key, nonce, mt)

	### HMAC ###
	if crypto is None:
		hmac_key = os.urandom(64)
	else:
		hmac_key = bytes(crypto["hmac_key"])

	hmac_payload = bytearray()
	hmac_payload += hmac_key
	hmac_payload += original_nonce
	hmac_payload += chacha_key
	hmac_payload += enc

	hmac_val = hmac.new(hmac_key, hmac_payload, hashlib.sha256).digest()
	print(f"* hmac : {hmac_val.hex()}")
	hmac_payload += hmac_val

	### KEY MATERIAL ###
	if crypto is None:
		key_material = bytearray(os.urandom(km_size))
	else:
		key_material = bytearray(crypto["key_material"])

	if len(key_material) != km_size:
		raise Exception(f"> key material must be {km_size} bytes for {format_name}")

	# the game checks these bytes against a hardcoded const
	for i, val in zip(idx, chacha_const):
		key_material[i] = val

	### CRC ###
	crc_payload = bytearray()
	crc_payload += key_material
	crc_payload += len(hmac_payload).to_bytes(4, "little")
	crc_payload += hmac_payload

	file_crc = crc(crc_payload)
	print(f"* crc : {file_crc}")

	final_payload = bytearray()
	final_payload += file_crc.to_bytes(4, "little", signed=False)
	final_payload += crc_payload

	return final_payload
