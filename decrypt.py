import math
import hmac
import json
import hashlib
import lz4.block
from mt import init_mt, prng_iter
from common import crc, compute_rounds, array_cipher

# Save container formats.
#   v1 : 3.28.x and older -> 255-byte key material, chacha const spread with step 1
#   v2 : 3.29.x and newer -> 65535-byte key material, chacha const spread with step 5
# The const values below are the ones hardcoded in the game (checked after loading),
# so key material has to be built around them.
FORMATS = {
	"v1": {
		"key_material_size": 0xFF,
		"step": 1,
		"const": bytes.fromhex("4396a58e6493b492d58bfc94e28de48c"),
	},
	"v2": {
		"key_material_size": 0xFFFF,
		"step": 5,
		"const": bytes.fromhex("ac88b68f9d975390468b809149964890"),
	},
}

DEFAULT_FORMAT = "v2"  # what the current game version (3.29.x) writes

def triangleIndices(step, count):
	# 1, 1+(step+1), +((step+1)+step), ... : the spread the game uses
	out = []
	idx = 1
	gap = step + 1
	while len(out) < count:
		out.append(idx)
		idx += gap
		gap += step
	return out

def extractConst(key_material, step, count=16):
	idx = triangleIndices(step, count)
	if idx[-1] >= len(key_material):
		return None
	return bytes(key_material[i] for i in idx)

def detectFormat(saveData):
	# same discrimination as the game: which hardcoded const does the key
	# material produce?
	body = saveData[4:]
	for name in ("v1", "v2"):
		f = FORMATS[name]
		if extractConst(body, f["step"]) == f["const"]:
			return name

	# fall back to the payload size field (covers files we generated ourselves)
	for name in ("v1", "v2"):
		size = FORMATS[name]["key_material_size"]
		if len(saveData) < size + 8:
			continue
		if int.from_bytes(saveData[4+size:8+size], "little") == len(saveData) - (size + 8):
			return name

	return None

def decryptSave(saveData):
	# Offset          Size   Name
	# ----------------------------------------------------------
	# 0x0             4      CRC32
	# 0x4             K      ChaCha Key Material
	# 0x4+K           4      Payload size (N)
	# 0x8+K           64     HMAC Key
	# 0x48+K          12     ChaCha Nonce seed
	# 0x54+K          32     ChaCha Key
	# 0x74+K          4      Decompressed size
	# 0x78+K          4      Compressed size M
	# 0x7C+K          M      LZ4 Compressed JSON
	# 0x7C+K+M        32     HMAC digest
	# K is 255 for v1 and 65535 for v2

	### CRC ###
	file_crc = int.from_bytes(saveData[0:4], "little", signed=False)
	data_crc = crc(saveData[4:])

	print(f"* file crc : {hex(file_crc)}")
	print(f"* computed crc : {hex(data_crc)} | {data_crc}")

	if file_crc != data_crc:
		raise Exception("> crc mismatch !")
	print("> crc match !")

	### FORMAT ###
	format_name = detectFormat(saveData)
	if format_name is None:
		raise Exception("> unknown save format !")

	format = FORMATS[format_name]
	km_size = format["key_material_size"]
	print(f"* format : {format_name} (key material {km_size} bytes)")

	### HEADER ###
	key_material = saveData[4:4+km_size]
	payload_size = int.from_bytes(saveData[4+km_size:8+km_size], "little")
	print(f"* payload size : {payload_size}")

	if len(saveData) - (8 + km_size) != payload_size:
		raise Exception("> payload size mismatch !")

	payload = saveData[8+km_size:8+km_size+payload_size]

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
	chacha_const = extractConst(key_material, format["step"])
	if chacha_const is None:
		raise Exception("> key material too short !")

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

def readCrypto(saveData):
	# extract the crypto material out of a .ojs file without decrypting it,
	# so it can be fed back to encryptSave() and kept consistent with the original
	if len(saveData) < 8:
		return None

	file_crc = int.from_bytes(saveData[0:4], "little", signed=False)
	if crc(saveData[4:]) != file_crc:
		return None

	format_name = detectFormat(saveData)
	if format_name is None:
		return None

	format = FORMATS[format_name]
	km_size = format["key_material_size"]
	if len(saveData) < km_size + 8:
		return None

	payload_size = int.from_bytes(saveData[4+km_size:8+km_size], "little")
	if payload_size < 140 or len(saveData) - (8 + km_size) != payload_size:
		return None

	key_material = saveData[4:4+km_size]
	payload = saveData[8+km_size:8+km_size+payload_size]

	return {
		"format": format_name,
		"nonce": bytes(payload[64:76]),
		"chacha_key": bytes(payload[76:108]),
		"hmac_key": bytes(payload[0:64]),
		"chacha_const": extractConst(key_material, format["step"]),
		"key_material": bytes(key_material),
	}
