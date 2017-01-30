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
                {"CharacterName": "Warrior1",
                 "ClassId": "Warrior"},
                {"CharacterName": "Warrior2",
                 "ClassId": "Warrior"},
                {"CharacterName": "Warrior3",
                 "ClassId": "Warrior"},
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
    for character in enemyteam:
        if not character.is_dead():
            target = character
            break

  
    # If we found a target
    if target:

        #THIS IS THE PART THAT I AM WORKING ON, STUN WHEN WE WANT TO (NEED TO INCORPERATE ONLY STUN WHEN WE SEE A HEAL COMMING)
        #NEED A SEPERATE COMMAND THAT STUNS ON ARMOR DEBUFF
        for character in myteam:
            print inRangeOfAnyEnemy(character, enemyteam, 1) and canCastOnAny(myteam, enemyteam, 1)
            if inRangeOfAnyEnemy(character, enemyteam, 1) and canCastOnAny(myteam, enemyteam, 1):
                todo = (stunAll(myteam, enemyteam)) 
                for x in todo:
                    actions.append(x)
                thing = False
                return {
                    'TeamName': teamName,
                    'Actions': actions
                }  
            # If I am in range, either move towards target
            if character.in_range_of(target, gameMap):
                actions.append({
                    "Action": "Attack",
                    "CharacterId": character.id,
                    "TargetId": target.id,
                })
            else: # Not in range, move towards
                actions.append({
                    "Action": "Move",
                    "CharacterId": character.id,
                    "TargetId": target.id,
                })

    # Send actions to the server
    return {
        'TeamName': teamName,
        'Actions': actions
    }

#assumes enemies in array are about to cast
def stunAll(myteam, enemArray):
    things_to_do = []
    for character in myteam:
            for enemy in enemArray:
                if not enemy.is_dead():
                    if character.can_use_ability(1) and character.in_ability_range_of(enemy, gameMap, 1) and not enemy.attributes.get_attribute('Stunned'):
                        things_to_do.append({
                            "Action": "Cast",
                            "CharacterId": character.id,
                            "TargetId": enemy.id,
                            "AbilityId": 1
                        })
                        print "stun 1" + str(enemy.id)
                        enemArray.remove(enemy)
                    if character.can_use_ability(14) and character.in_ability_range_of(enemy, gameMap, 10):
                        things_to_do.append({
                            "Action": "Cast",
                            "CharacterId": character.id,
                            "TargetId": enemy.id,
                            "AbilityId": 14
                        })
                        print "stun 10"
    return things_to_do

def inRangeOfAnyEnemy(myChar, enemyteam, abilityId):
    for enemy in enemyteam:
        if myChar.in_ability_range_of(enemy, gameMap, abilityId):
            return True
    return False

def canCastOnAny(myteam, enemyteam, abilityId):
    for character in myteam:
        for enemy in enemyteam:
            if character.in_ability_range_of(enemy, gameMap, abilityId) and character.can_use_ability(abilityId):
                return True
    return False

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
