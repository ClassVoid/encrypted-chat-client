import datetime
import json
from typing import *

import requests
import base64
import hashlib
import string
import random
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA


# Loading the configuration

with open("client_conf.json") as config:
    client_config=json.load(open("client_conf.json"))
    server_url=f"{client_config['server_address']}:{client_config['server_port']}/{client_config['server_endpoint']}"
'''
server_port = "8080"
server_url = f"http://127.0.0.1:{server_port}/api"
'''




def generateCredentials(username: str, password: str):
    '''
    This function has the role of generating a pair of RSA keys when creating a new account
    :param username: the username picked by the user
    :param password: user's password
    :return: a hashmap (username, public_key, encrypted_private_key)
    '''

    # no AES encryption on private key at the moment
    key = RSA.generate(4096)
    # key format 'PEM' 'DER'
    privateKey = str(key.exportKey(format='PEM'), 'utf-8')  # ASCII armored
    publicKey = key.publickey().exportKey(format='DER')  # bytes

    encrPrivKey = encryptAES(privateKey, password)
    # decrPrivKey=decryptAES(encrPrivKey, password)

    print(f"encrypted private key created:\n{encrPrivKey}")
    print(f"encrypted private key size: {len(encrPrivKey)}")
    # print(f"decrypted private key:\n {decrPrivKey}")

    result = {"username": username,
              "pubKey": f"{base64.b64encode(publicKey).decode('utf-8')}",
              "encryptedPriKey": f"{encrPrivKey}"}

    return result


def createAccount(username: str, password: str) -> requests.Response.__class__:
    data = generateCredentials(username, password)

    headers = {"Content-Type": "application/json"}

    res = requests.post(f"{server_url}/users", json=data, headers=headers)

    # print(res.status_code)
    return res


def getUserData(username: str) -> requests.Response.__class__:
    '''
    :param username:
    :return: a hashmap (username, pubKey, encryptedPriKey) that correspond to the user's credentials
    '''
    res = requests.get(f"{server_url}/users/{username}")

    # print(f"credentials for {username}\n{res.text}")

    return res


def sendMessage(username: str, chatName: str, chatKey: str, message: str) -> requests.Response.__class__:
    '''
    :param username:
    :param chatName:
    :param message: should already be encrypted
    :return:
    '''
    encrMsg = encryptAES(message, chatKey)

    data = {"authorName": username,
            "chatName": chatName,
            "encryptedMsg": encrMsg}

    headers = {"Content-Type": "application/json"}
    res = requests.post(f"{server_url}/messages", json=data, headers=headers)
    print(res.status_code)

    return res


def getMessages(chatName: str, dateTime: str) -> requests.Response.__class__:
    res = requests.get(f"{server_url}/messages?chat_name={chatName}&date_time={dateTime}")
    #print(res.json())

    return res


def getChatOwner(chatName: str) -> requests.Response.__class__:
    res = requests.get(f"{server_url}/chats/{chatName}/owner")
    # print(res.text)

    return res


def getChatKey(username: str, chatName: str) -> requests.Response.__class__:
    res = requests.get(f"{server_url}/chat-keys/{chatName}/{username}")
    return res


def getTicket(username: str) -> requests.Response.__class__:
    res = requests.get(f"{server_url}/ticket/{username}")

    return res


def decryptRSA(message: str, privateKey: str) -> str:
    msgEncode = base64.b64decode(message)

    rsaPrivKey = RSA.importKey(privateKey)
    oaepCipher = PKCS1_OAEP.new(rsaPrivKey)
    decryptedMsg = oaepCipher.decrypt(msgEncode)

    return str(decryptedMsg, 'utf-8')


def encryptRSA(message: str, publicKey: str) -> str:
    msgEncode = str.encode(message)

    rsaPubKey = RSA.importKey(base64.b64decode(publicKey))
    oaepCipher = PKCS1_OAEP.new(rsaPubKey)
    encryptedMsg = oaepCipher.encrypt(msgEncode)

    return base64.b64encode(encryptedMsg).decode('utf-8')


def encryptAES(message: str, password: str) -> str:
    keySHA256 = hashlib.sha256(password.encode()).digest()
    BS = AES.block_size
    pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)

    raw = base64.b64encode(pad(message).encode('utf8'))
    iv = get_random_bytes(AES.block_size)  # initialization vector

    cipher = AES.new(keySHA256, AES.MODE_CFB, iv)
    msgEncrypted = cipher.encrypt(raw)
    # here
    resultEncryption = base64.b64encode(iv + msgEncrypted).decode('utf8')

    return resultEncryption


