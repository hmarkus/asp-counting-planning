#!/usr/bin/env python

import re
import os
import io
import subprocess
import utils
import argparse

class ActionsCounter:
    #model_file:  the model of the planning task without grounding actions
    #theory_file: the theory of the plannign task INCLUDING actions
    def __init__(self, model_file, theory_file, gen_choices, output_actions):
        self._gen_choices = gen_choices
        self._model = model_file.readlines()
        self._theory = theory_file.readlines()
        self._output = output_actions
        #self._vars = {}
        #self._pos = {}
        #self._preds = {}
        #self.parseActions(theory_file.readlines())

    def generateRegEx(self, name):
        return re.compile("(?P<total>(?P<name>{}\w+)\s*\((?P<params>(\s*\w+\s*,?)+)\))".format(name))

    def getPred(self, match):
        if match is None:
            return None
        else:
            return [match.group("total"), match.group("name"),] + list(map(lambda x: x.strip(), match.group("params").split(",")))

    #def parseActionsStream(self):
    #    return self.parseActions(self._theory.readlines())

    def parseActions(self):
        lines = self._theory
        r = self.generateRegEx("^action_")
        rl = self.generateRegEx("")
        cnt = 0
        #prog = io.StringIO()
        #rule = io.StringIO()
        for l in lines:
            prog = io.StringIO()
            rule = io.StringIO()
            #print(l)
            head = self.getPred(r.match(l))
            if not head is None:
                #print(head)
                ip = 0
                self._preds = {}
                _vars = {}
                _pos = set()
                #done = set()
                for pb in head[2:]:
                    _vars[pb] = ip
                    ip = ip + 1
                rule.write(head[1] + " :- ")
                ln = 0
                for p in rl.finditer(l, len(head[0])):
                    if ln > 0:
                        rule.write(",")
                    body = self.getPred(p)
                    assert(not body is None)
                    if body[1].startswith("type"):
                        rule.write(body[0])
                    else: #get predicate and predicate with copy vars
                        cnt = cnt + 1
                        pnam = "p_{}{}".format(cnt,body[1])
                        pred = "{}({})".format(body[1], ",".join(body[2:]))
                        ip = 0
                        #print(body[2:])
                        #if body[1] not in done:
                        if True:
                            for pb in body[2:]:
                                if _vars[pb] not in _pos: #has_key(self._vars[p]):  
                                    _pos.add(_vars[pb]) # (pnam, ip)
                                    #ps = self._preds[pnam] if ip > 0 {} else
                                    #self._preds[pnam] = ps
                                    self._preds[pnam + "," + str(ip)] = _vars[pb]
                                ip = ip + 1
                        #    done.add(body[1])
                        #print(done)
                        cpred = "{}({}_c)".format(body[1], "_c,".join(body[2:]))
                        rule.write("p_{}{}".format(cnt, pred))
                        if self._output:
                            prog.write("#show p_{1}{0}/{2}.\n".format(body[1], cnt, len(body[2:])))
                        if self._gen_choices:
                            prog.write("1 {{ p_{1}{0} : {0} }} 1.\n".format(pred, cnt))
                        else:
                            prog.write("p_{1}{0} :- not n_{1}{0}, {0}. n_{1}{0} :- not p_{1}{0}, {0}.\n".format(pred, cnt))
                            for par in body[2:]:
                                prog.write(":- p_{3}{0}, p_{3}{1}, {2} > {2}_c.\n".format(pred, cpred, par, cnt))
                    ln = ln + 1
                rule.write(".\n")
                prog.write(":- not {}.\n".format(head[1]))
                if not self._output:
                    prog.write("#show {}/0.\n".format(head[1]))
                #else:
                #    prog.write("#show {}/{}.\n".format(head[1], len(head[2:])))
                #    prog.write("{}({}) :- \n".format(head[1], ",".join(head[2:])))
                #    for p in rl.finditer(l, len(head[0])):
                p, l = self.decomposeAction(rule.getvalue())
                prog.write(p)
                #print(_vars, self._preds, _pos)
                yield prog.getvalue(), l + 1 + ln * (len(body[2:]) + 2), head[1]
        #return prog.getvalue()


    def countActions(self, stream):
        cnt = 0
        lowerb = False
        for cnts, nbrules, predicate in stream:
            res = self.countAction(cnts, nbrules, predicate)
            if not res is None:
                cnt += res
            else:
                lowerb = True
            print("# of actions (intermediate result): {}{}".format(cnt, "+" if lowerb else ""))
        return "{}{}".format(cnt, "+" if lowerb else "")

    def countAction(self, prog, nbrules, pred):
        #cnt = io.StringIO()
        #assert(os.environ.get('GRINGO_BIN_PATH') is not None) # gringo is used by lpcnt
        lpcnt = os.environ.get('LPCNT_BIN_PATH')
        assert(lpcnt is not None)
        inpt = io.StringIO()
        inpt.writelines(self._model)
        inpt.write(prog)
        #debug output
        #f=open(pred, "w")
        #f.write(inpt.getvalue())
        #f.close()
        with (subprocess.Popen([lpcnt], stdin=subprocess.PIPE, stdout=subprocess.PIPE)) as proc:
            #print()
            print("counting {} on {} facts (model) and {} rules (theory + encoding for counting)".format(pred, len(self._model), nbrules))
            #print(prog)
            #out, err = proc.communicate(inpt.getvalue().encode())
            #cnt.writelines(proc.communicate((inpt.getvalue()).encode())[0].decode())
            proc.stdin.write(inpt.getvalue().encode()) #rule)
            #print(inpt.getvalue().encode())
            proc.stdin.flush()
            proc.stdin.close()
            #print(proc.stdout.readlines())
            #prog.writelines(proc.stdout.readlines())
            #return(cnt.getvalue())
            res = None
            #print(proc.stdout.read())
            r = self.generateRegEx("^p_")
            for line in proc.stdout:
                #print(line)
                line = line.decode()
                #if not line:
                #    break
                #line = lne.decode().split("\n") #any whitespace
                if line.startswith("s "):
                    res = int(line[2:])
                elif line.startswith("Models       : "):
                    pos = -1 if line.find("+") > -1 else len(line)
                    res = int(line[15:pos])
                elif self._output and line.startswith("p_"):
                    ps = [None] * len(self._preds)
                    #print(line,self._preds)
                    for l in line.split(" "):
                        atom = self.getPred(r.match(l))
                        if not atom is None:
                            ip = 0 
                            for px in atom[2:]:
                                k = atom[1] + "," + str(ip)
                                #print(self._preds,k,px)
                                if k in self._preds.keys():
                                    ps[self._preds[k]] = px
                                ip = ip + 1
                    #print(ps)
                    #print("{}({})".format(pred, ",".join(ps)))
            proc.stdout.close()
        return res


    def decomposeAction(self, rules):
        prog = io.StringIO()
        lpopt = os.environ.get('LPOPT_BIN_PATH')
        assert(lpopt is not None)
        with (subprocess.Popen([lpopt], stdin=subprocess.PIPE, stdout=subprocess.PIPE)) as proc:
            prog.writelines(proc.communicate(rules.encode())[0].decode())
            #proc.stdin.write(rule)
            #proc.stdin.flush()
            #proc.stdin.close()
            #prog.writelines(proc.stdout.readlines())
        return prog.getvalue(), len(prog.getvalue().split("\n"))


