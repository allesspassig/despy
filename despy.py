import webbrowser
import threading
import hashlib
import socket
import base64
import time
import math

class DesmosAPI:
    lastport = 7002
    verbose = False

    def __init__(self, title='Desmos Controls', color='#1AAD57', equations=[]):
        self.port = DesmosAPI.lastport
        DesmosAPI.lastport += 1
        self.color = color
        self.numericObservers = {}
        self.listObservers = {}
        self.numericObserverLatexs = {}
        self.listObserverLatexs = {}
        self.eqns = {}
        self.eqnColors = {}
        self.eqnMinMaxStepBounds = {}
        self.nextDefaultEqnNumber = 0
        for x in equations:
            self.eqns['equation_' + str(self.nextDefaultEqnNumber)] = x
            self.nextDefaultEqnNumber += 1
        self.header = '<html lang="en">\r\n'
        self.header += '<head>\r\n<meta charset="utf-8"/>\r\n'
        self.header += '<title>' + title + '</title>\r\n'
        self.header += '</head>\r\n'
        self.header += '<body id="body">\r\n'
        self.header += '<div id="calculator" style="width: 100%; height: 100%; outline-style: solid; outline-color: ' + str(color) + '; float: left;"></div>\r\n'
        self.header += '</body>\r\n'
        self.header += '<script src=\'https://www.desmos.com/api/v1.2/calculator.js?apiKey=dcb31709b452b1cf9dc26972add0fda6\'></script>\r\n'
        self.header += '<script>\r\n  var elt = document.getElementById("calculator");\r\n  var calculator = Desmos.GraphingCalculator(elt);\r\n'
        self.footer = '</script>\r\n</html>'
        self.commsocks = []
        self.maxclients = 10

        self.ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ss.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        try:
            self.ss.bind(("127.0.0.1", self.port))
        except socket.error as err:
            print('fail', err)
            exit()
        self.ss.listen()
        def go():
            while (True):
                try:
                    if (DesmosAPI.verbose):
                        print('Waiting for socket')
                    s, address = self.ss.accept()
                    if (DesmosAPI.verbose):
                        print('Accepted ', s)
                    data = s.recv(16384).decode('utf-8')
                    lines = data.splitlines()
                    entries = {}
                    for x in lines:
                        try:
                            idx = x.index(':')
                            entries[x[0:idx]] = x[idx+2::]
                        except ValueError:
                            entries[x] = x
                    if (len(lines)>0 and len(lines[0])>0):
                        if (DesmosAPI.verbose):
                            print(lines[0])
                            maxlen = max([len(x) for x in entries])
                            for string in list(entries)[1::]:
                                print(string, ' '*(maxlen-len(string)), entries[string])
                        if ('POST' in lines[0].upper()):
                            payload = lines[len(lines)-1]
                            print('why are you sending me post requests? ', payload)
                            s.send(bytearray('HTTP/1.1 200 OK\r\n', 'utf-8'))
                            s.send(bytearray('Connection: Closed\r\n\r\n', 'utf-8'))
                            s.close()
                        if ('GET' in lines[0].upper() and len(entries)>0):
                            if ('Upgrade' in entries and entries['Upgrade']=='websocket'):
                                if ('Sec-WebSocket-Key' in entries):
                                    s.send(bytearray('HTTP/1.1 101 Switching Protocols\r\n', 'utf-8'))
                                    s.send(bytearray('Connection: Upgrade\r\n', 'utf-8'))
                                    s.send(bytearray('Upgrade: websocket\r\n', 'utf-8'))
                                    key = entries['Sec-WebSocket-Key']
                                    s.send(bytearray('Sec-WebSocket-Accept: '+base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode('utf-8')).digest()).decode('utf-8')+'\r\n\r\n', 'utf-8'))
                                    if (len(self.commsocks) < self.maxclients):
                                        self.commsocks.append(s)
                                        s.settimeout(.1)
                                        s.setblocking(False)
                                    else:
                                        s.close()
                            elif ('favicon' in lines[0]):
                                s.send(bytearray('HTTP/1.1 200 OK\r\n', 'utf-8'))
                                s.send(bytearray('Content-Type: image/x-icon\r\n', 'utf-8'))
                                s.send(bytearray('Connection: Closed\r\n\r\n', 'utf-8'))
                                fp = open('favicon.png', 'rb')
                                s.send(fp.read())
                                fp.close()
                                s.send(bytearray('\r\n\r\n', 'utf-8'))
                                s.close()
                            else:
                                s.send(bytearray('HTTP/1.1 200 OK\r\n', 'utf-8'))
                                s.send(bytearray('Content-Type: text/html\r\n', 'utf-8'))
                                s.send(bytearray('Connection: Closed\r\n\r\n', 'utf-8'))
                                s.send(bytearray(self.header, 'utf-8'))
                                #s.send(bytearray('socket.addEventListener("open", function (e) {socket.send("opened");});\r\n', 'utf-8'))
                                s.send(bytearray('const socket = new WebSocket("ws://'+socket.gethostbyname(socket.gethostname())+':'+str(self.port)+'");', 'utf-8'))
                                s.send(bytearray('socket.addEventListener("message", function (e) {calculator.setExpression({id:e.data.substring(0,e.data.indexOf(":")), latex:e.data.substring(e.data.indexOf(":")+1,e.data.indexOf(":",e.data.indexOf(":")+1)), color:e.data.substring(e.data.indexOf(":",e.data.indexOf(":")+1)+1)});});\r\n', 'utf-8'))#THIS IS THE ENTIRETY OF THE CLIENT RESPONSE CODE, updateEqn CALLS END UP HERE
                                s.send(bytearray('socket.addEventListener("error", function(e) {calculator.setExpression({latex:"An error occured, try reloading"});});', 'utf-8'))
                                s.send(bytearray('socket.addEventListener("close", function(e) {calculator.setExpression({latex:"Lost communication with program, try reloading"});});', 'utf-8'))
                                for equation in self.eqns:
                                    if (equation == 'equation_' + str(self.nextDefaultEqnNumber)):
                                        self.nextDefaultEqnNumber += 1
                                    s.send(bytearray('\r\n', 'utf-8'))
                                    eqnInnards = '{id:"' + equation + '", latex:"' + self.eqns[equation] + '"'
                                    if (equation in self.eqnColors):
                                        eqnInnards += ', color:"' + self.eqnColors[equation] + '"'
                                    if (equation in self.eqnMinMaxStepBounds):
                                        eqnInnards += ', sliderBounds:{min:"' + str(self.eqnMinMaxStepBounds[equation][0]) + '", max:"' + str(self.eqnMinMaxStepBounds[equation][1]) + '", step:"' + str(self.eqnMinMaxStepBounds[equation][2]) + '"}'
                                    s.send(bytearray('  calculator.setExpression(' + str(eqnInnards) + '});\r\n', 'utf-8'))
                                for numericObserver in self.numericObservers:
                                    s.send(bytearray('\r\n', 'utf-8'))
                                    s.send(bytearray('  var observeN_value_' + str(numericObserver) + ';\r\n', 'utf-8'))
                                    s.send(bytearray('  var observerN_' + str(numericObserver) + ' = calculator.HelperExpression({latex: "' + str(self.numericObserverLatexs[numericObserver]) + '"});\r\n', 'utf-8'))
                                    s.send(bytearray('  observerN_' + str(numericObserver) + '.observe("numericValue", function() {', 'utf-8'))
                                    s.send(bytearray('observeN_value_' + str(numericObserver) + '=observerN_' + str(numericObserver) + '.numericValue;socket.send("' + str(numericObserver) + ': "+observeN_value_' + str(numericObserver) + '+"\\n");', 'utf-8'))
                                    s.send(bytearray('});\r\n', 'utf-8'))
                                for listObserver in self.listObservers:
                                    s.send(bytearray('\r\n', 'utf-8'))
                                    s.send(bytearray('  var observeL_value_' + str(listObserver) + ';\r\n', 'utf-8'))
                                    s.send(bytearray('  var observerL_' + str(listObserver) + ' = calculator.HelperExpression({latex: "' + str(self.listObserverLatexs[listObserver]) + '"});\r\n', 'utf-8'))
                                    s.send(bytearray('  observerL_' + str(listObserver) + '.observe("listValue", function() {', 'utf-8'))
                                    s.send(bytearray('observeL_value_' + str(listObserver) + '=observerL_' + str(listObserver) + '.listValue;socket.send("' + str(listObserver) + ': "+observeL_value_' + str(listObserver) + '+"\\n");', 'utf-8'))
                                    s.send(bytearray('});\r\n', 'utf-8'))
                                s.send(bytearray(self.footer, 'utf-8'))
                                s.send(bytearray('\r\n', 'utf-8'))
                                s.close()
                except KeyboardInterrupt:
                    print('klilingser...')
                    self.ss.shutdown(socket.SHUT_RDWR)
                    self.ss.close()
                    break
        def handleClients():
            while (True): #TODO: ping sockets and kill unresponsive ones
                try:
                    if (len(self.commsocks)<1):
                        time.sleep(.1)
                    for s in self.commsocks:
                        try:
                            data = s.recv(16384)
                        except socket.error:
                            continue
                        unmasked = None
                        if (len(data)>1):
                            if (data[0]==129):
                                if (data[1]-128>=0):
                                    if (data[1]-128<126):
                                        size = data[1]-128
                                        if (len(data)>5+size):
                                            unmasked = bytearray(data[2:6+size:])
                                    elif (data[1]-128==126):
                                        if (len(data)>3):
                                            size = (data[2] << 8) | data[3]
                                            if (len(data)>7+size):
                                                unmasked = bytearray(data[4:8+size:])
                                    else:
                                        if (len(data)>9):
                                            size = (data[2]<<56)|(data[3]<<48)|(data[4]<<40)|(data[5]<<32)|(data[6]<<24)|(data[7]<<16)|(data[8]<<8)|data[9]
                                            if (len(data)>13+size):
                                                unmasked = bytearray(data[10:14+size:])
                            elif (data[0] & 9 == 1):
                                s.send(b'\x89'+data[1:128:])
                            elif (data[0] & 8 == 1):
                                self.commsocks.remove(s)
                                s.close()
                        if (unmasked is not None):
                            size += 4
                            for i in range(4, size, 4):
                                unmasked[i] = unmasked[i] ^ unmasked[0]
                            for i in range(5, size, 4):
                                unmasked[i] = unmasked[i] ^ unmasked[1]
                            for i in range(6, size, 4):
                                unmasked[i] = unmasked[i] ^ unmasked[2]
                            for i in range(7, size, 4):
                                unmasked[i] = unmasked[i] ^ unmasked[3]
                            payload = unmasked[4::].decode('utf-8')
                            try:
                                idx = payload.index(':')
                                sub = payload[0:idx]
                                if (sub in self.numericObservers):
                                    numericObserver = self.numericObservers[sub]
                                    try:
                                        dat = float(payload[idx+1::])
                                        numericObserver(dat)
                                    except ValueError:
                                            pass
                                if (sub in self.listObservers):
                                    listObserver = self.listObservers[sub]
                                    vals = payload[idx+1::].split(',')
                                    arr = []
                                    for x in vals:
                                        try:
                                            dat = float(x.strip())
                                            arr.append(dat)
                                        except ValueError:
                                            pass
                                    listObserver(arr)
                            except ValueError:
                                pass
                except KeyboardInterrupt:
                    print('killing...')
                    self.ss.shutdown(socket.SHUT_RDWR)
                    self.ss.close()
                    break
        serverThread = threading.Thread(target = go)
        clientsThread = threading.Thread(target = handleClients)
        serverThread.start()
        clientsThread.start()

    def showToUser(self):
        webbrowser.open_new_tab('http://localhost:' + str(self.port))

    # ALL OF THESE LATEX STRINGS ARE FUNCTIONAL IN DESMOS
    _cdot = '\\\\cdot'
    _lparen = '\\\\left('
    _lbrace = '\\\\left['
    _lbrack = '\\\\left\\\\{'
    _rparen = '\\\\right)'
    _rbrace = '\\\\right]'
    _rbrack = '\\\\right\\\\}'
    _sin = '\\\\sin'
    _cos = '\\\\cos'
    _tan = '\\\\tan'
    _csc = '\\\\csc'
    _sec = '\\\\sec'
    _cot = '\\\\cot'
    _asin = '\\\\arcsin'
    _acos = '\\\\arccos'
    _atan = '\\\\arctan'
    _acsc = '\\\\arccsc'
    _asec = '\\\\arcsec'
    _acot = '\\\\arccot'
    _arcsin = '\\\\arcsin'
    _arccos = '\\\\arccos'
    _arctan = '\\\\arctan'
    _arccsc = '\\\\arccsc'
    _arcsec = '\\\\arcsec'
    _arccot = '\\\\arccot'
    _sinh = '\\\\sinh'
    _cosh = '\\\\cosh'
    _tanh = '\\\\tanh'
    _csch = '\\\\csch'
    _sech = '\\\\sech'
    _coth = '\\\\coth'
    _asinh = '\\\\operatorname{arcsinh}'
    _acosh = '\\\\operatorname{arccosh}'
    _atanh = '\\\\operatorname{arctanh}'
    _acsch = '\\\\operatorname{arccsch}'
    _asech = '\\\\operatorname{arcsech}'
    _acoth = '\\\\operatorname{arccoth}'
    _arcsinh = '\\\\operatorname{arcsinh}'
    _arccosh = '\\\\operatorname{arccosh}'
    _arctanh = '\\\\operatorname{arctanh}'
    _arccsch = '\\\\operatorname{arccsch}'
    _arcsech = '\\\\operatorname{arcsech}'
    _arccoth = '\\\\operatorname{arccoth}'
    _length = '\\\\operatorname{length}'
    _leq = '\\\\leq'
    _geq = '\\\\geq'
    _alpha = '\\\\alpha'
    _beta = '\\\\beta'
    _gamma = '\\\\gamma'
    _Gamma = '\\\\Gamma'
    _delta = '\\\\delta'
    _Delta = '\\\\Delta'
    _epsilon = '\\\\epsilon'
    _varepsilon = '\\\\varepsilon'
    _zeta = '\\\\zeta'
    _eta = '\\\\eta'
    _theta = '\\\\theta'
    _Theta = '\\\\Theta'
    _vartheta = '\\\\vartheta'
    _iota = '\\\\iota'
    _kappa = '\\\\kappa'
    _lambda = '\\\\lambda' #freaking frick
    _Lambda = '\\\\Lambda'
    _mu = '\\\\mu'
    _nu = '\\\\nu'
    _xi = '\\\\xi'
    _Xi = '\\\\Xi'
    _pi = '\\\\pi'
    _varpi = '\\\\varpi'
    _Pi = '\\\\Pi'
    _rho = '\\\\rho'
    _varrho = '\\\\varrho'
    _sigma = '\\\\sigma'
    _Sigma = '\\\\Sigma'
    _tau = '\\\\tau'
    _upsilon = '\\\\upsilon'
    _Upsilon = '\\\\Upsilon'
    _phi = '\\\\phi'
    _Phi = '\\\\Phi'
    _varphi = '\\\\varphi'
    _chi = '\\\\chi'
    _psi = '\\\\psi'
    _Psi = '\\\\Psi'
    _omega = '\\\\omega'
    _Omega = '\\\\Omega'
    _greekLetters = [ _alpha, _beta, _gamma, _Gamma, _delta, _Delta, _epsilon, _varepsilon, _zeta, _eta, _theta, _Theta, _vartheta, _iota, _kappa, _lambda, _Lambda, _mu, _nu, _xi, _Xi, _pi, _varpi, _Pi, _rho, _varrho, _sigma, _Sigma, _tau, _upsilon, _Upsilon, _phi, _Phi, _varphi, _chi, _psi, _Psi, _omega, _Omega ]

    def makeBackslashesComeInPairsAndOnlyPairs(str):
        out = str.replace('\\','\\\\')
        end = False
        while (not end):
            try:
                out.index('\\\\\\')
                out = out.replace('\\\\\\','\\\\')
            except ValueError:
                end = True
        return out

    def makeBackslashesComeInSinglesAndOnlySingles(str):
        end = False
        out = str
        while (not end):
            try:
                out.index('\\\\')
                out = out.replace('\\\\','\\')
            except ValueError:
                end = True
        return out

    def addNumericObserver(self, latex, callback, name=None):
        name = self.checkName(name)
        self.numericObservers[name] = callback
        self.numericObserverLatexs[name] = DesmosAPI.makeBackslashesComeInPairsAndOnlyPairs(latex)
        return lambda x: self.updateEqn(x, name)

    def addListObserver(self, latex, callback, name=None):
        name = self.checkName(name)
        self.listObservers[name] = callback
        self.listObserverLatexs[name] = DesmosAPI.makeBackslashesComeInPairsAndOnlyPairs(latex)
        return lambda x: self.updateEqn(x, name)

    def checkName(self, name=None):
        if (name!=None and len(name)>0 and name not in self.eqns):
            return name
        while ("equation_" + str(self.nextDefaultEqnNumber) in self.eqns):
            self.nextDefaultEqnNumber += 1
        self.nextDefaultEqnNumber += 1
        return "equation_" + str(self.nextDefaultEqnNumber-1)

    def updateEqn(self, latex, name, color=None):
        if (color is not None):
            self.eqnColors[name] = color
        data = bytearray(name+':'+DesmosAPI.makeBackslashesComeInSinglesAndOnlySingles(latex)+':'+(self.eqnColors[name]if name in self.eqnColors else''), 'utf-8')
        if (len(data)<126):
            for x in self.commsocks:
                x.send(b'\x81')
                x.send(bytes([len(data)&0xff]))
                x.send(bytearray(data))
        elif (len(data)<=65536):
            for x in self.commsocks:
                x.send(b'\x81')
                x.send(b'\x7e')
                x.send(bytes([(len(data)>>8)&0xff, len(data)&0xff]))
                x.send(bytearray(data))
        else:
            for x in self.commsocks:
                x.send(b'\x81')
                x.send(b'\x7f')
                x.send(bytes([(len(data)>>56)&0xff, (len(data)>>48)&0xff, (len(data)>>40)&0xff, (len(data)>>32)&0xff, (len(data)>>24)&0xff, (len(data)>>16)&0xff, (len(data)>>8)&0xff, len(data)&0xff]))
                x.send(bytearray(data))
        return

    # LATEX MACRO METHODS
    #
    # Method     Latex Macro
    # of         \left(#1\right)
    # root       \root{}
    # root       \root[#1]{}
    # frac       \frac{}{}
    # ln         \ln\left(#1\right)
    # log        \log\left(#1\right)
    # log        \log_{#2}\left(#1\right)
    # int_egral  \int_{#2}^{#3}#1d#4      This method might make your integrals render wonky in the calculator
    # sum        \sum_{#2}^{#3}#1
    # prod       \prod_{#2}^{#3}#1
    # sin        \sin\left(#1\right)
    # cos        \cos\left(#1\right)
    # tan        \tan\left(#1\right)
    # csc        \csc\left(#1\right)
    # sec        \sec\left(#1\right)
    # cot        \cot\left(#1\right)
    # asin       \asin\left(#1\right)
    # acos       \acos\left(#1\right)
    # atan       \atan\left(#1\right)
    # acsc       \acsc\left(#1\right)
    # asec       \asec\left(#1\right)
    # acot       \acot\left(#1\right)
    # arcsin     \arcsin\left(#1\right)
    # arccos     \arccos\left(#1\right)
    # arctan     \arctan\left(#1\right)
    # arccsc     \arccsc\left(#1\right)
    # arcsec     \arcsec\left(#1\right)
    # arccot     \arccot\left(#1\right)
    # sinh       \sinh\left(#1\right)
    # cosh       \cosh\left(#1\right)
    # tanh       \tanh\left(#1\right)
    # csch       \csch\left(#1\right)
    # sech       \sech\left(#1\right)
    # coth       \coth\left(#1\right)
    # asinh      \asinh\left(#1\right)
    # acosh      \acosh\left(#1\right)
    # atanh      \atanh\left(#1\right)
    # acsch      \acsch\left(#1\right)
    # asech      \asech\left(#1\right)
    # acoth      \acoth\left(#1\right)
    # arcsinh    \arcsinh\left(#1\right)
    # arccosh    \arccosh\left(#1\right)
    # arctanh    \arctanh\left(#1\right)
    # arccsch    \arccsch\left(#1\right)
    # arcsech    \arcsech\left(#1\right)
    # arccoth    \arccoth\left(#1\right)
    # length     \operatorname{length}\left(#1\right)
    #

    def of(innards):
        return DesmosAPI._lparen + innards + DesmosAPI._rparen
    def root(innards, surdIdx=None):
        if (surdIdx is None):
            return "\\\\sqrt{" + innards + "}"
        else:
            return "\\\\sqrt[" + surdIdx + "]{" + innards + "}"
    def frac(numerator, denominator):
        return "\\\\frac{" + numerator + "}{" + denominator + "}"
    def ln(innards):
        return "\\\\ln" + DesmosAPI.of(innards)
    def log(innards):
        return "\\\\log" + DesmosAPI.of(innards)
    def log(innards, base):
        return "\\\\log_{" + base + "}" + DesmosAPI.of(innards)
    def int_egral(innards, lower, upper, wrt):
        return "\\\\int_{" + lower + "}^{" + upper + "}" + innards + "d" + wrt
    def sum(innards, lower, upper):
        return "\\\\sum_{" + lower + "}^{" + upper + "}" + innards
    def prod(innards, lower, upper):
        return "\\\\prod_{" + lower + "}^{" + upper + "}" + innards
    def sin(innards):
        return DesmosAPI._sin + DesmosAPI.of(innards)
    def cos(innards):
        return DesmosAPI._cos + DesmosAPI.of(innards)
    def tan(innards):
        return DesmosAPI._tan + DesmosAPI.of(innards)
    def csc(innards):
        return DesmosAPI._csc + DesmosAPI.of(innards)
    def sec(innards):
        return DesmosAPI._sec + DesmosAPI.of(innards)
    def cot(innards):
        return DesmosAPI._cot + DesmosAPI.of(innards)
    def asin(innards):
        return DesmosAPI._asin + DesmosAPI.of(innards)
    def acos(innards):
        return DesmosAPI._acos + DesmosAPI.of(innards)
    def atan(innards):
        return DesmosAPI._atan + DesmosAPI.of(innards)
    def acsc(innards):
        return DesmosAPI._acsc + DesmosAPI.of(innards)
    def asec(innards):
        return DesmosAPI._asec + DesmosAPI.of(innards)
    def acot(innards):
        return DesmosAPI._acot + DesmosAPI.of(innards)
    def arcsin(innards):
        return DesmosAPI._arcsin + DesmosAPI.of(innards)
    def arccos(innards):
        return DesmosAPI._arccos + DesmosAPI.of(innards)
    def arctan(innards):
        return DesmosAPI._arctan + DesmosAPI.of(innards)
    def arccsc(innards):
        return DesmosAPI._arccsc + DesmosAPI.of(innards)
    def arcsec(innards):
        return DesmosAPI._arcsec + DesmosAPI.of(innards)
    def arccot(innards):
        return DesmosAPI._arccot + DesmosAPI.of(innards)
    def sinh(innards):
        return DesmosAPI._sinh + DesmosAPI.of(innards)
    def cosh(innards):
        return DesmosAPI._cosh + DesmosAPI.of(innards)
    def tanh(innards):
        return DesmosAPI._tanh + DesmosAPI.of(innards)
    def csch(innards):
        return DesmosAPI._csch + DesmosAPI.of(innards)
    def sech(innards):
        return DesmosAPI._sech + DesmosAPI.of(innards)
    def coth(innards):
        return DesmosAPI._coth + DesmosAPI.of(innards)
    def asinh(innards):
        return DesmosAPI._asinh + DesmosAPI.of(innards)
    def acosh(innards):
        return DesmosAPI._acosh + DesmosAPI.of(innards)
    def atanh(innards):
        return DesmosAPI._atanh + DesmosAPI.of(innards)
    def acsch(innards):
        return DesmosAPI._acsch + DesmosAPI.of(innards)
    def asech(innards):
        return DesmosAPI._asech + DesmosAPI.of(innards)
    def acoth(innards):
        return DesmosAPI._acoth + DesmosAPI.of(innards)
    def arcsinh(innards):
        return DesmosAPI._arcsinh + DesmosAPI.of(innards)
    def arccosh(innards):
        return DesmosAPI._arccosh + DesmosAPI.of(innards)
    def arctanh(innards):
        return DesmosAPI._arctanh + DesmosAPI.of(innards)
    def arccsch(innards):
        return DesmosAPI._arccsch + DesmosAPI.of(innards)
    def arcsech(innards):
        return DesmosAPI._arcsech + DesmosAPI.of(innards)
    def arccoth(innards):
        return DesmosAPI._arccoth + DesmosAPI.of(innards)
    def length(innards):
        return DesmosAPI._length + DesmosAPI.of(innards)
    # END LATEX MACRO METHODS

    def toLatexList(self=None, elements=None):
        if (elements is None):
            try:
                __unusediter = iter(self)
                elements = self
            except TypeError:
                elements = []
        sb = DesmosAPI._lbrace
        for x in elements:
            sb += str(x)
            sb += ','
        if (len(elements) > 0):
            sb += str(elements[len(elements) - 1])
        sb += DesmosAPI._rbrace
        return sb

    def addEquation(self, latex, color=None, name=None):
        name = self.checkName(name)
        self.eqns[name] = DesmosAPI.makeBackslashesComeInPairsAndOnlyPairs(latex)
        if (color is not None):
            self.eqnColors[name] = color
        return lambda x: self.updateEqn(x, name)

    def addSlider(self, latex, min=0, max=1, inc='', callback=None, name=None):
        name = self.checkName(name)
        latex = DesmosAPI.makeBackslashesComeInPairsAndOnlyPairs(latex)
        try:
            idx = latex.index('=')
            self.eqns[name] = latex
            self.eqnMinMaxStepBounds[name] = [str(min),str(max),str(inc)]
            if (callback is not None):
                return self.addNumericObserver(latex[0:idx], callback, name)
            return lambda x: self.updateEqn(x, name)
        except ValueError:
            val = str(min)
            try:
                val = str((float(min)+float(max))/2)
            except ValueError:
                pass
            self.eqns[name] = latex + '=' + val
            self.eqnMinMaxStepBounds[name] = [min,max,inc]
            if (callback is not None):
                return self.addNumericObserver(latex, callback, name)
            return lambda x: self.updateEqn(x, name)

    def addPointSlider(self, latexX, latexY, minX=-1, maxX=1, incX='', minY=-1, maxY=1, incY='', callbackX=None, callbackY=None, color=None, nameX=None, nameY=None, namePoint=None):
        nameX = self.checkName(nameX)
        nameY = self.checkName(nameY)
        namePoint = self.checkName(namePoint)
        latexX = DesmosAPI.makeBackslashesComeInPairsAndOnlyPairs(latexX)
        latexY = DesmosAPI.makeBackslashesComeInPairsAndOnlyPairs(latexY)
        modx = self.addSlider(latexX, minX, maxX, incX, callbackX, nameX)
        mody = self.addSlider(latexY, minY, maxY, incY, callbackY, nameY)
        try:
            idx = latexX.index('=')
            latexX = latexX[0:idx]
        except ValueError:
            pass
        try:
            idx = latexY.index('=')
            latexY = latexY[0:idx]
        except ValueError:
            pass
        pointLatex = DesmosAPI._lparen + latexX + ',' + latexY + DesmosAPI._rparen
        pointLatex = DesmosAPI.makeBackslashesComeInPairsAndOnlyPairs(pointLatex)
        return (modx, mody, self.addEquation(pointLatex, color, namePoint))
