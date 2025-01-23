import requests
import json
import sys
import os

def char_maker(avatarInfoItem, char_bridge):
    def find_char(avatarId,char_bridge):
        for item,values in char_bridge.items():
            if type(values) is str:
                if values == str(avatarId):
                    return item
            if type(values) is list:
                if str(avatarId) in values:
                    return item
    
    result = {}
    result['key'] = find_char(avatarInfoItem['avatarId'],char_bridge=char_bridge)
    result['level']= int(avatarInfoItem['propMap']['4001']['val'])
    result['ascension'] = int(avatarInfoItem['propMap']['1002']['val'])
    talents = list(avatarInfoItem['skillLevelMap'].values())
    result['talent'] = {}
    result['talent']['auto'] = talents[0]
    result['talent']['skill'] = talents[1]
    result['talent']['burst'] = talents[2]
    result['constellation'] = len(avatarInfoItem.get('talentIdList',[]))
    result['id'] = result['key']
    return result

def weapon_maker(avatarInfoItem, weapon_bridge, char_bridge):
    def find_char(avatarId,char_bridge):
        for item,values in char_bridge.items():
            if type(values) is str:
                if values == str(avatarId):
                    return item
            if type(values) is list:
                if str(avatarId) in values:
                    return item
    
    equip_list = avatarInfoItem['equipList']
    ind = None
    for i,element in enumerate(equip_list):
        if 'weapon' in element.keys():
            ind = i
            break
    result = {}
    weapon_info = equip_list[ind]
    result["key"] = weapon_bridge[weapon_info['flat']['nameTextMapHash']]
    result["level"] = weapon_info['weapon']['level']
    result["ascension"] = weapon_info['weapon'].get('promoteLevel',False) if weapon_info['weapon'].get('promoteLevel',False) else 0
    result["refinement"] = list(weapon_info['weapon']['affixMap'].values())[0] + 1
    result["location"] = find_char(avatarInfoItem['avatarId'],char_bridge=char_bridge)
    result["lock"] = 'false'
    return result

def artifacts_maker(avatarInfoItem, artifacts_bridge, equip_bridge, stats_bridge, char_bridge):
    def find_char(avatarId,char_bridge):
        for item,values in char_bridge.items():
            if type(values) is str:
                if values == str(avatarId):
                    return item
            if type(values) is list:
                if str(avatarId) in values:
                    return item
    
    def mini_version(artifactInfo, artifacts_bridge, equip_bridge, stats_bridge, location):
        result = {}
        result["setKey"] = artifacts_bridge[artifactInfo['flat']['setNameTextMapHash']]
        result["rarity"] = artifactInfo['flat']['rankLevel']
        result["level"] = artifactInfo['reliquary']['level']-1
        result["slotKey"] = equip_bridge[artifactInfo['flat']['equipType']]
        result["mainStatKey"] = stats_bridge[artifactInfo['flat']['reliquaryMainstat']['mainPropId']]
        result["substats"] = [
            {'key': stats_bridge[substat['appendPropId']], 'value': substat['statValue']} 
            for substat in artifactInfo['flat']['reliquarySubstats']
            ]
        result['location'] = location
        result['lock'] = 'false'
        return result

    equip_list = avatarInfoItem['equipList']
    result = []
    for item in equip_list:
        if 'reliquary' in item.keys():
            location = find_char(avatarInfoItem['avatarId'],char_bridge=char_bridge)
            arti = mini_version(item, artifacts_bridge, equip_bridge, stats_bridge, location)
            result.append(arti)
    return result
    
    

def generate(uid):
    with open('./sources/char.json','r') as f:
        char_bridge = json.load(f)
    with open('./sources/weapons.json','r') as f:
        weapon_bridge = json.load(f)
    with open('./sources/artifacts.json','r') as f:
        artifacts_bridge = json.load(f)
    with open('./sources/stats.json','r') as f:
        stats_bridge = json.load(f)
    with open('./sources/artifact_equips.json','r') as f:
        equip_bridge = json.load(f)

    try:
        resp = requests.get(f'https://enka.network/api/uid/{uid}/')
        data = resp.json()
    except Exception as e:
        return f"error: {e}"
    if not (200 <= resp.status_code < 300):
        return f'error status code : response ended with {resp.status_code}'
    #try:
    result = {}
    result["format"] =  "GOOD"
    result["dbVersion"] = 25
    result["source"] = "Genshin Optimizer"
    result["version"] = 1
    characters = []
    weapons = []
    artifacts = []
    for avatar in data['avatarInfoList']:
        chars = char_maker(avatar, char_bridge)
        weap = weapon_maker(avatar, weapon_bridge, char_bridge)
        arti = artifacts_maker(avatar, artifacts_bridge, equip_bridge, stats_bridge, char_bridge)
        characters.append(chars)
        weapons.append(weap)
        artifacts.extend(arti)
    result['characters'] = characters
    result['weapons'] = weapons
    result['artifacts'] = artifacts
    output_file = f'./outputs/{uid}.json'
    with open(output_file,'w') as f:
        json.dump(result,f)
    return f'the output file is in location {os.path.abspath(output_file)}'
    #except Exception as e:
    #    return f'error with the code\n{e}' 

if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            for arg in sys.argv[1:]:
                if arg.strip() != "": 
                    number = str(arg)
                    res = generate(number)
                    print(res)
            if all(arg.strip() == "" for arg in sys.argv[1:]): #check if all arguments are empty
                print('No valid integer provided.')
        except ValueError:
            print('Invalid input: Please provide an integer.')
    else:
        print('Usage: python filename.py integer_number')
