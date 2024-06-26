from IPython.display import display, Math, Markdown

import matplotlib.pyplot as plt

from scipy import stats as st
import sympy as sp
import numpy as np
import copy as cp
import pandas as pd

import random as rnd

from formulab import curve_fit, plots, stats, utils
import formulab.config as cfg

class sym():
    def __init__(self, name, unit=''):
        self.argument, self.subindex, self.flatname, self.printname, self.name = utils.name_splitter(name)  
        self.strUnit = unit
        self.unit = sp.parsing.sympy_parser.parse_expr(unit, transformations=sp.parsing.sympy_parser.T[:]) if unit != '' else 1
        
        self.val = sp.Symbol(rf'\overline{{{self.printname}}}')
        self.valr = sp.Symbol(rf'\overline{{{self.argument}_{{{self.subindex}\, rounded}}}}')
        self.sd = sp.Symbol(rf's_{{{self.flatname}}}')
        self.sdm = sp.Symbol(rf's_{{\overline{{{self.flatname}}}}}')
        self.n = sp.Symbol(rf'n_{{{self.flatname}}}')
        self.nu = sp.Symbol(rf'\nu_{{{self.flatname}}}')
        self.u = sp.Symbol(rf'u_{{{self.flatname}}}')
        self.u_st = sp.Symbol(rf'u_{{st\,{self.flatname}}}')
        
        self.cov={}
        pass
    
class expr():
    def __init__(self, f):
        self.d = {x: sp.diff(f.f, x) for x in f.variables}
        self.sdm=sp.sqrt(sp.expand((f.sym.dVector*f.sym.covMatrix*f.sym.dVector.T)[0]))
        # self.nu = f.sym.sdm**4/sum((f.sym.d[x] * x.sym.sdm)**4/x.sym.nu for x in f.variables)
        self.nu = f.sym.sdm**4/sp.expand((f.sym.dVector.applyfunc(lambda x: x**2)*f.sym.nuMatrix*(f.sym.covMatrix*f.sym.dVector.T).applyfunc(lambda x: x**2))[0])
        self.nuUnexpanded = f.sym.sdm**4/(f.sym.dVector.applyfunc(lambda x: x**2)*f.sym.nuMatrix*(f.sym.covMatrix*f.sym.dVector.T).applyfunc(lambda x: x**2))[0]
        pass

class param(sp.Symbol):
    def __new__(self, name, val, unit='', vbs=cfg.vbs):
        symbols = sym(name, unit)
        self = sp.Symbol.__new__(self, symbols.printname)
        self.sym = symbols
        self.unit = self.sym.unit if self.sym.unit != 1 else ''
        
        self.val = val
        self.display(vbs=vbs)
        return self
    
    def display(self, vbs=cfg.vbs):
        if vbs>=1: display(Math(rf'{self} = {self.val} \, {sp.latex(self.unit)}'))
        return

class param_list():
    def __init__(self, names=[], vals=[], units=[], vbs=cfg.vbs):
        self.n = len(names)
        if not vals: vals = [1]*self.n
        if not units: units = ['']*self.n
        
        self.params = np.empty(self.n, dtype=object)
        for i in range(0,self.n):
            a,s,flat,printname,name=utils.name_splitter(names[i])
            self.params[i]=param(name, vals[i], units[i], vbs=vbs)
            setattr(self, name, self.params[i])
        pass
    
    def display(self, vbs=cfg.vbs):
        for x in self.params:
            x.display(vbs=vbs)
        return  
    
