#!/usr/bin/python
# Author: Damian Lasek (edamlas)
# Date: 19.10.2015

import subprocess
import argparse
import datetime
import shutil
import os

nflExecutorPath = '/vobs/ims_ttcn3/common/bin/nfl_executor'
commonBinPath = '/vobs/ims_ttcn3/common/bin/'

def parseArguments():
    parser = argparse.ArgumentParser(description='Script for automatic running NFL_UC module')
    
    parser.add_argument('-b', '--build', required=True, help='path to MTAS build')
    return parser.parse_args()

def generateMakefile():
    # python2.7 /vobs/ims_ttcn3/projects/TAS/tools/tiger/src/puma/puma.py -c -t -A NFL_UC
    p = subprocess.Popen('python2.7 /vobs/ims_ttcn3/projects/TAS/tools/tiger/src/puma/puma.py -c -t -A NFL_UC'.split(), cwd=commonBinPath)
    p.wait()
    
    os.symlink('/vobs/ims_ttcn3/common/bin/.build/mtas', '/vobs/ims_ttcn3/common/bin/mtas')

def compileModule():
    # time make compile
    p = subprocess.Popen('time make compile'.split(), cwd='/vobs/ims_ttcn3/common/bin/.build')
    p.wait()

    # time make -j 8
    p = subprocess.Popen('time make -j 8'.split(), cwd='/vobs/ims_ttcn3/common/bin/.build')
    p.wait()
    
def regenerateDbAddToExecutionList():
    # /vobs/ims_ttcn3/projects/TAS/ft_common/scripts/buildTcsList.pl --mod ALTCF_TRAF_TCs --output execution_list.lst --db mtas.db --regen_db
    p = subprocess.Popen('/vobs/ims_ttcn3/projects/TAS/ft_common/scripts/buildTcsList.pl --mod NFL_UC --output execution_list.lst --db mtas.db --regen_db'.split(),
        cwd=commonBinPath)
    p.wait()
    
def installBuild(buildPath):
    # /vobs/ims_ttcn3/projects/TAS/ft_common/scripts/installer_maia.py --verbose start --timeout 1800 --hardware-type 2 --mtas-build <build> --use-force --consolelogs-size 9000000000
    p = subprocess.Popen(['python2.7', '/vobs/ims_ttcn3/projects/TAS/ft_common/scripts/installer_maia.py', '--verbose', 'start', \
        '--timeout', '1800', '--hardware-type', '2', '--mtas-build', buildPath, '--use-force', '--consolelogs-size', '9000000000'], cwd=commonBinPath)
    p.wait()
    
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
    
    data[53] = 'ttcnfw_logDir := "%s"\n' % logsPath  #TODO https://docs.python.org/2/howto/regex.html#search-and-replace
    data[92] = 'ttcnfw_fullProcessing := "FALSE"\n'
    
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
#    generateMakefile()
#    compileModule()
    regenerateDbAddToExecutionList()
    generateConfigFiles(args.build)
    changeConfig()
    linkConfig()
    addTestcases()
    installBuild(args.build)
    runInitialConfiguration()

    for i in range(3):
        executeTests()
        selectFailedTcs()
        addTestcases()
    
    
    
if __name__ == '__main__':
    main()
    
