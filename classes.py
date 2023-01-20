from flask import Flask
from flask import request
from flask import jsonify
from urllib.parse import urlparse
from uuid import uuid4
from collections import OrderedDict
import hashlib
import datetime as date
from time import time
from random import *
import json
import requests


# Defines the Block class
# a singular Block that makes up a chain
class Block:

    # constructor for a Block
    # parameters::
    # index: index of this block in the BlockChain
    # timestamp: when was this block created
    # transaction: the info for the transaction that the block contains
    # previous_hash: the hash code of the previous block in the chain
    # proof: proof of work
    def __init__(self, index, timestamp, transaction, previous_hash, proof):
        self.index = index
        self.timestamp = timestamp
        self.transaction = transaction
        self.previous_hash = previous_hash
        self.proof = proof
        self.hash = self.hash_block()

    # hash_block method hashes the string containing
    # timestamp, transaction info, previous_hash, and proof of this block
    # and creates a hexadecimal hash code
    def hash_block(self):
        hasher = hashlib.sha256()

        string = (str(self.timestamp) + str(self.transaction) + str(self.previous_hash) + str(self.proof))

        block_string = json.dumps(string, sort_keys=True).encode('utf-8')

        return hashlib.sha256(block_string).hexdigest()

    # Takes the characteristics of this Block and places it into a Dictionary object
    # that will be stored in the chain
    def toDict(self):
        response = {
            "index": self.index,
            "timestamp": str(self.timestamp),
            "proof": self.proof,
            "transaction": self.transaction,
            "hash": self.hash,
            "previous_hash": self.previous_hash,
        }

        return response


# Defines the BlockChain class
# a class made up of Block dictionary objects
class BlockChain(object):

    # Constructor
    # instantiates a new BlockChain
    def __init__(self):

        # creates a genesis block, the first block in a chain
        genesis_block = BlockChain.create_genesis_block()

        # chain is an array of dictionary lists containing each Block information
        self.chain = [genesis_block.toDict()]

        # current transactions that should be stored in each created Block
        self.current_transactions = []

        # Create a collection that will create unique elements containing
        # the nodes that are part of this chain.
        # Nodes are are unique IP addresses
        # who want to take part in creating and mining Blocks
        self.nodes = set()

    # register a new node to participate
    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

        # validate the chain of a node by checking proof of work and hashes

    def valid_chain(self, chain):

        # check that the blockchains have the same starting point (genesis block)
        # meaning that we are part of the same blockchain
        if chain[0]["hash"] == self.chain[0]["hash"]:

            last_block = chain[0]
            current_index = 1

            while current_index < len(chain):
                block = chain[current_index]
                print(last_block)
                print(block)

                # Check that the hash of the block is correct
                if block["previous_hash"] != last_block["hash"]:
                    return False

                # Check that the Proof of Work is correct
                if not self.validate_proof(last_block["proof"], last_block["hash"], block["proof"]):
                    return False

                last_block = block
                current_index += 1

            return True

        else:
            return false

    # Get consensus method
    # Evaluate all the chains of nodes registered and see which node has the longest valid chain and copy that as
    # our new chain
    def get_consensus(self):
        other_nodes = self.nodes
        new_chain = None
        max_length = len(self.chain)

        for node in other_nodes:
            response = requests.get('http://{}/chain'.format(node))

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

        return False

        # Add a new block to this BlockChain

    def new_block(self, proof, previous_hash):

        this_index = len(self.chain)
        this_timestamp = date.datetime.now()
        this_transaction = self.current_transactions
        last_block = self.last_block()
        valid_proof = self.proof_of_work(last_block["proof"], last_block["hash"])

        if (proof == valid_proof):
            new_block = Block(this_index, this_timestamp, this_transaction, previous_hash, proof)

            self.chain.append(new_block.toDict())

            self.current_transactions = []

            return new_block

        else:
            return "invalid proof"

    # creates a genesis block for this BlockChain
    # Previous hash is set to 0 since it's the first Block
    # Proof of work is set to a random int from 1 to 100
    @staticmethod
    def create_genesis_block():
        index = 0
        timestamp = date.datetime.now()
        transaction = "Genesis Block"
        previous_hash = "0"
        proof = randint(1, 100)
        return Block(index, timestamp, transaction, previous_hash, proof)

    # Creates a new transaction that requires the following params:
    # sender, recipient, amount
    # This transaction will be added to the current_transactions array and will be added to the next mined Block
    def new_transaction(self, sender, recipient, amount):

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

    # gets the last block in the current BlockChain
    def last_block(self):
        return self.chain[-1]

    # Returns the Proof of Work given the parameters
    # parameters:
    ##last_proof: the Proof of Work of the previous block in the chain
    ##previous_hash: the hashcode of the previous block in the chain
    def proof_of_work(self, last_proof, previous_hash):

        proof = 0

        # while validate_proof is false, increment proof by 1 until we find the correct proof
        while self.validate_proof(last_proof, previous_hash, proof) is False:
            proof = proof + 1

        return proof

    ##Calculates the Proof of Work using the following algorithm: find a number x where if the previous proof, previous hash, and x are hashed together, the hash will begin with 3 leading zeros '000'
    def validate_proof(self, last_proof, previous_hash, proof):
        proof_guess = (str(last_proof) + str(previous_hash) + str(proof)).encode('UTF-8')
        guess_hash = hashlib.sha256(proof_guess).hexdigest()

        return guess_hash[:3] == "000"