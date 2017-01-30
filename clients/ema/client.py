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
teamName = "3 Archers"
# ---------------------------------------------------------------------

# Set initial connection data
def initialResponse():
# ------------------------- CHANGE THESE VALUES -----------------------
    return {'TeamName': teamName,
            'Characters': [
                {"CharacterName": "Archer1",
                 "ClassId": "Archer"},
                {"CharacterName": "Archer2",
                 "ClassId": "Archer"},
                {"CharacterName": "Archer3",
                 "ClassId": "Archer"},
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
    if len(enemyteam) == 0:
            return
    target = first_nondead_enemy(enemyteam)
    for enemy in enemyteam:
        if not enemy.is_dead():
            if enemy.attributes.get_attribute("Health") < target.attributes.get_attribute("Health"):
                target = enemy

    just_armor_buffed = False

    for character in myteam:
        if not character.is_dead():
            cast = False

            if character.attributes.get_attribute('Stunned') == True:
                #print("stunned")
                actions.append({
                    "Action": "Cast",
                    "CharacterId": character.id,
                    # Am I buffing or debuffing? If buffing, target myself
                    "TargetId": character.id,
                    "AbilityId": 0
                })
                #print("burst")
                cast = True

            # If we found a target
            if target:

                # If I am in range, either move towards target
                if character.in_range_of(target, gameMap):
                    # Am I already trying to cast something?
                    if character.casting is None:
                        if not just_armor_buffed:
                            if character.can_use_ability(2):
                                actions.append({
                                    "Action": "Cast",
                                    "CharacterId": character.id,
                                    # Am I buffing or debuffing? If buffing, target myself
                                    "TargetId": target.id,
                                    "AbilityId": 2
                                })
                                cast = True
                                just_armor_buffed = True
                    # Was I able to cast something? Either wise attack
                        if not cast:
                            #print "attack"
                            actions.append({
                                "Action": "Attack",
                                "CharacterId": character.id,
                                "TargetId": target.id,
                            })
                            just_armor_buffed = False
                else: # Not in range, move towards
                    #print "moved"
                    actions.append({
                        "Action": "Move",
                        "CharacterId": character.id,
                        "TargetId": target.id,
                    })
                    just_armor_buffed = False


    # Send actions to the server
    return {
        'TeamName': teamName,
        'Actions': actions
    }
# ---------------------------------------------------------------------

def first_nondead_enemy(arr):
    for x in arr:
        if not x.is_dead():
            return x

def validMovesFromHere(pos):
    double_adjacent_pos = []
    for i in [-2,2]:
        double_adjacent_pos.append([pos[0] + i, pos[1]])
        double_adjacent_pos.append([pos[0], i + pos[1]])
    valid_pos = []
    for x in double_adjacent_pos:
        if gameMap.is_inbounds(x):
            valid_pos.append(x)
    #print valid_pos
    return valid_pos









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