class var(sp.Symbol):
    def __new__(self, name, values, unit='', alpha=cfg.alpha, vbs=cfg.vbs): #values should be dict or array of values
        symbols = sym(name, unit)
        self = sp.Symbol.__new__(self, symbols.printname)
        self.sym = symbols
        self.unit = self.sym.unit if self.sym.unit != 1 else ''
        
        return self.calc(values, alpha=alpha, vbs=vbs)
        
    def calc(self, values, alpha=cfg.alpha, vbs=cfg.vbs):
        self.sym.cov[self]=self.sym.sdm**2
        self.cov={self:0}
        
        self.values = values
        self.alpha=0
        
        if utils.is_number(values): values = {'val': values}
        
        if type(values) is dict:
            values = utils.var_dict(**values)
            for key, value in values.items():
                setattr(self, key, value)
            if self.val is None: print(f'Insufficient data'); return
            else: 
                self.prec = -stats.magnitude(self.val)
                self.dec = self.prec if self.prec>0 else 0
            if self.n is None: self.n, self.nu = 1, 0
            else: self.nu = int(self.n-1)
            if self.sd is None:
                if self.sdm is None: 
                    self.sd, self.sdm=0, 0
                    if vbs>=2: print(f'Warning var has no attributes')
                    return self
                self.sd = self.sdm
            else: self.sdm = self.sd/np.sqrt(self.n)   #Standard Deviation of the mean
            
        elif isinstance(values, (list, np.ndarray)):
            self.val = np.mean(values)  #mean value
            self.n = len(values)
            self.nu = int(self.n-1)
            self.sd = np.std(values, ddof=1)   #Standard Deviation
            self.sdm = self.sd/np.sqrt(self.n)   #Standard Deviation of the mean
        else: print (rf'Invalid data type {type(values)}'); return
        
        self.cov[self]=self.sdm**2
        self.prec = -stats.magnitude(self.sdm)
        self.dec = self.prec if self.prec>0 else 0
        self.u = round(self.sdm, self.prec)   #Confidence Interval of 68%
        self.valr = round(self.val, self.prec)    #rounded value

        if alpha!=0: 
            self.u_st = stats.u_st(self.nu, self.sdm, alpha).round(self.prec) #Confidence Interval of 95%
            self.alpha = alpha
        
        self.display(vbs=vbs)
        return self
    
    def set_cov(self, var, cov):
        self.cov[var]=cov
        self.sym.cov[var]=sp.Symbol(rf's_{{\overline{{{self.sym.flatname}{var.sym.flatname}}}}}')
    
    def display(self, vbs=cfg.vbs):
        if vbs>=2: display(Math(rf'{self.sym.val} = {self.val} \, {sp.latex(self.unit)}'))
        if vbs>=2: display(Math(rf'{self.sym.sd} = {self.sd} \quad {self.sym.sdm} = {self.sdm} \quad {self.sym.nu} = {self.nu}'))
        if vbs>=1: display(Math(rf'{self} = ({self.valr:.{self.dec}f} \pm {self.u:.{self.dec}f}) \, {sp.latex(self.unit)}'))
        if self.alpha!=0 and self.u_st and vbs>=1: display(Math(rf'\text{{Intervalo de confianza de \({int((1-self.alpha)*100)}\%\):}}\quad {self.sym.argument}_{{{self.sym.subindex} \, {int((1-self.alpha)*100)}\%}}=({self.valr:.{self.dec}f} \pm {self.u_st:.{self.dec}f}) \, {sp.latex(self.unit)}'))
        return
        
