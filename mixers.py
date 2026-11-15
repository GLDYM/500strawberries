"""Daily mixer prediction for 100% Orange Juice.

Mixers are computed from a timestamp only (the game uses the Steam server
time), so the same set is shown to everyone.

Algorithm (from 3.29.2.0: sub_140637D90 / sub_140F0B080 / sub_1403ED990):

  1. t = unix time
     if t >= 28801:                        # align on 00:00 UTC-08:00
         t -= (t - 28800) % 86400
  2. seed a modified MT19937 with t
  3. Fisher-Yates shuffle the list [0 .. 32] (33 mixers)
  4. count = COUNTS[uniform_int(1, 3)] with COUNTS = [1, 2, 2, 3]
  5. the mixers are the first count entries of the shuffled list

The MT19937 differs from a stock one only in the post-seed step that mixes
mt[396] and mt[623] into mt[0].
"""

import datetime
import sys

M32 = 0xFFFFFFFF

# index -> mixer name, in the game's enum order (33 entries in 3.29.x)
MIXER_NAMES = [
	"Air Raid",
	"Amplify",
	"Backtrack",
	"Bomber",
	"Charity",
	"Confusion",
	"Freeze",
	"Minelayer",
	"Miracle",
	"Random Warp",
	"Regeneration",
	"Sprint",
	"Treasure",
	"Healthy Boss",
	"Star-chaser",
	"Beggar",
	"Aggressive Heroes",
	"Defensive Heroes",
	"Evasive Heroes",
	"Blazing",
	"Flipped",
	"Menacing Boss",
	"Hard-shelled Boss",
	"Slippery Boss",
	"Joker",
	"Bankrupt",
	"Goo",
	"Spores",
	"Wildfriends",
	"Cardshark",
	"Speedy Boss",
	"Ubi Boss",
	"Ambush",
]

# how many mixers a day gets: COUNTS[uniform_int(1, len(COUNTS)-1)]
COUNTS = [1, 2, 2, 3]

# reward modifier of each mixer, mirrored from the game
MIXER_REWARD = {
	"Air Raid": "+10%", "Amplify": "+10%", "Backtrack": "+10%", "Bomber": "+10%",
	"Charity": "+0%", "Confusion": "+25%", "Freeze": "+10%", "Minelayer": "+25%",
	"Miracle": "+0%", "Random Warp": "+25%", "Regeneration": "+0%", "Sprint": "+10%",
	"Treasure": "+0%", "Healthy Boss": "+25%", "Star-chaser": "+0%", "Beggar": "+25%",
	"Aggressive Heroes": "+0%", "Defensive Heroes": "+0%", "Evasive Heroes": "+0%",
	"Blazing": "+10%", "Flipped": "+10%", "Menacing Boss": "+25%",
	"Hard-shelled Boss": "+25%", "Slippery Boss": "+25%", "Joker": "+0%",
	"Bankrupt": "+25%", "Goo": "+25%", "Spores": "+10%",
}

class MT19937:
	"""The game's MT19937: standard twist/temper, custom post-seed step."""

	def __init__(self, seed):
		mt = [0] * 624
		mt[0] = seed & M32
		for i in range(1, 624):
			mt[i] = (i + 1812433253 * ((mt[i - 1] ^ (mt[i - 1] >> 30)) & M32)) & M32

		# post-seed mixing (sub_140F0B080)
		x = mt[396] ^ mt[623]
		if x & 0x80000000:
			v = ((2 * x) ^ 0x321161BF) & M32
		else:
			v = (2 * x) & M32
		mt[0] = (mt[0] & 0x80000000) | (v & 0x7FFFFFFF)

		if not any(mt):
			mt[0] = 0x80000000

		self.mt = mt
		self.index = 624

	def _twist(self):
		mt = self.mt
		for i in range(624):
			y = (mt[i] & 0x80000000) | (mt[(i + 1) % 624] & 0x7FFFFFFF)
			value = mt[(i + 397) % 624] ^ (y >> 1)
			if y & 1:
				value ^= 0x9908B0DF
			mt[i] = value & M32
		self.index = 0

	def next_uint32(self):
		if self.index >= 624:
			self._twist()

		y = self.mt[self.index]
		self.index += 1
		y ^= y >> 11
		y = (y ^ ((y << 7) & 0x9D2C5680)) & M32
		y = (y ^ ((y << 15) & 0xEFC60000)) & M32
		y ^= y >> 18
		return y & M32

	def uniform_int(self, low, high):
		# MSVC std::uniform_int_distribution
		rng = (high - low) & M32
		if rng == 0:
			return low
		if rng == M32:
			return low + self.next_uint32()

		divisor = (M32 // (rng + 1)) + (1 if M32 % (rng + 1) == rng else 0)
		while True:
			v = self.next_uint32() // divisor
			if v <= rng:
				return low + v


def day_seed(timestamp):
	"""Round a unix timestamp down to 00:00 UTC-08:00 (08:00 UTC)."""
	timestamp = int(timestamp) & M32
	if timestamp >= 28801:
		timestamp -= (timestamp - 28800) % 86400
	return timestamp


def mixer_indices(when=None):
	"""Return the mixer indices for a datetime, a unix timestamp, or now."""
	if when is None:
		timestamp = datetime.datetime.now(datetime.timezone.utc).timestamp()
	elif isinstance(when, datetime.datetime):
		if when.tzinfo is None:
			when = when.replace(tzinfo=datetime.timezone.utc)
		timestamp = when.timestamp()
	else:
		timestamp = when

	rng = MT19937(day_seed(timestamp))

	result = list(range(len(MIXER_NAMES)))
	n = len(result)
	while True:
		i = rng.uniform_int(0, n - 1)
		result[n - 1], result[i] = result[i], result[n - 1]
		if n <= 2:
			break
		n -= 1

	count = COUNTS[rng.uniform_int(1, len(COUNTS) - 1)]
	return result[:count]


def mixers(when=None):
	"""Return the mixer names for a datetime, a unix timestamp, or now."""
	return [MIXER_NAMES[i] for i in mixer_indices(when)]


def main():
	if len(sys.argv) > 1:
		# the argument is the UTC-08:00 calendar date the mixers are for
		when = datetime.datetime.strptime(sys.argv[1], "%Y-%m-%d").replace(
			tzinfo=datetime.timezone(datetime.timedelta(hours=-8)))
	else:
		when = datetime.datetime.now(datetime.timezone.utc)
	if when.tzinfo is None:
		when = when.replace(tzinfo=datetime.timezone.utc)

	indices = mixer_indices(when)
	print("seed :", day_seed(when.timestamp()))
	print("index:", indices)
	for i in indices:
		name = MIXER_NAMES[i]
		print("  %2d  %-20s %s" % (i, name, MIXER_REWARD.get(name, "")))


if __name__ == "__main__":
	main()
