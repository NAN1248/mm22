#!/usr/bin/python2
import socket
import json
import os
import random
import sys
from socket import error as SocketError
import errno
sys.path.append("../..")
import src.game.game_constants as game_consts
from src.game.character import *
from src.game.gamemap import *

# Game map that you can use to query 
gameMap = GameMap()

# --------------------------- SET THIS IS UP -------------------------
teamName = "Test"
# ---------------------------------------------------------------------

# Set initial connection data
def initialResponse():
# ------------------------- CHANGE THESE VALUES -----------------------
    return {'TeamName': teamName,
            'Characters': [
                {"CharacterName": "Paladin1",
                 "ClassId": "Paladin"},
                {"CharacterName": "Paladin2",
                 "ClassId": "Paladin"},
                {"CharacterName": "Sorcerer",
                 "ClassId": "Sorcerer"},
            ]}
# ---------------------------------------------------------------------

# Determine actions to take on a given turn, given the server response
def processTurn(serverResponse):
# --------------------------- CHANGE THIS SECTION -------------------------
    # Setup helper variables
    actions = []
    myteam = []
    enemyteam = []
    # Find each team and serialize the objects
    for team in serverResponse["Teams"]:
        if team["Id"] == serverResponse["PlayerInfo"]["TeamId"]:
            for characterJson in team["Characters"]:
                character = Character()
                character.serialize(characterJson)
                myteam.append(character)
        else:
            for characterJson in team["Characters"]:
                character = Character()
                character.serialize(characterJson)
                enemyteam.append(character)
# ------------------ You shouldn't change above but you can ---------------

    # Choose a target
    target = None
    targets = []
    for character in enemyteam:
        if not character.is_dead():
            targets.append(character)
    
    target = targets[0]
    for x in targets:
        if x.attributes.get_attribute("Health") < target.attributes.get_attribute("Health"):
            target = x

    hashmap = {}
    for me in myteam:
        if not me.is_dead():
            hashmap[me.name] = me.id

    # If we found a target
    justDamageBuffed = False
    if target:
        for me in myteam:
            lowestHealth = myteam[0]
            for y in myteam:
                if y.attributes.get_attribute("Health") < lowestHealth.attributes.get_attribute("Health"):
                    lowestHealth = y
            #print me.id
            #print "hello"
            if(me.id == 6):
                #print me.id
                if (not justDamageBuffed) and me.in_ability_range_of(target, 16, gameMap) and me.can_use_ability(16):
                    actions.append({
                                "Action": "Cast",
                                "CharacterId": me.id,
                                # Am I buffing or debuffing? If buffing, target myself
                                "TargetId": target.id,
                                "AbilityId": 16
                            })
                    justDamageBuffed = False
                elif me.in_range_of(target, gameMap):
                    actions.append({
                            "Action": "Attack",
                            "CharacterId": me.id,
                            "TargetId": target.id,
                        })
                    justDamageBuffed = False
                elif me.can_use_ability(8) and me.attributes.get_attribute("Health") > 450:
                       actions.append({
                                "Action": "Cast",
                                "CharacterId": me.id,
                                # Am I buffing or debuffing? If buffing, target myself
                                "TargetId": target.id,
                                "AbilityId": 8
                            })
                       justDamageBuffed = True
            elif (me.id == 4 or me.id == 5):
                print hashmap
                if me.in_ability_range_of(myteam[2], 3, gameMap) and me.can_use_ability(3):
                    actions.append({
                                "Action": "Cast",
                                "CharacterId": me.id,
                                # Am I buffing or debuffing? If buffing, target myself
                                "TargetId": lowestHealth.id,
                                "AbilityId": 3
                            })
                elif me.in_ability_range_of(target,14,gameMap) and me.can_use_ability(14):
                    actions.append({
                                "Action": "Cast",
                                "CharacterId": me.id,
                                # Am I buffing or debuffing? If buffing, target myself
                                "TargetId": target.id,
                                "AbilityId": 14
                            })
                elif me.in_range_of(target, gameMap):
                    actions.append({
                            "Action": "Attack",
                            "CharacterId": me.id,
                            "TargetId": target.id,
                        })

    # Send actions to the server
    return {
        'TeamName': teamName,
        'Actions': actions
    }
# ---------------------------------------------------------------------

# Main method
# @competitors DO NOT MODIFY
if __name__ == "__main__":
    # Config
    conn = ('localhost', 1337)
    if len(sys.argv) > 2:
        conn = (sys.argv[1], int(sys.argv[2]))

    # Handshake
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(conn)

    # Initial connection
    s.sendall(json.dumps(initialResponse()) + '\n')

    # Initialize test client
    game_running = True
    members = None

    # Run game
    try:
        data = s.recv(1024)
        while len(data) > 0 and game_running:
            value = None
            if "\n" in data:
                data = data.split('\n')
                if len(data) > 1 and data[1] != "":
                    data = data[1]
                    data += s.recv(1024)
                else:
                    value = json.loads(data[0])

                    # Check game status
                    if 'winner' in value:
                        game_running = False

                    # Send next turn (if appropriate)
                    else:
                        msg = processTurn(value) if "PlayerInfo" in value else initialResponse()
                        s.sendall(json.dumps(msg) + '\n')
                        data = s.recv(1024)
            else:
                data += s.recv(1024)
    except SocketError as e:
        if e.errno != errno.ECONNRESET:
            raise  # Not error we are looking for
        pass  # Handle error here.
    s.close()
