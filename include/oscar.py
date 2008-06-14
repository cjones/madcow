#!/usr/bin/env python

"""
This was brutally ripped out of twisted and given a simpler TCP model
twisted is just too big and i want as much as possible included inside
of madcow.
"""

import re
import sys
from Queue import Queue
from threading import Thread
import socket
from time import sleep
from select import select
import os
import struct
import md5
import string
import random
import types

TLV_USERNAME = 0x0001
TLV_CLIENTNAME = 0x0003
TLV_COUNTRY = 0x000E
TLV_LANG = 0x000F
TLV_CLIENTMAJOR = 0x0017
TLV_CLIENTMINOR = 0x0018
TLV_CLIENTSUB = 0x001A
TLV_PASSWORD = 0x0025
TLV_USESSI = 0x004A
CAP_ICON = '\011F\023FL\177\021\321\202"DEST\000\000'
CAP_VOICE = '\011F\023AL\177\021\321\202"DEST\000\000'
CAP_IMAGE = '\011F\023EL\177\021\321\202"DEST\000\000'
CAP_CHAT = 't\217$ b\207\021\321\202"DEST\000\000'
CAP_GET_FILE = '\011F\023HL\177\021\321\202"DEST\000\000'
CAP_SEND_FILE = '\011F\023CL\177\021\321\202"DEST\000\000'
CAP_GAMES = '\011F\023GL\177\021\321\202"DEST\000\000'
CAP_SEND_LIST = '\011F\023KL\177\021\321\202"DEST\000\000'
_tags = re.compile(r'<.*?>', re.DOTALL)

class AIMClient:

    host = 'login.oscar.aol.com'
    port = 5190

    def __init__(self, user, passwd, profile):
        self.profile = profile
        self.oscar = OscarAuthenticator(user, passwd)
        self.oscar.aimclient = self
        self.socket = None
        self.fd = None
        self.running = False
        self.dispatcher_queue = Queue()

    def start(self):
        self.running = True
        t = Thread(target=self.dispatch, name='Dispatcher')
        t.setDaemon(True)
        t.start()
        self.run()

    def stop(self):
        self.running = False

    def dispatch(self):
        while self.running:
            data = self.dispatcher_queue.get()
            self.oscar.dataReceived(data)
            self.dispatcher_queue.task_done()

    def run(self):
        self.connect()
        self.oscar.connectionMade()
        self.oscar.transport = self.socket
        self.start_poll()
        while True:
            sleep(1)

    def start_poll(self):
        t = Thread(target=self.poll, name='PollThread')
        t.setDaemon(True)
        t.start()

    def poll(self):
        while self.running:
            try:
                if self.fd in select([self.fd], [], [], 5)[0]:
                    ch = os.read(self.fd, 512)
                    if not len(ch):
                        continue
                    self.dispatcher_queue.put(ch)
            except Exception, e:
                self.running = False

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.socket.setblocking(False)
        self.fd = self.socket.fileno()

    def output(self, response, req=None):
        self.handle_response(response, req)

    def protocol_output(self, message, req=None):
        message = self.newline.sub('<br>', message)
        req.aim.sendMessage(req.nick, message)

    def process_request(self, message, nick, aim):
        aim.sendMessage(nick, 'ECHO: %s' % message)


class OSCARUser:

    def __init__(self, name, warn, tlvs):
        self.name = name
        self.warning = warn
        self.flags = []
        self.caps = []
        for k,v in tlvs.items():
            if k == 1:
                v=struct.unpack('!H',v)[0]
                for o, f in [(1,'trial'),
                             (2,'unknown bit 2'),
                             (4,'aol'),
                             (8,'unknown bit 4'),
                             (16,'aim'),
                             (32,'away'),
                             (1024,'activebuddy')]:
                    if v&o: self.flags.append(f)
            elif k == 2:
                self.memberSince = struct.unpack('!L',v)[0]
            elif k == 3:
                self.onSince = struct.unpack('!L',v)[0]
            elif k == 4:
                self.idleTime = struct.unpack('!H',v)[0]
            elif k == 5:
                pass
            elif k == 6:
                if v[2] == '\x00':
                    self.icqStatus = 'online'
                elif v[2] == '\x01':
                    self.icqStatus = 'away'
                elif v[2] == '\x02':
                    self.icqStatus = 'dnd'
                elif v[2] == '\x04':
                    self.icqStatus = 'out'
                elif v[2] == '\x10':
                    self.icqStatus = 'busy'
                else:
                    self.icqStatus = 'unknown'
            elif k == 10:
                self.icqIPaddy = socket.inet_ntoa(v)
            elif k == 12:
                self.icqRandom = v
            elif k == 13:
                caps=[]
                while v:
                    c=v[:16]
                    if c==CAP_ICON: caps.append("icon")
                    elif c==CAP_IMAGE: caps.append("image")
                    elif c==CAP_VOICE: caps.append("voice")
                    elif c==CAP_CHAT: caps.append("chat")
                    elif c==CAP_GET_FILE: caps.append("getfile")
                    elif c==CAP_SEND_FILE: caps.append("sendfile")
                    elif c==CAP_SEND_LIST: caps.append("sendlist")
                    elif c==CAP_GAMES: caps.append("games")
                    else: caps.append(("unknown",c))
                    v=v[16:]
                caps.sort()
                self.caps=caps
            elif k == 14: pass
            elif k == 15:
                self.sessionLength = struct.unpack('!L',v)[0]
            elif k == 16:
                self.sessionLength = struct.unpack('!L',v)[0]
            elif k == 30:
                pass
            else:
                pass