class varList(sp.Symbol):
    def __new__(self, name, values, unit='', alpha=0, vbs=cfg.vbs):
        symbols = sym(name, unit)
        self = sp.Symbol.__new__(self, symbols.printname)
        self.sym = symbols
        self.unit = self.sym.unit if self.sym.unit != 1 else ''
        
        return self.calc(values, alpha=alpha, vbs=vbs)
        
    def calc(self, values, alpha=0, vbs=cfg.vbs):
        self.sym.cov[self]=self.sym.sdm**2
        self.cov={}
        
        self.values = values
        
        self.n = len(values)
        if type(values) is dict:
            if 'values' in values:
                self.n = len(values['values'])
                values = values['values']
            elif 'val' in values:
                self.n=len(values['val'])
                if 'n' not in values: values['n'] = [None]*self.n
                elif not isinstance(values['n'], (list, np.ndarray)): values['n'] = [values['n']]*self.n
                
                if 'sd' not in values: values['sd'] = [None]*self.n
                elif not isinstance(values['sd'], (list, np.ndarray)): values['sd'] = [values['sd']]*self.n
                
                if 'sdm' not in values: values['sdm'] = [None]*self.n
                elif not isinstance(values['sdm'], (list, np.ndarray)): values['sdm'] = [values['sdm']]*self.n
                
                if 'u' not in values: values['u'] = [None]*self.n
                elif not isinstance(values['u'], (list, np.ndarray)): values['u'] = [values['u']]*self.n
                
                values = [utils.var_dict(val=values['val'][i], sd=values['sd'][i], sdm=values['sdm'][i], u=values['u'][i], n=values['n'][i]) for i in range(0, self.n)]
        elif not isinstance(values, (list, np.ndarray)):
            print (rf'Invalid data type {type(values)}'); pass
        
        names = [rf'{self.sym.name}{str(i+1)}' for i in range(0, self.n)] #Subindexed
        
        self.vars = np.empty(self.n, dtype=object)
        self.val, self.valr, self.sd, self.sdm, self.u, self.nvar, self.nu = np.empty(self.n), np.empty(self.n), np.empty(self.n), np.empty(self.n), np.empty(self.n), np.empty(self.n), np.empty(self.n)
            
        for i in range(0, self.n):
            self.vars[i] = var(names[i], values[i], unit=self.sym.strUnit, alpha=alpha, vbs=vbs)
            self.val[i], self.valr[i], self.sd[i], self.sdm[i], self.u[i], self.nvar[i], self.nu[i] = self.vars[i].val, self.vars[i].valr, self.vars[i].sd, self.vars[i].sdm, self.vars[i].u, self.vars[i].n, self.vars[i].nu
            ## Create tuple/list method for var object that returns all of this
        self.cov[self]=self.sdm**2
        
        #develop a better table
        tableDictx={rf'${self}\, [{self.unit}]$': [rf'${vari.val:.{vari.dec}f}$' for vari in self.vars]}
        self.formatted=pd.DataFrame(tableDictx).to_markdown()
        
        return self
    
    def __call__(self, n=0):
        if n==0:
            display(Markdown(self.formatted))
            return self 
        return self.vars[n-1]
    
    def set_cov(self, var, cov):
        self.cov[var]=cov
        self.sym.cov[var]=sp.Symbol(rf's_{{\overline{{{self.sym.flatname}{var.sym.flatname}}}}}')
        
    def display(self, vbs=cfg.vbs):
        for x in self.vars:
            x.display(vbs=vbs)
        return
    
class table():
    def __init__(self, fName, varNames='', sep=',', vbs=1):
        self.table, self.vars, self.varsU, self.n = utils.read_file(fName, varNames=varNames, sep=sep)
        self.varls={}
        for i in range(0,self.n):    
            nameunit=self.vars[i].replace(' ', '').replace(']','').split('[')
            name=nameunit[0]
            unit=nameunit[-1]
            if len(nameunit)!=2: unit=''
            a,s,flat,printname,name=utils.name_splitter(name)
            self.varls[name]=varList(name, {'val': list(self.table.loc[:][self.vars[i]]), 'u': list(self.table.loc[:][self.varsU[i]])}, unit, vbs=vbs)
            setattr(self, name, self.varls[name])
        
        tableDictx={}
        for key, varlist in self.varls.items():
            tableDictx[rf'${varlist}\, [{varlist.unit}]$']=[rf'${vari.val:.{vari.dec}f}$' for vari in varlist.vars]
            tableDictx[rf'${varlist.sym.u}\, [{varlist.unit}]$']=[rf'${vari.u:.{vari.dec}f}$' for vari in varlist.vars]
        
        self.formatted = pd.DataFrame(tableDictx).to_markdown()
        pass
    
    def __repr__(self):
        return str(display(Markdown(self.formatted)))

