import threading
import socket
import webbrowser

#Doesn't work with EDGE nor IE (SSE not supported)

class DesmosAPI:
    lastport = 1000

    # ALL OF THESE LATEX STRINGS ARE FUNCTIONAL IN DESMOS
    cdot = '\\\\cdot'
    lparen = '\\\\left('
    lbrace = '\\\\left['
    lbrack = '\\\\left\\\\{'
    rparen = '\\\\right)'
    rbrace = '\\\\right]'
    rbrack = '\\\\right\\\\}'
    sin = '\\\\sin'
    cos = '\\\\cos'
    tan = '\\\\tan'
    csc = '\\\\csc'
    sec = '\\\\sec'
    cot = '\\\\cot'
    asin = '\\\\arcsin'
    acos = '\\\\arccos'
    atan = '\\\\arctan'
    acsc = '\\\\arccsc'
    asec = '\\\\arcsec'
    acot = '\\\\arccot'
    arcsin = '\\\\arcsin'
    arccos = '\\\\arccos'
    arctan = '\\\\arctan'
    arccsc = '\\\\arccsc'
    arcsec = '\\\\arcsec'
    arccot = '\\\\arccot'
    sinh = '\\\\sinh'
    cosh = '\\\\cosh'
    tanh = '\\\\tanh'
    csch = '\\\\csch'
    sech = '\\\\sech'
    coth = '\\\\coth'
    asinh = '\\\\operatorname{arcsinh}'
    acosh = '\\\\operatorname{arccosh}'
    atanh = '\\\\operatorname{arctanh}'
    acsch = '\\\\operatorname{arccsch}'
    asech = '\\\\operatorname{arcsech}'
    acoth = '\\\\operatorname{arccoth}'
    arcsinh = '\\\\operatorname{arcsinh}'
    arccosh = '\\\\operatorname{arccosh}'
    arctanh = '\\\\operatorname{arctanh}'
    arccsch = '\\\\operatorname{arccsch}'
    arcsech = '\\\\operatorname{arcsech}'
    arccoth = '\\\\operatorname{arccoth}'
    leq = '\\\\leq'
    geq = '\\\\geq'
    alpha = '\\\\alpha'
    beta = '\\\\beta'
    gamma = '\\\\gamma'
    Gamma = '\\\\Gamma'
    delta = '\\\\delta'
    Delta = '\\\\Delta'
    epsilon = '\\\\epsilon'
    varepsilon = '\\\\varepsilon'
    zeta = '\\\\zeta'
    eta = '\\\\eta'
    theta = '\\\\theta'
    Theta = '\\\\Theta'
    vartheta = '\\\\vartheta'
    iota = '\\\\iota'
    kappa = '\\\\kappa'
    lambda_ = '\\\\lambda' #freaking frick
    Lambda = '\\\\Lambda'
    mu = '\\\\mu'
    nu = '\\\\nu'
    xi = '\\\\xi'
    Xi = '\\\\Xi'
    pi = '\\\\pi'
    varpi = '\\\\varpi'
    Pi = '\\\\Pi'
    rho = '\\\\rho'
    varrho = '\\\\varrho'
    sigma = '\\\\sigma'
    Sigma = '\\\\Sigma'
    tau = '\\\\tau'
    upsilon = '\\\\upsilon'
    Upsilon = '\\\\Upsilon'
    phi = '\\\\phi'
    Phi = '\\\\Phi'
    varphi = '\\\\varphi'
    chi = '\\\\chi'
    psi = '\\\\psi'
    Psi = '\\\\Psi'
    omega = '\\\\omega'
    Omega = '\\\\Omega'
    greekLetters = [ alpha, beta, gamma, Gamma, delta, Delta, epsilon, varepsilon, zeta, eta, theta, Theta, vartheta, iota, kappa, lambda_, Lambda, mu, nu, xi, Xi, pi, varpi, Pi, rho, varrho, sigma, Sigma, tau, upsilon, Upsilon, phi, Phi, varphi, chi, psi, Psi, omega, Omega ]
   
    debug = False
    def __init__(self, title='Desmos Controls', color=0x1AAD57, equations=[]):
        self.port = DesmosAPI.lastport
        DesmosAPI.lastport += 1
        self.pageSource = ''
        self.color = color
        self.numericObservers = {}
        self.listObservers = {}
        self.numericObserverLatexs = {}
        self.listObserverLatexs = {}
        self.eqns = {}
        self.eqnColors = {}
        self.eqnMinMaxStepBounds = {}
        self.nextDefaultEqnNumber = 0
        self.longpoll = None
        for x in equations:
            self.eqns['equation_' + str(self.nextDefaultEqnNumber)] = x
            self.nextDefaultEqnNumber += 1
        self.header = '<html lang="en">\r\n'
        self.header += '<head>\r\n<meta charset="utf-8"/>\r\n'
        self.header += '<title>' + title + '</title>\r\n'
        self.header += '</head>\r\n'
        self.header += '<body id="body">\r\n'
        self.header += '<div id="calculator" style="width: 100%; height: 100%; outline-style: solid; outline-color: ' + str(color) + '; float: left;"></div>\r\n'
        self.header += "</body>\r\n"
        self.header += "<script src=\"https://www.desmos.com/api/v1.2/calculator.js?apiKey=dcb31709b452b1cf9dc26972add0fda6\"></script>\r\n"
        self.header += '<script>\r\n  var elt = document.getElementById("calculator");\r\n  var calculator = Desmos.GraphingCalculator(elt);\r\n'
        self.footer = '</script>\r\n</html>'

        self.ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.ss.bind(('127.0.0.1', self.port))
        except socket.error as err:
            print('fail', err)
            exit()
        self.ss.listen()
        def go():
            while (True):
                if (DesmosAPI.debug):
                    print('Waiting for socket')
                s, address = self.ss.accept()
                if (DesmosAPI.debug):
                    print('Accepted ', s)
                data = s.recv(16384).decode('utf-8')
                lines = data.splitlines()
                entries = {}
                for x in lines:
                    try:
                        idx = x.index(':')
                        entries[x[0:idx]] = x[idx+1::]
                    except ValueError:
                        entries[x] = x
                if (len(lines)>0 and len(lines[0])>0):
                    if (DesmosAPI.debug):
                        print(lines[0])
                        maxlen = max([len(x) for x in entries])
                        for string in list(entries)[1::]:
                            print(string, ' '*(maxlen-len(string)), entries[string])
                    if ('POST' in lines[0].upper()):
                        payload = lines[len(lines)-1]
                        s.send(bytearray('HTTP/1.1 200 OK\r\n', 'utf-8'))
                        s.send(bytearray('Connection: Closed\r\n\r\n', 'utf-8'))
                        s.close()
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
                                    except ValueError:
                                        pass
                                listObserver(arr)
                        except ValueError:
                            pass
                    if ('GET' in lines[0].upper() and len(entries)>0):
                        if ('longpoll' in lines[0]):
                            self.longpoll = s
                        elif ('favicon' in lines[0]): # TODO: return favicon when requested
                            print('requested image')
                            s.close()
                        else:
                            s.send(bytearray('HTTP/1.1 200 OK\r\n', 'utf-8'))
                            s.send(bytearray('Content-Type: text/html\r\n', 'utf-8'))
                            s.send(bytearray('Connection: Closed\r\n\r\n', 'utf-8'))
                            s.send(bytearray(self.header, 'utf-8'))
                            s.send(bytearray('  var xhrlongpoll = new XMLHttpRequest();xhrlongpoll.open("GET", "longpoll");xhrlongpoll.send();xhrlongpoll.addEventListener("load", function(e) {s=xhrlongpoll.responseText;console.log(s);calculator.setExpression({id:s.substr(0,s.indexOf(":")),latex:s.substr(s.indexOf(":")+1)});xhrlongpoll.open("GET", "longpoll");xhrlongpoll.send();});\r\n', 'utf-8'))
                            for equation in self.eqns:
                                if (equation == 'equation_' + str(self.nextDefaultEqnNumber)):
                                    self.nextDefaultEqnNumber += 1
                                s.send(bytearray('\r\n', 'utf-8'))
                                eqnInnards = '{id:"' + equation + '", latex:"' + self.eqns[equation] + '"'
                                if (equation in self.eqnColors):
                                    eqnInnards += ', color:"' + self.eqnColors[equation] + '"'
                                if (equation in self.eqnMinMaxStepBounds):
                                    eqnInnards += ', sliderBounds:{min:"' + self.eqnMinMaxStepBounds[equation][0] + '", max:"' + self.eqnMinMaxStepBounds[equation][1] + '", step:"' + self.eqnMinMaxStepBounds[equation][2] + '"}'
                                s.send(bytearray('  calculator.setExpression(' + eqnInnards + '});\r\n', 'utf-8'))
                            for numericObserver in self.numericObservers:
                                s.send(bytearray('\r\n', 'utf-8'))
                                s.send(bytearray('  var observeN_value_' + numericObserver + ';\r\n', 'utf-8'))
                                s.send(bytearray('  var observerN_' + numericObserver + ' = calculator.HelperExpression({latex: "' + self.numericObserverLatexs[numericObserver] + '"});\r\n', 'utf-8'))
                                s.send(bytearray('  observerN_' + numericObserver + '.observe("numericValue", function() {', 'utf-8'))
                                s.send(bytearray('observeN_value_' + numericObserver + '=observerN_' + numericObserver + '.numericValue;\r\n', 'utf-8'))
                                s.send(bytearray('  var xhr = new XMLHttpRequest();xhr.open("POST","http://localhost:' + str(self.port) + '",true);xhr.send("' + numericObserver + ': "+observeN_value_' + numericObserver + '+"\\n");', 'utf-8'))
                                s.send(bytearray('});\r\n', 'utf-8'))
                            for listObserver in self.listObservers:
                                s.send(bytearray('\r\n', 'utf-8'))
                                s.send(bytearray('  var observeL_value_' + listObserver + ';\r\n', 'utf-8'))
                                s.send(bytearray('  var observerL_' + listObserver + ' = calculator.HelperExpression({latex: "' + self.listObserverLatexs[listObserver] + '"});\r\n', 'utf-8'))
                                s.send(bytearray('  observerL_' + listObserver + '.observe("listValue", function() {', 'utf-8'))
                                s.send(bytearray('observeL_value_' + listObserver + '=observerL_' + listObserver + '.listValue;\r\n', 'utf-8'))
                                s.send(bytearray('  var xhr = new XMLHttpRequest();xhr.open("POST","http://localhost:' + str(self.port) + '",true);xhr.send("' + listObserver + ': "+observeL_value_' + listObserver + '+"\\n");', 'utf-8'))
                                s.send(bytearray('});\r\n', 'utf-8'))
                            s.send(bytearray('\r\n', 'utf-8'))
                            s.send(bytearray(self.footer, 'utf-8'))
                            s.send(bytearray('\r\n', 'utf-8'))
                            s.close()
        serverThread = threading.Thread(target = go)
        serverThread.start()

    def showToUser(self):
        webbrowser.open_new_tab('http://localhost:' + str(self.port))

    def addNumericObserver(self, latex, callback, name=None):
        name = self.checkName(name)
        self.numericObservers[name] = callback
        self.numericObserverLatexs[name] = latex
        return lambda x: self.asyncUpdateEqn(x, name)

    def addListObserver(self, latex, callback, name=None):
        name = self.checkName(name)
        self.listObservers[name] = callback
        self.listObserverLatexs[name] = latex
        return lambda x: self.asyncUpdateEqn(x, name)

    def checkName(self, name=None):
        if (name!=None and len(name)>0 and name not in self.eqns):
            return name
        while ("equation_" + str(self.nextDefaultEqnNumber) in self.eqns):
            self.nextDefaultEqnNumber += 1
        self.nextDefaultEqnNumber += 1
        return "equation_" + str(self.nextDefaultEqnNumber-1)

    def asyncUpdateEqn(self, latex, name):
        while (self.longpoll is None or self.longpoll.fileno()<0):
            pass
        self.longpoll.send(bytearray('HTTP/1.1 200 OK\r\n', 'utf-8'))
        self.longpoll.send(bytearray('Content-Type: text/html\r\n', 'utf-8'))
        self.longpoll.send(bytearray('Connection: Closed\r\n\r\n', 'utf-8'))
        self.longpoll.send(bytearray(name+':'+latex.replace('\\\\','\\'), 'utf-8'))
        self.longpoll.close()
        self.longpoll = None

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
    #

    def of(innards):
        return lparen + innards + rparen
    def root(innards):
        return "\\\\sqrt{" + innards + "}"
    def root(innards, surdIdx):
        return "\\\\sqrt[" + surdIdx + "]{" + innards + "}"
    def frac(numerator, denominator):
        return "\\\\frac{" + numerator + "}{" + denominator + "}"
    def ln(innards):
        return "\\\\ln" + of(innards)
    def log(innards):
        return "\\\\log" + of(innards)
    def log(innards, base):
        return "\\\\log_{" + base + "}" + of(innards)
    def int_egral(innards, lower, upper, wrt):
        return "\\\\int_{" + lower + "}^{" + upper + "}" + innards + "d" + wrt
    def sum(innards, lower, upper):
        return "\\\\sum_{" + lower + "}^{" + upper + "}" + innards
    def prod(innards, lower, upper):
        return "\\\\prod_{" + lower + "}^{" + upper + "}" + innards
    def sin(innards):
        return sin + of(innards)
    def cos(innards):
        return cos + of(innards)
    def tan(innards):
        return tan + of(innards)
    def csc(innards):
        return csc + of(innards)
    def sec(innards):
        return sec + of(innards)
    def cot(innards):
        return cot + of(innards)
    def asin(innards):
        return asin + of(innards)
    def acos(innards):
        return acos + of(innards)
    def atan(innards):
        return atan + of(innards)
    def acsc(innards):
        return acsc + of(innards)
    def asec(innards):
        return asec + of(innards)
    def acot(innards):
        return acot + of(innards)
    def arcsin(innards):
        return arcsin + of(innards)
    def arccos(innards):
        return arccos + of(innards)
    def arctan(innards):
        return arctan + of(innards)
    def arccsc(innards):
        return arccsc + of(innards)
    def arcsec(innards):
        return arcsec + of(innards)
    def arccot(innards):
        return arccot + of(innards)
    def sinh(innards):
        return sinh + of(innards)
    def cosh(innards):
        return cosh + of(innards)
    def tanh(innards):
        return tanh + of(innards)
    def csch(innards):
        return csch + of(innards)
    def sech(innards):
        return sech + of(innards)
    def coth(innards):
        return coth + of(innards)
    def asinh(innards):
        return asinh + of(innards)
    def acosh(innards):
        return acosh + of(innards)
    def atanh(innards):
        return atanh + of(innards)
    def acsch(innards):
        return acsch + of(innards)
    def asech(innards):
        return asech + of(innards)
    def acoth(innards):
        return acoth + of(innards)
    def arcsinh(innards):
        return arcsinh + of(innards)
    def arccosh(innards):
        return arccosh + of(innards)
    def arctanh(innards):
        return arctanh + of(innards)
    def arccsch(innards):
        return arccsch + of(innards)
    def arcsech(innards):
        return arcsech + of(innards)
    def arccoth(innards):
        return arccoth + of(innards)
    # END LATEX MACRO METHODS

    def toLatexList(self, elements):
        sb = DesmosAPI.lbrace
        for x in elements:
            sb += str(x)
            sb += ','
        if (len(elements) > 0):
            sb += str(elements[len(elements) - 1])
        sb += DesmosAPI.rbrace
        return sb

    def addEquation(self, latex, color=None, name=None):
        name = self.checkName(name)
        self.eqns[name] = latex
        if (color is not None):
            self.eqnColors[name] = color
        return lambda x: self.asyncUpdateEqn(x, name)

    def addSlider(self, latex, min=0, max=1, inc='', callback=None, name=None):
        name = self.checkName(name)
        try:
            idx = latex.index('=')
            self.eqns[name] = latex
            self.eqnMinMaxStepBounds[name] = [str(min),str(max),str(inc)]
            if (callback is not None):
                return self.addNumericObserver(latex[0:idx], callback, name)
            return lambda x: self.asyncUpdateEqn(x, name)
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
            return lambda x: self.asyncUpdateEqn(x, name)

    def addPointSlider(self, latexX, latexY, minX=-1, maxX=1, incX='', minY=-1, maxY=1, incY='', callbackX=None, callbackY=None, color=None, nameX=None, nameY=None, namePoint=None):
        nameX = self.checkName(nameX)
        nameY = self.checkName(nameY)
        namePoint = self.checkName(namePoint)
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
        return (modx, mody, self.addEquation(DesmosAPI.lparen + latexX + ',' + latexY + DesmosAPI.rparen, color, namePoint))
