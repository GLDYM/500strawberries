import os
import sys
import json
from decrypt import decryptSave, readCrypto
from encrypt import encryptSave

def main():
	if len(sys.argv) != 3:
		print("usage: main.py <decrypt|encrypt> <file>")
		sys.exit(1)

	mode = sys.argv[1]
	file = sys.argv[2]

	if mode == "decrypt":
		if not file.endswith(".ojs"):
			raise Exception("File must be a .ojs file !")

		with open(file, "rb") as f:
			data = f.read()
			f.close()

		print(f"===== DECRYPTING {file} =====")
		try:
			out = decryptSave(data)
		except Exception as e:
			print(f"\nFAILED TO DECRYPT : {e}")
			return
		print(f"\nDECRYPTION DONE")

		with open(f"{file.replace('.ojs', '.json')}", "w+", encoding="utf-8") as f:
			f.write(json.dumps(out, indent=4))
			f.close()
	elif mode == "encrypt":
		if not file.endswith(".json"):
			raise Exception("File must be a .json file !")

		with open(file, "r", encoding="utf-8") as f:
			data = json.loads(f.read())
			f.close()

		print(f"===== ENCRYPTING {file} =====")

		# the crypto material must stay the same as the original save, so read it
		# back from the .ojs sitting next to the .json (the one we are replacing)
		crypto = None
		src = f"{file[:-len('.json')]}.ojs"
		if os.path.exists(src):
			with open(src, "rb") as f:
				crypto = readCrypto(f.read())
			if crypto is None:
				print(f"! no valid crypto material in {src}, generating a new one")
		else:
			print(f"! {src} not found, generating new crypto material")

		try:
			out = encryptSave(data, crypto)
		except Exception as e:
			print(f"\nFAILED TO ENCRYPT : {e}")
			return
		print(f"\nENCRYPTION DONE")
		
		with open(f"{file.replace('.json', '.ojs')}", "wb") as f:
			f.write(out)
			f.close()
	else:
		print("invalid mode")
		sys.exit(1)

if __name__ == "__main__":
	main()