class func(sp.Symbol):
    def __new__(self, name, f, unit='', calcEv=True, calcU=True, alpha=cfg.alpha, vbs=cfg.vbs):
        symbols = sym(name, unit)
        self = sp.Symbol.__new__(self, symbols.printname)
        self.sym = symbols
        self.unit = self.sym.unit if self.sym.unit != 1 else ''
        
        return self.calc(f, calcEv=calcEv, calcU=calcU, alpha=alpha, vbs=vbs)
    
    def calc(self, f, calcEv=True, calcU=True, alpha=cfg.alpha, vbs=cfg.vbs):
        self.sym.cov[self]=self.sym.sdm**2
        self.cov={}
        
        self.f = sp.nsimplify(f)
        self.fsymbols = list(f.free_symbols)   #Get all variables and parameters
        
        self.id=rnd.randint(10**5,10**6)
        if not calcEv: 
            self.display(calcEv=calcEv, calcU=calcU, vbs=vbs)
            self.getsym()
        else: self(calcU=calcU, alpha=alpha, vbs=vbs)
        return self
    
    def getsym(self):
        self.vars, self.varsl, self.params = [],[],[]
        for x in self.fsymbols:  #Classify them
            tx = type(x)
            if tx is var: self.vars.append(x)
            elif tx is varList: self.varsl.append(x)
            elif tx is param: self.params.append(x)
            else: print (rf'Invalid variable type {tx}'); pass
        self.variables = self.vars + self.varsl
        
        self.d={}
        self.sym.d={x: sp.Symbol(rf'\frac{{\partial {self}}}{{\partial {x}}}') for x in self.variables}
        self.sym.dVector=sp.Matrix([[self.sym.d[x] for x in self.variables]])
        self.sym.covMatrix=sp.Matrix([[x.sym.cov.get(y,0) for y in self.variables] for x in self.variables])
        self.sym.nuMatrix = sp.diag(*[1/x.sym.nu for x in self.variables])
        for i in range(0,self.sym.covMatrix.rows):
            for j in range(0,self.sym.covMatrix.cols):
                self.sym.covMatrix[i,j]=self.sym.covMatrix[j,i]
        self.expr=expr(self)
    
    def __call__(self, values={}, calcU=True, alpha=cfg.alpha, vbs=cfg.vbs):
        self.getsym()
        self.symsub = {}
        self.many = {}
        
        for x in self.fsymbols:
            self.symsub[x] = x.val
            
        for x in self.variables:
            self.symsub.update({x.sym.sdm: x.sdm, x.sym.nu: x.nu})
            self.symsub.update({v:x.cov[y] for y,v in x.sym.cov.items()})
                
        self.symsub.update(values)
        for k, v in self.symsub.items():
            if isinstance(v, (list, np.ndarray)):
                self.many[k]=v      #adding dict of list to a new dict
            if k==x.sym.sdm:
                self.symsub.update({x.sym.cov[x]:v**2})
                
        for x in self.variables:    ##This SHOULD be simplified
            if x in self.many:
                lenx=len(self.symsub[x])
                if isinstance(self.symsub[x.sym.sdm], (list, np.ndarray)):
                    if len(self.symsub[x.sym.sdm])!=lenx:
                        self.symsub[x.sym.sdm] = self.symsub[x.sym.sdm][0]
                        self.symsub[x.sym.cov[x]] = self.symsub[x.sym.sdm]**2
                        self.many.pop(x.sym.sdm)
                        self.many.pop(x.sym.cov[x])
                        if vbs>=2: print(rf'Warning: First {x.sym.sdm} is being used')
                if isinstance(self.symsub[x.sym.nu], (list, np.ndarray)):
                    if len(self.symsub[x.sym.nu])!=lenx:
                        self.symsub[x.sym.nu] = self.symsub[x.sym.nu][0]
                        self.many.pop(x.sym.nu)
                        if vbs>=2: print(rf'Warning: First {x.sym.nu} is being used')
                        
                for y,v in x.sym.cov.items():
                    if isinstance(self.symsub[x.sym.cov[y]], (list, np.ndarray)):
                        if len(self.symsub[x.sym.cov[y]])!=lenx:
                            self.symsub[x.sym.cov[y]] = self.symsub[x.sym.cov[y]][0]
                            self.many.pop(x.sym.cov[y])
                            if vbs>=2: print(rf'Warning: First {x.sym.cov[y]} is being used')
            else:
                if isinstance(self.symsub[x.sym.sdm], (list, np.ndarray)):
                    self.symsub[x.sym.sdm] = self.symsub[x.sym.sdm][0]
                    self.symsub[x.sym.cov[x]] = self.symsub[x.sym.sdm]**2
                    self.many.pop(x.sym.sdm)
                    if vbs>=2: print(rf'Warning: First {x.sym.sdm} is being used')
                if isinstance(self.symsub[x.sym.nu], (list, np.ndarray)):
                    self.symsub[x.sym.nu] = self.symsub[x.sym.nu][0]
                    self.many.pop(x.sym.nu)
                    if vbs>=2: print(rf'Warning: First {x.sym.nu} is being used')
                
                for y,v in x.sym.cov.items():
                    if isinstance(self.symsub[x.sym.cov[y]], (list, np.ndarray)):
                        self.symsub[x.sym.cov[y]] = self.symsub[x.sym.cov[y]][0]
                        self.many.pop(x.sym.cov[y])
                        if vbs>=2: print(rf'Warning: First {x.sym.cov[y]} is being used')
                 
        self.manyld=[dict(zip(self.many, t)) for t in zip(*self.many.values())]  #turning dict of lists to list of dicts
        listlen = len(self.manyld)

        setlen=len({len(v) for k,v in self.many.items()}) #the length of the set of number of lengths of lists
        # if setlen > 1:
        #     print('all var_lists must be of same length')
        #     return
        # elif setlen==1:
        if setlen >= 1:
            self.out, self.vals=np.empty(listlen, dtype=dict), np.empty(listlen)
            for i in range(0,listlen):
                self.symsub.update(self.manyld[i])
                if vbs>=1: display(Math(rf'\text{{Evaluando en}}\quad {self.manyld[i]}'))
                self.out[i]=self.ev(calcU=calcU, alpha=alpha, vbs=vbs)
                self.vals[i]=self.out[i][self.sym.val]
        else:
            self.out=self.ev(calcU=calcU, alpha=alpha, vbs=vbs)
        return self.out
    
    def ev(self, calcU=True, alpha=cfg.alpha, vbs=cfg.vbs):
        self.val = self.f.subs(self.symsub).evalf()
        if not calcU: 
            self.prec = -stats.magnitude(self.val)
            self.dec = self.prec if self.prec>0 else 0
            self.display(calcU=calcU, vbs=vbs)
            return {self.sym.val: self.val}
        
        for x in self.variables:
            self.d[x] = self.expr.d[x].subs(self.symsub).evalf()
            self.symsub[self.sym.d[x]] = self.d[x]
            
        self.sdm=self.expr.sdm.subs(self.symsub).evalf()
        self.sd=self.sdm
        
        self.prec = -stats.magnitude(self.sdm)
        self.dec = self.prec if self.prec>0 else 0
        self.u = round(self.sdm, self.prec)
        self.valr = round(self.val, self.prec)
        
        self.alpha=0
        if alpha==0:
            self.display(calcU=calcU, vbs=vbs)
            return {self.sym.val: self.val, 'dsym': self.sym.d, 'd': self.d, self.sym.sdm: self.sdm, self.sym.u: self.u, self.sym.valr: self.valr}

        self.alpha=alpha
        self.symsub[self.sym.sdm] = self.sdm
        
        self.nufloat = self.expr.nu.subs(self.symsub).evalf()
        self.nu = int(sp.floor(self.nufloat))
        if self.nu==0: self.nu=1
        self.n = self.nu+1
        self.u_st = stats.u_st(self.nu, self.sdm, alpha).round(self.prec) #Confidence Interval of (1-alpha)*100%

        self.display(calcU=calcU, vbs=vbs)
        return {self.sym.val: self.val, 'dsym': self.sym.d, 'd': self.d, self.sym.sdm: self.sdm, self.sym.u: self.u, self.sym.valr: self.valr, self.sym.nu: self.nu, self.sym.u_st: self.u_st}
    
    def set_cov(self, var, cov):
        self.cov[var]=cov
        self.sym.cov[var]=sp.Symbol(rf's_{{\overline{{{self.sym.flatname}{var.sym.flatname}}}}}')
    
    def plot(self, ran=(), pts=100, ref=0, zorder=0, color=cfg.plotcolor, linewidth=cfg.linewidth, textsize=cfg.textsize, label=' ', xlabel='', ylabel='', title=''):
        if ref==0: ref=self.id
        if label == ' ': label=rf'${sp.latex(self)}({sp.latex(self.x)})={sp.latex(self.f)}$'
        if not xlabel: xlabel=rf'${sp.latex(self.x)}\, [{sp.latex(self.x.unit)}]$'
        if not ylabel: ylabel=rf'${sp.latex(self)}\, [{sp.latex(self.unit)}]$'
        
        if ran==(): 
            ran=(self.x.val[0],self.x.val[-1])
        if ran[0]>=ran[1]: ran = ran[1],ran[0]
        step=(ran[1]-ran[0])/(pts+1)
        
        xVal=np.arange(ran[0], ran[1]+step,step)
        self({self.x:xVal}, calcU=False, alpha=0, vbs=0)
        yVal=self.vals
        self.fig = plots.plot(xVal, yVal, ref=ref, zorder=zorder, color=color, linewidth=linewidth, textsize=textsize, label=label, xlabel=xlabel, ylabel=ylabel, title=title)
        return self.fig
    
    def display(self, calcEv=True, calcU=True, vbs=cfg.vbs):
        if vbs>=2: display(Math(rf'{self} = {sp.latex(self.f)}'))
        if not calcEv: return
        
        symsubfsymbols={k: v for k, v in self.symsub.items() if k in self.fsymbols}
        if vbs>=2: display(Math(rf'{self}({symsubfsymbols}) = {self.val} \, {sp.latex(self.unit)}'))
        if not calcU: return
        
        if vbs>=2:
            for x in self.variables:
                derivU = self.sym.unit/x.sym.unit
                derivU= sp.latex(derivU if derivU != 1 else '')
                display(Math(rf'{self.sym.d[x]} = {sp.latex(self.expr.d[x])} = {self.d[x]} \, {derivU}'))
        
            display(Math(rf'{self.sym.sdm} = {sp.latex(self.expr.sdm)}'))
            display(Math(rf'{self.sym.sdm} = {self.sdm} \, {sp.latex(self.unit)}'))
            
        if vbs>=1: display(Math(rf'{self} = ({self.valr:.{self.dec}f} \pm {self.u:.{self.dec}f}) \, {sp.latex(self.unit)}'))
        if self.alpha==0: return
        
        if vbs>=2: display(Math(rf'{self.sym.nu} = {sp.latex(self.expr.nu)} = {self.nufloat} \approx {self.nu}'))
        if vbs>= 1: display(Math(rf'\text{{Intervalo de confianza de \({int((1-self.alpha)*100)}\%\):}}\quad {self.sym.argument}_{{{self.sym.subindex} \, {int((1-self.alpha)*100)}\%}}=({self.valr:.{self.dec}f} \pm {self.u_st:.{self.dec}f}) \, {sp.latex(self.unit)}'))
        return