# for quick testing (use case: direct translator)
# todo exception handling for io, signal handling, ...
if __name__ == "__main__":
    assert(os.environ.get('LPCNT_AUX_PATH') is not None)
    assert(os.environ.get('LPCNT_BIN_PATH') is not None)
    assert(os.environ.get('LPOPT_BIN_PATH') is not None)
    #with (subprocess.Popen([os.environ.get('LPCNT_AUX_PATH') + "/set_env_vars.sh"])) as proc:
    #    pass
    parser = argparse.ArgumentParser(description='Count the # of actions that would be contained in a full grounding. Requires to set env variable LPCNT_AUX_PATH containing auxiliary binaries used in lpcnt AND executing source $LPCNT_AUX_PATH/set_env_vars.sh first (or setting those environment variables right)')
    parser.add_argument('-m', '--model', required=True, help="The (compact) model of the theory without grounding actions.")
    parser.add_argument('-t', '--theory', required=True, help="The (full) theory containing actions.")
    parser.add_argument('-c', '--choices', required=False, action="store_const", const=True, default=False, help="Enables the generation of choice rules.")
    parser.add_argument('-o', '--output', required=False, action="store_const", const=True, default=False, help="Enables the output of actions.")
    args = parser.parse_args()

    #a = ActionsCounter(open("output.cnt"), open("output.theory-full"))
    #print("\n".join(a.parseActions()))

    a = ActionsCounter(open(args.model), open(args.theory), args.choices, args.output)
    print("# of actions: {}".format(a.countActions(a.parseActions())))
