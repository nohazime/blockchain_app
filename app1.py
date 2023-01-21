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
from classes import BlockChain as BlockChain
from classes import Block as Block
import os
import pickle


# define a helper function for PyInstaller to get absolute path to resource
def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# define path to find blockChain text file which stores the current chain for this node.
text_path = resource_path('blockChain.txt')

# we will be using Flask to help us run this web app
node = Flask(__name__)

# define a unique node id for this node.
node_id = str(uuid4()).replace('-', '')

# instantiate a new BlockChain class
blockchain = BlockChain()

# check if the text file storing previous BlockChain is not empty
# if there is an existing chain saved in text file, we will copy that as our current chain
if os.stat(text_path).st_size > 0:
    file_object = open(text_path, 'rb')
    blockchain.chain = pickle.load(file_object)


# create a new transaction to be stored in the blockchain
@node.route('/transaction', methods=['POST'])
def transaction():
    if request.method == 'POST':
        data = request.get_json(force="true")
        required = ["sender", "recipient", "amount"]

        if data['sender'] and data['recipient'] and data['amount']:

            index = blockchain.new_transaction(data["sender"], data["recipient"], data["amount"])

            response = {'message: Transaction will be added to Block {}'.format(index)}

            return jsonify(response), 201
        else:
            return 'Wrong Transaction Format', 400


# mine a block
# each mined block will reward this node with one coin
@node.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block()
    proof = blockchain.proof_of_work(last_block["proof"], last_block["hash"])

    blockchain.new_transaction(sender="0", recipient=node_id, amount=1, )

    previous_hash = last_block["hash"]
    block = blockchain.new_block(proof, previous_hash)

    file_object = open(text_path, 'wb')
    pickle.dump(blockchain.chain, file_object)

    response = {
        'message': "New Block Added To Chain",
        'index': block.index,
        'transaction': block.transaction,
        'proof': block.proof,
        'previous_hash': block.previous_hash,
    }
    return jsonify(response), 200


# returns the current blockchain of this node
@node.route('/chain', methods=['GET'])
def chain():
    response = {'length': len(blockchain.chain),
                'chain': blockchain.chain}

    file_object = open(text_path, 'wb')
    pickle.dump(blockchain.chain, file_object)

    return jsonify(response), 200


# registers new nodes that will be tracked for consensus
@node.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json(force="true")

    nodes = values.get('nodes')

    if nodes:
        answer = values['nodes']
        blockchain.register_node(answer)
        print("true")

        response = {
            'message': 'New nodes have been added',
            'total_nodes': list(blockchain.nodes),
        }
        return jsonify(response), 201

    else:
        return "Error: Please supply a valid list of nodes", 400


# checks the chains of other nodes, validates if they are correct, then copies the longest chain
@node.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.get_consensus()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


# syncs this node with another node
# sync means we will copy the current chain of the other node
@node.route('/nodes/sync', methods=['POST'])
def get_current_chain():
    value = request.get_json(force="true")

    nodes = value.get("nodes")

    if nodes:
        answer = value['nodes']
        parsed_url = urlparse(answer).netloc

        response = requests.get('http://{}/chain'.format(parsed_url))

        if response.status_code == 200:
            length = response.json()['length']
            blockchain.chain = response.json()['chain']

            new_chain = {
                "message": "Sync successful.",
                "chain": blockchain.chain,
                "length": len(blockchain.chain)
            }

            return jsonify(new_chain), 201


# runs this node on local host port 5000
if __name__ == '__main__':
    node.run(host='localhost', port=5000)
    #node.run(debug = True)
     