class OscarConnection:

    def connectionMade(self):
        self.state=""
        self.seqnum=0
        self.buf=''
        self.stopKeepAliveID = None
        self.setKeepAlive(4*60)

    def sendFLAP(self,data,channel = 0x02):
        header="!cBHH"
        self.seqnum=(self.seqnum+1)%0xFFFF
        seqnum=self.seqnum
        head=struct.pack(header,'*', channel,
                         seqnum, len(data))
        self.transport.send(head+str(data))

    def readFlap(self):
        header="!cBHH"
        if len(self.buf)<6: return
        flap=struct.unpack(header,self.buf[:6])
        if len(self.buf)<6+flap[3]: return
        data,self.buf=self.buf[6:6+flap[3]],self.buf[6+flap[3]:]
        return [flap[1],data]

    def dataReceived(self,data):
        self.buf=self.buf+data
        flap=self.readFlap()
        while flap:
            func=getattr(self,"oscar_%s"%self.state,None)
            if not func:
                pass
            state=func(flap)
            if state:
                self.state=state
            flap=self.readFlap()

    def setKeepAlive(self,t):
        self.keepAliveDelay=t
        self.stopKeepAlive()

    def stopKeepAlive(self):
        if self.stopKeepAliveID:
            self.stopKeepAliveID.cancel()
            self.stopKeepAliveID = None

    def disconnect(self):
        self.sendFLAP('', 0x04)


class OscarAuthenticator(OscarConnection):

    def __init__(self,username,password,deferred=None,icq=0):
        self.username=username
        self.password=password
        self.deferred=deferred
        self.icq=icq

    def oscar_(self,flap):
        if not self.icq:
            self.sendFLAP("\000\000\000\001", 0x01)
            self.sendFLAP(SNAC(0x17,0x06,0,
                               TLV(TLV_USERNAME,self.username)+
                               TLV(0x004B,'')))
            self.state="Key"
        else:
            encpass=encryptPasswordICQ(self.password)
            self.sendFLAP('\000\000\000\001'+
                          TLV(0x01,self.username)+
                          TLV(0x02,encpass)+
                          TLV(0x03,'ICQ Inc. - Product of ICQ (TM).2001b.5.18.1.3659.85')+
                          TLV(0x16,"\x01\x0a")+
                          TLV(0x17,"\x00\x05")+
                          TLV(0x18,"\x00\x12")+
                          TLV(0x19,"\000\001")+
                          TLV(0x1a,"\x0eK")+
                          TLV(0x14,"\x00\x00\x00U")+
                          TLV(0x0f,"en")+
                          TLV(0x0e,"us"),0x01)
            self.state="Cookie"

    def oscar_Key(self,data):
        snac=readSNAC(data[1])
        key=snac[5][2:]
        encpass=encryptPasswordMD5(self.password,key)
        self.sendFLAP(SNAC(0x17,0x02,0,
                           TLV(TLV_USERNAME,self.username)+
                           TLV(TLV_PASSWORD,encpass)+
                           TLV(0x004C, '')+
                           TLV(TLV_CLIENTNAME,"AOL Instant Messenger (SM), version 4.8.2790/WIN32")+
                           TLV(0x0016,"\x01\x09")+
                           TLV(TLV_CLIENTMAJOR,"\000\004")+
                           TLV(TLV_CLIENTMINOR,"\000\010")+
                           TLV(0x0019,"\000\000")+
                           TLV(TLV_CLIENTSUB,"\x0A\xE6")+
                           TLV(0x0014,"\x00\x00\x00\xBB")+
                           TLV(TLV_LANG,"en")+
                           TLV(TLV_COUNTRY,"us")+
                           TLV(TLV_USESSI,"\001")))
        return "Cookie"

    def oscar_Cookie(self,data):
        snac=readSNAC(data[1])
        if self.icq:
            i=snac[5].find("\000")
            snac[5]=snac[5][i:]
        tlvs=readTLVs(snac[5])
        if tlvs.has_key(6):
            self.cookie=tlvs[6]
            server,port=string.split(tlvs[5],":")
            self.disconnect()
            self.aimclient.socket.close()
            # XXX all of this shit needs to be elsewhere heh... like
            # a function inside of AIMClient. duh. is the sleep necessary?
            while self.aimclient.running:
                sleep(1)
            self.aimclient.oscar = MyOSCARConnection(self.username, self.cookie)
            self.aimclient.running = True
            self.aimclient.host = server
            self.aimclient.port = int(port)
            self.aimclient.connect()
            self.aimclient.oscar.connectionMade()
            self.aimclient.oscar.transport = self.aimclient.socket
            self.aimclient.start_poll()
            self.aimclient.oscar.client = self.aimclient
        elif tlvs.has_key(8):
            errorcode=tlvs[8]
            errorurl=tlvs[4]
            if errorcode=='\000\030':
                error="You are attempting to sign on again too soon.  Please try again later."
            elif errorcode=='\000\005':
                error="Invalid Username or Password."
            else: error=repr(errorcode)
            self.error(error,errorurl)
        else:
            pass
        return "None"

    def oscar_None(self,data):
        pass