def decryptAES(message: str, password: str) -> str:
    keySHA256 = hashlib.sha256(password.encode()).digest()
    unpad = lambda s: s[:-ord(s[-1:])]

    enc = base64.b64decode(message)
    iv = enc[:AES.block_size]

    cipher = AES.new(keySHA256, AES.MODE_CFB, iv)
    msgDecrypted = cipher.decrypt(enc[AES.block_size:])
    resultDecryption = unpad(base64.b64decode(msgDecrypted).decode('utf8'))

    return resultDecryption


def generateRandomString(size) -> str:
    result = ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=size))

    return result


def getIdentityTicket(credentials: Dict[str, str]) -> Dict[str, str]:
    # request a ticket
    ticket_res = getTicket(credentials['username'])

    # decrypt the message
    decryptedMsg = decryptRSA(ticket_res.json()['encryptedSecret'], credentials['PriKey'])

    # encrypt the message
    encryptedMsg = encryptRSA(decryptedMsg, ticket_res.json()['serverPublicKey'])

    # create user ticket
    identityTicket = {"username": f"{credentials['username']}",
                      "encryptedMsg": f"{encryptedMsg}"}

    return identityTicket


def getUserChats(credentials: Dict[str, str]) -> requests.Response.__class__:
    res = requests.get(f"{server_url}/chats/{credentials['username']}")
    return res


def createChat(credentials: Dict[str, str], chatName: str) -> requests.Response.__class__:
    '''
    This creates a chat without users
    when you create a chat you also don't have its AES key
    :param credentials:
    :param chatName:
    :return:
    '''

    data = getIdentityTicket(credentials)
    headers = {"Content-Type": "application/json"}

    print("sending create chat request")
    res = requests.post(f"{server_url}/chats/{chatName}/{credentials['username']}",
                        json=data, headers=headers)
    print(res.status_code)
    print(res.text)

    return res


def addUser(credentials: Dict[str, str], username: str, chatName: str) -> requests.Response.__class__:
    '''
    -if the user is the chat owner then it creates the AES key
    -uploads the AES encrypted key for that user
    -adds a user to the chat

    :param credentials:
    :param username:
    :param chatName:
    :return:
    '''
    data = getIdentityTicket(credentials)

    chatOwner = getChatOwner(chatName).text
    chatPasswordEncr = ''
    # if I add myself to the chat, I must create a chat key
    if chatOwner == username:
        chatPassword = generateRandomString(30)
        chatPasswordEncr = encryptRSA(chatPassword, credentials["pubKey"])
    else:
        chatKeyEncr = getChatKey(credentials['username'], chatName)
        chatKey = decryptRSA(chatKeyEncr.text, credentials['PriKey'])
        user_credentials = getUserData(username)
        print(f"user credentials {user_credentials.status_code}")
        if user_credentials.status_code == 404:
            raise Exception()
        chatPasswordEncr = encryptRSA(chatKey, user_credentials.json()['pubKey'])

    userData = {"username": username,
                "encryptedKey": chatPasswordEncr}

    addUserData = {"addUserDataList": [userData],
                   "userEncrMessage": data}

    headers = {"Content-Type": "application/json"}
    res = requests.post(f"{server_url}/chats/{chatName}/users", json=addUserData, headers=headers)

    print(res.status_code)
    print(res.text)

    return res


def deleteChat(credentials: Dict[str, str], chatName: str) -> requests.Response.__class__:
    data = getIdentityTicket(credentials)
    headers = {"Content-Type": "application/json"}

    res = requests.delete(f"{server_url}/chats/{chatName}", json=data, headers=headers)
    print(res.status_code)
    print(res.text)
    return res


def updateUserList(credentials: Dict[str, str], chatName: str) -> requests.Response.__class__:
    data = getIdentityTicket(credentials)
    headers = {"Content-Type": "application/json"}

    res = requests.get(f"{server_url}/chats/{chatName}/users", json=data, headers=headers)

    print(res.status_code)
    print(res.text)
    return res


def deleteAccount(credentials: Dict[str, str]) -> requests.Response.__class__:
    data = getIdentityTicket(credentials)
    headers = {"Content-Type": "application/json"}

    res = requests.delete(f"{server_url}/users/{credentials['username']}", json=data, headers=headers)

    print(res.status_code)
    print(res.text)