import sys
import json

###############################
# Change this here for your custom values
# If you want to change more stuff, you will have to dig through the save file yourself
# as more research is needed
###############################
_ORANGES = 989898
_STARS = 767676
_PLAYCOUNT = 123456
_HOURSPLAYED = 99999
###############################

def main():
	if len(sys.argv) != 2:
		print("usage: changes.py <file>")
		sys.exit(1)

	file = sys.argv[1]

	with open(file, "rb") as f:
		data = json.loads(f.read())
		f.close()

	###
	data["info"]["orangeCurrency"] = _ORANGES
	data["info"]["star_num"] = _STARS
	data["info"]["play_num"] = _PLAYCOUNT
	data["info"]["play_time"]["hour"] = _HOURSPLAYED
	###

	with open(file, "w+") as f:
		f.write(json.dumps(data, indent=4))
		f.close()

	print("Done!")

if __name__ == "__main__":
	main()
