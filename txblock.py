
import pickle
import time
import random

import signature
from transaction import Tx
from block import CBlock

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

reward = 25.0
leading_zeros = 2
next_char_limit = 50

class TxBlock(CBlock):

	nonce = "AAAAAAA"

	def __init__(self, previous_block):
		super(TxBlock, self).__init__([], previous_block)

	def addTx(self, Tx_in):
		self.data.append(Tx_in)

	def count_totals(self):
		total_in = 0
		total_out = 0
		for tx in self.data:
			for address, amount in tx.inputs:
				total_in += amount
			for address, amount in tx.outputs:
				total_out += amount
		return total_in, total_out

	def is_valid(self):
		if not super(TxBlock, self).is_valid():
			return False
		for tx in self.data:
			if not tx.is_valid():
				return False
		total_in, total_out = self.count_totals()
		if total_out - total_in - reward > 0.00000000001:
			return False
		return True

	def good_nonce(self):
		digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
		digest.update(bytes(str(self.data), 'utf8'))
		digest.update(bytes(str(self.previous_hash), 'utf8'))
		digest.update(bytes(str(self.nonce), 'utf8'))
		hash_g = digest.finalize()
		if hash_g[:leading_zeros] != bytes("".join(['\x00' for i in range(leading_zeros)]), 'utf8'):
			return False
		return int(hash_g[leading_zeros]) < next_char_limit

	def find_nonce(self):
		for i in range(10000000):
			self.nonce = ''.join([
			chr(random.randint(0,255)) for i in range(10 * leading_zeros)])
			if self.good_nonce():
				return self.nonce
		return None

if __name__ == "__main__":
	pr1, pu1 = signature.generate_keys()
	pr2, pu2 = signature.generate_keys()
	pr3, pu3 = signature.generate_keys()

	Tx1 = Tx()
	Tx1.add_input(pu1, 1)
	Tx1.add_output(pu2, 1)
	Tx1.sign(pr1)

	if Tx1.is_valid():
		print("Success! Tx is valid")
	else:
		print("Error! Tx is invalid")

	savefile = open("save.dat", "wb")

	pickle.dump(Tx1, savefile)
	savefile.close()

	loadfile = open("save.dat", "rb")
	newTx = pickle.load(loadfile)

	if newTx.is_valid():
		print("Success! loaded Tx is valid")
	else:
		print("Error! load Tx is invalid")

	loadfile.close()

	root = TxBlock(None)
	root.addTx(Tx1)

	Tx2 = Tx()
	Tx2.add_input(pu2, 1.1)
	Tx2.add_output(pu3, 1)
	Tx2.sign(pr2)
	root.addTx(Tx2)

	B1 = TxBlock(root)
	Tx3 = Tx()
	Tx3.add_input(pu3, 1.1)
	Tx3.add_output(pu1, 1)
	Tx3.sign(pr3)
	B1.addTx(Tx3)

	Tx4 = Tx()
	Tx4.add_input(pu1, 1)
	Tx4.add_output(pu2, 1)
	Tx4.add_reqd(pu3)
	Tx4.sign(pr1)
	Tx4.sign(pr3)
	B1.addTx(Tx4)

	start = time.time()
	print(str(B1.find_nonce()))
	elapse = time.time() - start
	print("elapsed time: ", str(elapse), " s")
	if elapse < 10:
		print("ERROR! Mining is to fast!")

	if B1.good_nonce():
		print("Success! Nonce is good!")
	else:
		print("ERROR! Bad nonce")

	savefile = open("block.dat", "wb")
	pickle.dump(B1, savefile)
	savefile.close()

	loadfile = open("block.dat", "rb")
	load_B1 = pickle.load(loadfile)
	load_B1.is_valid()
	for b in [root, B1, load_B1, load_B1.previous_block]:
		if b.is_valid():
			print("Success! Valid Block")
		else:
			print("Error! Invalid Block")

	if load_B1.good_nonce():
		print("Success! Nonce is good after save and load!")
	else:
		print("ERROR! Bad nonce after load")

	B2 = TxBlock(B1)
	Tx5 = Tx()
	Tx5.add_input(pu3, 1)
	Tx5.add_output(pu1, 100)
	Tx5.sign(pr3)
	B2.addTx(Tx5)

	load_B1.previous_block.addTx(Tx4)
	for b in [B2, load_B1]:
		if b.is_valid():
			print("Error! Bad block verified")
		else:
			print("Success! Bad block detected")

	# Test mining reward and tx fees
	pr4, pu4 = signature.generate_keys()
	B3 = TxBlock(B2)
	B3.addTx(Tx2)
	B3.addTx(Tx3)
	B3.addTx(Tx4)
	Tx6 = Tx()
	Tx6.add_output(pu4, 25)
	B3.addTx(Tx6)
	if B3.is_valid():
		print("Success! Block reward succeeds")
	else:
		print("Error! Block reward fail")

	B4 = TxBlock(B3)
	B4.addTx(Tx2)
	B4.addTx(Tx3)
	B4.addTx(Tx4)

	Tx7 = Tx()
	Tx7.add_output(pu4, 25.2)
	B4.addTx(Tx7)
	if B4.is_valid():
		print("Success! Tx fees succeed")
	else:
		print("Error! Tx fees fail")

	# Greedy miner
	B5 = TxBlock(B4)
	B5.addTx(Tx2)
	B5.addTx(Tx3)
	B5.addTx(Tx4)

	Tx8 = Tx()
	Tx8.add_output(pu4, 26.2)
	B5.addTx(Tx8)
	if not B5.is_valid():
		print("Success! Greedy miner detected")
	else:
		print("Error! Greedy miner not detected")