class funcFit(func):
    def __new__(self, name, f, y, unit='', alpha=cfg.alpha, vbs=cfg.vbs):
        if unit=='':unit=y.sym.strUnit
        self = func.__new__(self, name, f, unit=unit, calcEv=False, calcU=False, vbs=0)
        
        return self.calc_fit(y, vbs=vbs)
    
    def calc_fit(self, y, alpha=cfg.alpha, vbs=cfg.vbs):
        for x in self.variables:
            if type(x) is varList:
                # if hasattr(self, 'x'): print(f'Many varList found or function has attribute x'); return
                self.x=x
        if not hasattr(self, 'x'): print(f'x not found in variables'); return
        
        x=self.x
        self.y=y
        if type(x) is not varList or type(y) is not varList: print(f'x, y must be of type varList'); return
        if x.n != y.n: print(rf'{x}, {y} must be of same length'); return
        
        self.n = x.n

        setattr(self, x.sym.name, x)
        setattr(self, y.sym.name, y)
        self.adjParams = self.variables.copy()
        self.adjParams.remove(x)
        self.nAdjParams = len(self.adjParams)
        self.nuParams=self.n-self.nAdjParams
        
        self.lamb=sp.lambdify([x]+self.adjParams, self.f)
        self.fitRes=curve_fit.func_fit(self)
        
        if vbs>=2: # For debugging
            for i in range(0,self.nAdjParams):
                display(Math(rf'{self.adjParams[i]} = {self.fitRes[0][i]} \quad {self.adjParams[i].sym.sd}={self.fitRes[1][i][i]}'))
        for i in range(0,self.nAdjParams):
            self.adjParams[i].calc({'val': self.fitRes[0][i], 'sdm': np.sqrt(self.fitRes[1][i][i]), 'nu':self.nuParams}, alpha=alpha, vbs=0)
            for j in range(0,self.nAdjParams):
                if i==j: continue
                self.adjParams[i].set_cov(self.adjParams[j], self.fitRes[1][i][j])
           
        self({x:x.val}, calcU=False, alpha=0, vbs=0)   
        self.fitResult=self.vals
        self.res = varList('r', {'val': y.val - self.fitResult}, unit=self.y.sym.strUnit, vbs=0)
    
        self.id=rnd.randint(10**5,10**6)
        self.resId=rnd.randint(10**5,10**6)
        self.display(vbs=vbs)
        return self
    
    def err_scatter(self, ref=0, zorder=0, dotsize=cfg.dotsize, color=cfg.scattercolor, ecolor=cfg.ecolor, elinewidth=cfg.elinewidth, capsize=cfg.capsize, textsize=cfg.textsize, label=' ', xlabel='', ylabel='', title=''):
        if ref==0: ref=self.id
        if label == ' ': label=rf'$({sp.latex(self.x)},{sp.latex(self.y)})$'
        if not xlabel: xlabel=rf'${sp.latex(self.x)}\, [{sp.latex(self.x.unit)}]$'
        if not ylabel: ylabel=rf'${sp.latex(self)}\, [{sp.latex(self.unit)}]$'
        
        self.fig = plots.err_scatter(self.x.val, self.y.val, self.x.sdm, self.y.sdm, ref=ref, zorder=zorder, dotsize=dotsize, color=color, ecolor=ecolor, elinewidth=elinewidth, capsize=capsize, textsize=textsize, label=label, xlabel=xlabel, ylabel=ylabel, title=title)
        return self.fig
    
    def res_plot(self, ref=0, dotsize=cfg.dotsize, color=cfg.scattercolor, textsize=cfg.textsize, label=' ', xlabel='', ylabel='', title=''):
        if ref==0: ref=self.resId
        if label == ' ': label=rf'$({sp.latex(self.x)},{sp.latex(self.res)})$'
        if not xlabel: xlabel=rf'${sp.latex(self.x)}\, [{sp.latex(self.x.unit)}]$'
        if not ylabel: ylabel=rf'${sp.latex(self.res)}\, [{sp.latex(self.res.unit)}]$'

        self.resFig = plots.scatter(self.x.val, self.res.val, ref=ref, dotsize=dotsize, color=color, textsize=textsize, label=label, xlabel=xlabel, ylabel=ylabel, title=title)
        return self.resFig
        
        
    def plots(self):
        self.plot(zorder=10)
        self.err_scatter(zorder=0, title=rf'${self}$(${self.x}$) ajustada y puntos (${self.x}$, ${self.y}$)')
        self.res_plot(title=rf'Residuos $r = {self.y}-{self}$')
    
    def display(self, vbs=cfg.vbs, **kwargs):
        if vbs>=1: 
            display(Math(rf'{self} = {sp.latex(self.f)}'))
            for param in self.adjParams:
                param.display(vbs=vbs)
            if vbs>=2: self.res()
            self.plots()
            
