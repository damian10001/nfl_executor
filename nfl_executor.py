#!/usr/bin/python
# Author: Damian Lasek (edamlas)
# Date: 19.10.2015

#History info:
#2015-10-23 initial working version
#2015-11-03 - added re-install build in case of fail; 
#           - possibility of running other ttcn modules and more than one
#2015-11-04 - version 1.1 - should work :)

import subprocess
import argparse
import datetime
import shutil
import os
import re

nflExecutorPath = '/vobs/ims_ttcn3/common/bin/nfl_executor'
commonBinPath = '/vobs/ims_ttcn3/common/bin/'

def parseArguments():
    parser = argparse.ArgumentParser(description='Script for automatic running TC modules. It is intended for running NFL_UC, but works also with other modules.')
    
    parser.add_argument('-b', '--build', required=True, help='path to MTAS build')
    parser.add_argument('modules', help='List of modules to compile and execute. Default value is NFL_UC', metavar='module', type=str, nargs='*')
    return parser.parse_args()

def generateMakefile(ttcn_modules):
    print "List of modules to generate Makefile: ", ttcn_modules
            
    # python2.7 /vobs/ims_ttcn3/projects/TAS/tools/tiger/src/puma/puma.py -c -t -A NFL_UC
    p = subprocess.Popen(('python2.7 /vobs/ims_ttcn3/projects/TAS/tools/tiger/src/puma/puma.py -c -t -A ' + ' '.join(ttcn_modules)).split(), cwd=commonBinPath)
    p.wait()
    
    os.symlink('/vobs/ims_ttcn3/common/bin/.build/mtas', '/vobs/ims_ttcn3/common/bin/mtas')

def compileModule():
    # time make compile
    p = subprocess.Popen('time make compile'.split(), cwd='/vobs/ims_ttcn3/common/bin/.build')
    p.wait()

    # time make -j 8
    p = subprocess.Popen('time make -j 8'.split(), cwd='/vobs/ims_ttcn3/common/bin/.build')
    p.wait()
    
def regenerateDbAddToExecutionList(ttcn_modules):
    print "List of modules to add to execution_list.lst: ", ttcn_modules

    # /vobs/ims_ttcn3/projects/TAS/ft_common/scripts/buildTcsList.pl --mod NFL_UC --output execution_list.lst --db mtas.db --regen_db
    p = subprocess.Popen(['/vobs/ims_ttcn3/projects/TAS/ft_common/scripts/buildTcsList.pl', '--mod', ttcn_modules[0], '--output', 'execution_list.lst', '--db', 'mtas.db', '--regen_db'],
        cwd=commonBinPath)
    p.wait()
    
    if len(ttcn_modules) > 1:
        with open('/vobs/ims_ttcn3/common/bin/execution_list.lst', 'a') as file_:
            for i in range(1, len(ttcn_modules)):
                p = subprocess.Popen(['/vobs/ims_ttcn3/projects/TAS/ft_common/scripts/buildTcsList.pl', '--mod', ttcn_modules[i], '--output', 'execution_list_tmp.lst'],     
                    cwd=commonBinPath)
                p.wait()
                
                with open('/vobs/ims_ttcn3/common/bin/execution_list_tmp.lst', 'r') as file_tmp:
                    exec_list_tmp = file_tmp.readlines()
                
                file_.writelines(exec_list_tmp)
                
            if os.path.exists('/vobs/ims_ttcn3/common/bin/execution_list_tmp.lst'):
                os.remove('/vobs/ims_ttcn3/common/bin/execution_list_tmp.lst')
        
def installBuild(buildPath):
    # /vobs/ims_ttcn3/projects/TAS/ft_common/scripts/installer_maia.py --verbose start --timeout 1800 --hardware-type 2 --mtas-build <build> --use-force --consolelogs-size 9000000000
    p = subprocess.Popen(['python2.7', '/vobs/ims_ttcn3/projects/TAS/ft_common/scripts/installer_maia.py', '--verbose', 'start', \
        '--timeout', '1800', '--hardware-type', '2', '--mtas-build', buildPath, '--use-force', '--consolelogs-size', '9000000000'], cwd=commonBinPath)
    exitcode = p.wait()
    
    return exitcode
    
def generateConfigFiles(buildPath):
    # /vobs/ims_ttcn3/projects/TAS/tools/tiger/src/autoGenerateConfigFiles.pl -build <build> -maia -cfgdir /vobs/ims_ttcn3/common/bin/nfl_executor
    shutil.rmtree(nflExecutorPath, ignore_errors=True)
       
    os.makedirs(nflExecutorPath)
        
    os.environ['FT_WORK_DIR'] = nflExecutorPath
    
    p = subprocess.Popen(['/vobs/ims_ttcn3/projects/TAS/tools/tiger/src/autoGenerateConfigFiles.pl', '-build', buildPath, '-maia', '-cfgdir', nflExecutorPath])
    p.wait()
    
    shutil.copyfile('/vobs/ims_ttcn3/common/bin/nfl_executor/titan.cfg', '/vobs/ims_ttcn3/common/bin/nfl_executor/titan_template.cfg')

