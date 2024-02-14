import sys
sys.path.append("../..")
import c, peggen

#c.from_file("cdecl.hx", file_out = "cdecl.hx.ast")
#c.from_file("cdecl-init.hx", file_out = "cdecl-init.hx.ast")
#c.from_file("func.hx", file_out = "func.hx.ast", logfile = "func.hx.log")
#c.from_file("funcdecltr.hx", file_out = "funcdecltr.hx.ast")#, logfile = "funcdecltr.hx.log")
#c.from_file("main.hx", file_out = "main.hx.ast", logfile = "main.hx.log")
#c.from_file("stdio.hpp", file_out = "stdio.hpp.ast", logfile = "stdio.hpp.log")
c.from_file("stdio.hpp_test.h", file_out = "stdio.hpp_test.ast", logfile = "stdio.hpp_test.log")
#for t in peggen.TIMES:
#    print("time: ", t/1e9, "seconds")
#print("Rule Checks:", peggen.RULE_CHECKS[peggen.RULE_CHECK_NUM])
#print("Cache hits:", peggen.RULE_CHECKS[peggen.CACHE_HITS])