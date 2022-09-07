#!/usr/bin/env python
import re
import os
import io
import subprocess
import utils

class ActionsCounter:
    #model_file:  the model of the planning task without grounding actions
    #theory_file: the theory of the plannign task INCLUDING actions
    def __init__(self, model_file, theory_file):
        self._model = model_file.readlines()
        self._theory = theory_file.readlines()
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
                        pred = "{}({})".format(body[1], ",".join(body[2:]))
                        cpred = "{}({}_c)".format(body[1], "_c,".join(body[2:]))
                        rule.write("p_{}{}".format(cnt, pred))
                        prog.write("p_{1}{0} :- not n_{1}{0}, {0}. n_{1}{0} :- not p_{1}{0}, {0}.\n".format(pred, cnt))
                        for par in body[2:]:
                            prog.write(":- p_{3}{0}, p_{3}{1}, {2} > {2}_c.\n".format(pred, cpred, par, cnt))
                    ln = ln + 1
                rule.write(".\n")
                prog.write(":- not {}.\n".format(head[1]))
                p, l = self.decomposeAction(rule.getvalue())
                prog.write(p)
                yield prog.getvalue(), l + 1 + ln * (len(body[2:]) + 2)
        #return prog.getvalue()


    def countActions(self, stream):
        cnt = 0
        lowerb = False
        for cnts, nbrules in stream:
            res = self.countAction(cnts, nbrules)
            if not res is None:
                cnt += res
            else:
                lowerb = True
            print("# of actions (intermediate result): {}{}".format(cnt, "+" if lowerb else ""))
        return "{}{}".format(cnt, "+" if lowerb else "")

    def countAction(self, prog, nbrules):
        #cnt = io.StringIO()
        lpcnt = os.environ.get('LPCNT_BIN_PATH')
        inpt = io.StringIO()
        inpt.writelines(self._model)
        inpt.write(prog)
        assert(lpcnt is not None)
        with (subprocess.Popen([lpcnt], stdin=subprocess.PIPE, stdout=subprocess.PIPE)) as proc:
            #print()
            print("counting on {} facts (model) and {} rules (theory + encoding for counting)".format(len(self._model), nbrules))
            #print(prog)
            out, err = proc.communicate(inpt.getvalue().encode())
            #cnt.writelines(proc.communicate((inpt.getvalue()).encode())[0].decode())
            #proc.stdin.write(rule)
            #proc.stdin.flush()
            #proc.stdin.close()
            #prog.writelines(proc.stdout.readlines())
        #return(cnt.getvalue())
        res = None
        for line in out.decode().split("\n"):
            if line.startswith("s "):
                res = int(line[2:])
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
if __name__ == "__main__":
    a = ActionsCounter(open("output.cnt"), open("output.theory-full"))
    #print("\n".join(a.parseActions()))
    print("# of actions: {}".format(a.countActions(a.parseActions())))

