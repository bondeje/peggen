import sys
sys.path.append("../..")
import c, peggen, time, os

t = time.time()
#c.from_file("cdecl.hx", file_out = "cdecl.hx.ast")
#c.from_file("cdecl-init.hx", file_out = "cdecl-init.hx.ast")
#c.from_file("func.hx", file_out = "func.hx.ast", logfile = "func.hx.log")
#c.from_file("funcdecltr.hx", file_out = "funcdecltr.hx.ast")#, logfile = "funcdecltr.hx.log")
f = "main.hx"
print("processing file: ", f, end='...')
c.from_file(f, file_out = f + ".ast", logfile = f + ".log")
#c.from_file("stdio.hpp", file_out = "stdio.hpp.ast", logfile = "stdio.hpp.log")
#c.from_file(".\clib\stdio.hx", file_out = ".\clib\stdio.hx.ast", logfile = ".\clib\stdio.hx.log")
#c.from_file(".\\clib\\assert.hx", file_out = ".\\clib\\assert.hx.ast", logfile = ".\\clib\\assert.hx.log")
t = time.time() - t
print(t, "seconds")

#f = "string.hx"
#fi = '.\\clib\\' + f
#fo = fi + '.ast'
#fl = fi + '.log'
#print("processing file: ", f, end='...')
#t = time.time()
#c.from_file(fi, file_out = fo, logfile = fl)
#t = time.time() - t
#print(t, "seconds")

#"""
for f in os.listdir('.\\clib'):
    if f.endswith('.hx'):
        fi = '.\\clib\\' + f
        fo = fi + '.ast'
        fl = fi + '.log'
        print("processing file: ", f, end='...')
        t = time.time()
        c.from_file(fi, file_out = fo, logfile = fl)
        t = time.time() - t
        print(t, "seconds")
#"""
        
#for t in peggen.TIMES:
#    print("time: ", t/1e9, "seconds")
#print("Rule Checks:", peggen.RULE_CHECKS[peggen.RULE_CHECK_NUM])
#print("Cache hits:", peggen.RULE_CHECKS[peggen.CACHE_HITS])