class pasco():
    def __init__(self, fname):
        df = pd.read_csv(fname, sep=';', decimal=',')
        self.cols=df.columns
        self.step = df.iloc[1,0]
        for i in range(1, len(self.cols)):
            if self.cols[i][0:5] == self.cols[0][0:5]:
                self.ncols=i
                break
        
        self.df = df.drop([self.cols[self.ncols*i] for i in range(0,int(len(self.cols)/self.ncols))], axis=1)
        self.cols=self.df.columns
        self.ncols=self.ncols-1
        
        self.colPsc={}
        for i in range(0, self.ncols):
            self.colPsc[i] = {int(self.cols[self.ncols*j+i].split(' ')[-1]): self.cols[self.ncols*j+i] for j in range(0,int(len(self.cols)/self.ncols))}
        self.display()
        
    def __call__(self, col=None, ran=(), ref=0, plot=False, color=cfg.plotcolor, label='', ylabel='', title=''): ###ADD to GITHUB
        if type(col) is int:
            col = self.cols[col]
        elif isinstance(col, (list, np.ndarray, tuple)):
            col = self.colPsc[col[0]][col[1]]
            
        colArr=utils.rm(self.df.loc[:,col])
        
        if ran==():
            tstep=np.vectorize(lambda x: x*self.step)
            ranArr=tstep(np.arange(0, len(colArr)))
        else:
            ranArr=np.arange(ran[0], ran[1], self.step)
            colArr=colArr[int(ran[0]/self.step):int(ran[-1]/self.step)]
        
        if title=='': title=col
        if plot:
            if ref==0: ref=rnd.randint(10**5,10**6)
            self.id=ref
            self.fig=plots.plot(ranArr, colArr, ref=ref, color=color, label=label, xlabel='Tiempo [s]', ylabel=ylabel, title=title)
        return colArr
    
    def __repr__(self):
        return str(display(self.df))
    
    def display(self):
        display(self.df)