class MyOSCARConnection(OscarConnection):
    snacFamilies = {
        0x01:(3, 0x0110, 0x059b),
        0x13:(3, 0x0110, 0x059b),
        0x02:(1, 0x0110, 0x059b),
        0x03:(1, 0x0110, 0x059b),
        0x04:(1, 0x0110, 0x059b),
        0x06:(1, 0x0110, 0x059b),
        0x08:(1, 0x0104, 0x0001),
        0x09:(1, 0x0110, 0x059b),
        0x0a:(1, 0x0110, 0x059b),
        0x0b:(1, 0x0104, 0x0001),
        0x0c:(1, 0x0104, 0x0001)
    }
    capabilities = None

    def __init__(self,username,cookie):
        self.cookie=cookie
        self.lastID=0
        self.supportedFamilies = ()
        self.requestCallbacks={}
        self.username=username
        self.profile = None
        self.awayMessage = None
        self.services = {}
        if not self.capabilities:
            self.capabilities = [CAP_CHAT]

    def sendSNAC(self,fam,sub,data,flags=[0,0]):
        reqid=self.lastID
        self.lastID=reqid+1
        self.sendFLAP(SNAC(fam,sub,reqid,data))

    def sendSNACnr(self,fam,sub,data,flags=[0,0]):
        self.sendFLAP(SNAC(fam,sub,0x10000*fam+sub,data))

    def oscar_(self,data):
        self.sendFLAP("\000\000\000\001"+TLV(6,self.cookie), 0x01)
        return "Data"

    def oscar_Data(self,data):
        snac=readSNAC(data[1])
        if self.requestCallbacks.has_key(snac[4]):
            d = self.requestCallbacks[snac[4]]
            del self.requestCallbacks[snac[4]]
            if snac[1]!=1:
                d.callback(snac)
            else:
                d.errback(snac)
            return
        func=getattr(self,'oscar_%02X_%02X'%(snac[0],snac[1]),None)
        if not func:
            self.oscar_unknown(snac)
        else:
            func(snac[2:])
        return "Data"

    def oscar_unknown(self,snac):
        pass

    def oscar_01_03(self, snac):
        numFamilies = len(snac[3])/2
        self.supportedFamilies = struct.unpack("!"+str(numFamilies)+'H', snac[3])
        d = ''
        for fam in self.supportedFamilies:
            if self.snacFamilies.has_key(fam):
                d=d+struct.pack('!2H',fam,self.snacFamilies[fam][0])
        self.sendSNACnr(0x01,0x17, d)

    def oscar_01_0A(self,snac):
        pass

    def oscar_01_18(self,snac):
        self.sendSNACnr(0x01,0x06,"")

    def clientReady(self):
        d = ''
        for fam in self.supportedFamilies:
            if self.snacFamilies.has_key(fam):
                version, toolID, toolVersion = self.snacFamilies[fam]
                d = d + struct.pack('!4H',fam,version,toolID,toolVersion)
        self.sendSNACnr(0x01,0x02,d)

    def parseUser(self,data,count=None):
        l=ord(data[0])
        name=data[1:1+l]
        warn,foo=struct.unpack("!HH",data[1+l:5+l])
        warn=int(warn/10)
        tlvs=data[5+l:]
        if count:
            tlvs,rest = readTLVs(tlvs,foo)
        else:
            tlvs,rest = readTLVs(tlvs), None
        u = OSCARUser(name, warn, tlvs)
        if rest == None:
            return u
        else:
            return u, rest

    def oscar_01_07(self,snac):
        self.sendSNACnr(0x01,0x08,"\x00\x01\x00\x02\x00\x03\x00\x04\x00\x05")
        self.initDone()
        self.sendSNACnr(0x13,0x02,'')
        self.sendSNACnr(0x02,0x02,'')
        self.sendSNACnr(0x03,0x02,'')
        self.sendSNACnr(0x04,0x04,'')
        self.sendSNACnr(0x09,0x02,'')

    def oscar_01_13(self,snac):
        pass

    def oscar_02_03(self, snac):
        tlvs = readTLVs(snac[3])
        self.maxProfileLength = tlvs[1]

    def oscar_03_03(self, snac):
        tlvs = readTLVs(snac[3])
        self.maxBuddies = tlvs[1]
        self.maxWatchers = tlvs[2]

    def oscar_03_0B(self, snac):
        self.updateBuddy(self.parseUser(snac[3]))

    def oscar_04_05(self, snac):
        self.sendSNACnr(0x04,0x02,'\x00\x00\x00\x00\x00\x0b\x1f@\x03\xe7\x03\xe7\x00\x00\x00\x00')

    def oscar_04_07(self, snac):
        data = snac[3]
        cookie, data = data[:8], data[8:]
        channel = struct.unpack('!H',data[:2])[0]
        data = data[2:]
        user, data = self.parseUser(data, 1)
        tlvs = readTLVs(data)
        if channel == 1:
            flags = []
            multiparts = []
            for k, v in tlvs.items():
                if k == 2:
                    while v:
                        v = v[2:]
                        messageLength, charSet, charSubSet = struct.unpack('!3H', v[:6])
                        messageLength -= 4
                        message = [v[6:6+messageLength]]
                        if charSet == 0:
                            pass
                        elif charSet == 2:
                            message.append('unicode')
                        elif charSet == 3:
                            message.append('iso-8859-1')
                        elif charSet == 0xffff:
                            message.append('none')
                        if charSubSet == 0xb:
                            message.append('macintosh')
                        if messageLength > 0: multiparts.append(tuple(message))
                        v = v[6+messageLength:]
                elif k == 3:
                    flags.append('acknowledge')
                elif k == 4:
                    flags.append('auto')
                elif k == 6:
                    flags.append('offline')
                elif k == 8:
                    iconLength, foo, iconSum, iconStamp = struct.unpack('!LHHL',v)
                    if iconLength:
                        flags.append('icon')
                        flags.append((iconLength, iconSum, iconStamp))
                elif k == 9:
                    flags.append('buddyrequest')
                elif k == 0xb:
                    pass
                elif k == 0x17:
                    flags.append('extradata')
                    flags.append(v)
                else:
                    pass
            self.receiveMessage(user, multiparts, flags)
        elif channel == 2:
            status = struct.unpack('!H',tlvs[5][:2])[0]
            requestClass = tlvs[5][10:26]
            moreTLVs = readTLVs(tlvs[5][26:])
            # XXX chat requested.. this could probably go away.
            if requestClass == CAP_CHAT:
                exchange = struct.unpack('!H',moreTLVs[10001][:2])[0]
                name = moreTLVs[10001][3:-2]
                instance = struct.unpack('!H',moreTLVs[10001][-2:])[0]
                if not self.services.has_key(SERVICE_CHATNAV):
                    self.connectService(SERVICE_CHATNAV,1)
                else:
                    self.services[SERVICE_CHATNAV].getChatInfo(exchange, name, instance).\
                        addCallback(self._cbGetChatInfoForInvite, user, moreTLVs[12])
            elif requestClass == CAP_SEND_FILE:
                if moreTLVs.has_key(11):
                    return
                name = moreTLVs[10001][9:-7]
                desc = moreTLVs[12]
                self.receiveSendFileRequest(user, name, desc, cookie)
            else:
                pass
        else:
            pass

    def oscar_09_03(self, snac):
        tlvs = readTLVs(snac[3])
        self.maxPermitList = tlvs[1]
        self.maxDenyList = tlvs[2]

    def oscar_0B_02(self, snac):
        self.reportingInterval = struct.unpack('!H',snac[3][:2])[0]

    def oscar_13_03(self, snac):
        pass

    def requestSelfInfo(self):
        self.sendSNAC(0x01, 0x0E, '')

    def requestSSI(self, timestamp = 0, revision = 0):
        return self.sendSNAC(0x13, 0x05,
            struct.pack('!LH',timestamp,revision))

    def activateSSI(self):
        self.sendSNACnr(0x13,0x07,'')

    def setProfile(self, profile):
        self.profile = profile
        tlvs = ''
        if self.profile:
            tlvs =  TLV(1,'text/aolrtf; charset="us-ascii"') + \
                    TLV(2,self.profile)
        tlvs = tlvs + TLV(5, ''.join(self.capabilities))
        self.sendSNACnr(0x02, 0x04, tlvs)

    def setIdleTime(self, idleTime):
        self.sendSNACnr(0x01, 0x11, struct.pack('!L',idleTime))

    def sendMessage(self, user, message, wantAck = 0, autoResponse = 0, offline = 0 ):
        data = ''.join([chr(random.randrange(0, 127)) for i in range(8)])
        data = data + '\x00\x01' + chr(len(user)) + user
        if not type(message) in (types.TupleType, types.ListType):
            message = [[message,]]
            if type(message[0][0]) == types.UnicodeType:
                message[0].append('unicode')
        messageData = ''
        for part in message:
            charSet = 0
            if 'unicode' in part[1:]:
                charSet = 2
            elif 'iso-8859-1' in part[1:]:
                charSet = 3
            elif 'none' in part[1:]:
                charSet = 0xffff
            if 'macintosh' in part[1:]:
                charSubSet = 0xb
            else:
                charSubSet = 0
            messageData = messageData + '\x01\x01' + \
                          struct.pack('!3H',len(part[0])+4,charSet,charSubSet)
            messageData = messageData + part[0]
        data = data + TLV(2, '\x05\x01\x00\x03\x01\x01\x02'+messageData)
        if wantAck:
            data = data + TLV(3,'')
        if autoResponse:
            data = data + TLV(4,'')
        if offline:
            data = data + TLV(6,'')
        if wantAck:
            return self.sendSNAC(0x04, 0x06, data)
        self.sendSNACnr(0x04, 0x06, data)

    def updateBuddy(self, user):
        pass

    def initDone(self):
        self.requestSelfInfo()
        self.requestSSI()
        self.activateSSI()
        self.setProfile('hi')
        self.setIdleTime(0)
        self.clientReady()

    def receiveMessage(self, user, multiparts, flags):
        message = _tags.sub('', multiparts[0][0])
        self.client.process_request(message, user.name, self)