def changeConfig():
    with open('/vobs/ims_ttcn3/common/bin/nfl_executor/base.cfg', 'r') as file_:
        data = file_.readlines()
        
    username = os.getlogin()
    t = datetime.datetime.now()
    
    logsPath = '/home/%s/logs/NFL/%s' % (username, t.strftime("%Y%m%d_%H%M%S"))
    
    if not os.path.exists(logsPath):
        os.makedirs(logsPath)
    
    pattern = "ttcnfw_logDir"
    config = 'ttcnfw_logDir := "%s"\n' % logsPath
        
    for i in range (0, len(data)):
        if re.search(pattern, data[i]): 
            data[i] = config
            
    pattern = "ttcnfw_fullProcessing"
    config = 'ttcnfw_fullProcessing := "FALSE"\n'

    for i in range (0, len(data)):
        if re.search(pattern, data[i]):
            data[i] = config
    
    with open('/vobs/ims_ttcn3/common/bin/nfl_executor/base.cfg', 'w') as file_:
        file_.writelines(data)
    
    return logsPath
        
def linkConfig():
    basePath = '/vobs/ims_ttcn3/common/bin/base.cfg'
    titanPath = '/vobs/ims_ttcn3/common/bin/titan.cfg'

    if os.path.exists(basePath):
        os.remove(basePath)
    if os.path.exists(titanPath):
        os.remove(titanPath)
    
    os.symlink('/vobs/ims_ttcn3/common/bin/nfl_executor/base.cfg', '/vobs/ims_ttcn3/common/bin/base.cfg')
    os.symlink('/vobs/ims_ttcn3/common/bin/nfl_executor/titan.cfg', '/vobs/ims_ttcn3/common/bin/titan.cfg')
        
def addTestcases():
    # first, clear titan.cfg by copying template file
    shutil.copyfile('/vobs/ims_ttcn3/common/bin/nfl_executor/titan_template.cfg', '/vobs/ims_ttcn3/common/bin/nfl_executor/titan.cfg')

    # add testcases from execution_list
    with open('/vobs/ims_ttcn3/common/bin/nfl_executor/titan.cfg', 'a') as titan:
        with open('/vobs/ims_ttcn3/common/bin/execution_list.lst', 'r') as exec_list:
            execution_list = exec_list.readlines()
        titan.writelines(execution_list)
    
def runInitialConfiguration():
    # /app/TITAN/5_R3A/LMWP3.3/bin/ttcn3_start mtas /home/edamlas/config/titan.cfg testAutomation.initialConfiguration
    p = subprocess.Popen('/app/TITAN/5_R3A/LMWP3.3/bin/ttcn3_start mtas titan.cfg testAutomation.initialConfiguration'.split(), cwd=commonBinPath)
    p.wait()
    
def executeTests():
    # /app/TITAN/5_R3A/LMWP3.3/bin/ttcn3_start mtas titan.cfg
    p = subprocess.Popen(['/app/TITAN/5_R3A/LMWP3.3/bin/ttcn3_start', 'mtas', 'titan.cfg'], cwd=commonBinPath)
    p.wait()
    
def selectFailedTcs():
    with open('/vobs/ims_ttcn3/common/bin/execution_list.lst', 'r') as exec_list:
        execution_list = exec_list.readlines()

    failed_tcs = []
    
    # select not passed TCs
    for line in execution_list:
        testcase_verdict = line.split()
        if len(testcase_verdict) > 1 and testcase_verdict[1] != "pass":
            failed_tcs.append(testcase_verdict[0])

    # write them back to file
    with open('/vobs/ims_ttcn3/common/bin/execution_list.lst', 'w+') as exec_list:
        for line in failed_tcs:
            exec_list.write(line + "\n")
    

def main():
    args = parseArguments()
    if len(args.modules) == 0:
        args.modules.append('NFL_UC')
    generateMakefile(args.modules)
    compileModule()
    regenerateDbAddToExecutionList(args.modules)
    generateConfigFiles(args.build)
    changeConfig()
    linkConfig()
    addTestcases()

    # install build, repeat if something went wrong
    for i in range(3):
        install_code = installBuild(args.build)
        if install_code == 0:
            # installation went OK, run initial configuration
            runInitialConfiguration()
            break
    
    # run testcases, repeat with failed
    for i in range(3):
        executeTests()
        selectFailedTcs()
        addTestcases()
        
    
    
if __name__ == '__main__':
    main()
    