def SNAC(fam,sub,id,data,flags=[0,0]):
    header="!HHBBL"
    head=struct.pack(header,fam,sub,
                     flags[0],flags[1],
                     id)
    return head+str(data)

def readSNAC(data):
    header="!HHBBL"
    head=list(struct.unpack(header,data[:10]))
    return head+[data[10:]]

def TLV(type,value):
    header="!HH"
    head=struct.pack(header,type,len(value))
    return head+str(value)

def readTLVs(data,count=None):
    header="!HH"
    dict={}
    while data and len(dict)!=count:
        head=struct.unpack(header,data[:4])
        dict[head[0]]=data[4:4+head[1]]
        data=data[4+head[1]:]
    if not count:
        return dict
    return dict,data

def encryptPasswordMD5(password,key):
    m=md5.new()
    m.update(key)
    m.update(md5.new(password).digest())
    m.update("AOL Instant Messenger (SM)")
    return m.digest()

def main():
    # cleanup todo:
    # aim client needs total rewrite of tcp feature
    # catch login errors
    # remove aimclient, this module will ONLY be oscar
    # use madcow's stripHTML.
    #
    # some events cause serious problems.. send file/invite to chat/etc
    #
    # also.. need to divorce the TCP part from the part that will eventually
    # be inside just protocols/aim.py ...
    #
    # keepAlives? AIM might drop an idle bot.. i'm not sure what
    # twisted does with keepalives though.. gotta look into that.
    #aim = AIMClient('madcowbot2', 'rover42', 'hi')
    aim = AIMClient('madcowbot3', 'rover42', 'hi')
    aim.start()
    return 0

if __name__ == '__main__':
    sys.exit(main())
